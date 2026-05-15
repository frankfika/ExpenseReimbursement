use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};

use anyhow::{Context, Result};
use chrono::Utc;
use parking_lot::Mutex;
use uuid::Uuid;

use crate::providers::{Provider, ProvidersConfig, UiPrefs};

const MAX_BACKUPS: usize = 10;

pub struct Store {
    config_dir: PathBuf,
    config_path: PathBuf,
    backups_dir: PathBuf,
    state: Mutex<ProvidersConfig>,
}

impl Store {
    pub fn new() -> Result<Self> {
        let config_dir = dirs::home_dir()
            .context("cannot determine home directory")?
            .join(".expense-helper");
        fs::create_dir_all(&config_dir)?;

        let config_path = config_dir.join("providers.json");
        let backups_dir = config_dir.join("backups");
        fs::create_dir_all(&backups_dir)?;

        let already_exists = config_path.exists();
        let config = if already_exists {
            let data = fs::read_to_string(&config_path)?;
            serde_json::from_str(&data).unwrap_or_default()
        } else {
            ProvidersConfig::default()
        };

        let store = Self {
            config_dir,
            config_path,
            backups_dir,
            state: Mutex::new(config),
        };

        // First-run setup: try migrating from .env, then ensure providers.json exists
        if !already_exists {
            if store.state.lock().providers.is_empty() {
                store.try_migrate_from_env();
            }
            // Ensure file exists even if no migration happened
            if !store.config_path.exists() {
                let _ = store.persist();
            }
        }
        Ok(store)
    }

    pub fn get_config(&self) -> ProvidersConfig {
        self.state.lock().clone()
    }

    #[allow(dead_code)]
    pub fn get_active_provider(&self) -> Option<Provider> {
        let cfg = self.state.lock();
        cfg.active_provider().cloned()
    }

    #[allow(dead_code)]
    pub fn list_providers(&self) -> Vec<Provider> {
        self.state.lock().providers.clone()
    }

    pub fn add_provider(&self, mut provider: Provider) -> Result<Provider> {
        if provider.id.is_empty() {
            provider.id = Uuid::new_v4().to_string();
        }
        let now = Utc::now();
        provider.created_at = now;
        provider.updated_at = now;

        let mut cfg = self.state.lock();
        cfg.providers.push(provider.clone());
        if cfg.active_id.is_empty() {
            cfg.active_id = provider.id.clone();
        }
        drop(cfg);
        self.persist()?;
        Ok(provider)
    }

    pub fn update_provider(&self, updated: Provider) -> Result<()> {
        let mut cfg = self.state.lock();
        if let Some(p) = cfg.providers.iter_mut().find(|p| p.id == updated.id) {
            *p = Provider {
                updated_at: Utc::now(),
                ..updated
            };
        }
        drop(cfg);
        self.persist()
    }

    pub fn delete_provider(&self, id: &str) -> Result<()> {
        let mut cfg = self.state.lock();
        cfg.providers.retain(|p| p.id != id);
        if cfg.active_id == id {
            cfg.active_id = cfg.providers.first().map(|p| p.id.clone()).unwrap_or_default();
        }
        drop(cfg);
        self.persist()
    }

    pub fn activate_provider(&self, id: &str) -> Result<()> {
        let mut cfg = self.state.lock();
        if cfg.providers.iter().any(|p| p.id == id) {
            cfg.active_id = id.to_string();
        }
        drop(cfg);
        self.persist()
    }

    pub fn update_ui_prefs(&self, prefs: UiPrefs) -> Result<()> {
        let mut cfg = self.state.lock();
        cfg.ui = prefs;
        drop(cfg);
        self.persist()
    }

    pub fn list_backups(&self) -> Result<Vec<String>> {
        let mut entries: Vec<String> = fs::read_dir(&self.backups_dir)?
            .filter_map(|e| e.ok())
            .filter(|e| e.path().extension().is_some_and(|ext| ext == "json"))
            .filter_map(|e| e.file_name().into_string().ok())
            .collect();
        entries.sort();
        entries.reverse();
        Ok(entries)
    }

    pub fn restore_backup(&self, filename: &str) -> Result<()> {
        let backup_path = self.backups_dir.join(filename);
        let data = fs::read_to_string(&backup_path)?;
        let config: ProvidersConfig = serde_json::from_str(&data)?;
        *self.state.lock() = config;
        self.persist()
    }

    pub fn try_migrate_from_env(&self) {
        let mut env_paths: Vec<PathBuf> = vec![
            std::env::current_dir().unwrap_or_default().join(".env"),
            self.config_dir.join(".env"),
        ];

        // Also try the project's source dir relative to the executable.
        // Useful when launched from the .app bundle where cwd is "/".
        if let Ok(exe) = std::env::current_exe() {
            // ../../../.env relative to executable (tauri-app/src-tauri/target/.../bin)
            for ancestor in exe.ancestors().take(8) {
                let candidate = ancestor.join(".env");
                if candidate.exists() {
                    env_paths.push(candidate);
                }
            }
        }

        for env_path in &env_paths {
            if let Ok(content) = fs::read_to_string(env_path) {
                let mut api_key = String::new();
                let mut base_url = "https://api.siliconflow.cn".to_string();
                let mut model = "deepseek-ai/DeepSeek-V3".to_string();

                for line in content.lines() {
                    let line = line.trim();
                    if line.starts_with('#') || line.is_empty() {
                        continue;
                    }
                    if let Some((key, val)) = line.split_once('=') {
                        let val = val.trim().trim_matches('"');
                        match key.trim() {
                            "DEEPSEEK_API_KEY" => api_key = val.to_string(),
                            "DEEPSEEK_BASE_URL" => base_url = val.to_string(),
                            "DEEPSEEK_MODEL" => model = val.to_string(),
                            _ => {}
                        }
                    }
                }

                if !api_key.is_empty() && api_key != "your_api_key_here" {
                    let now = Utc::now();
                    let provider = Provider {
                        id: "legacy-env".to_string(),
                        name: "从 .env 迁移".to_string(),
                        preset: "siliconflow".to_string(),
                        base_url,
                        api_key,
                        text_model: model,
                        vision_model: "Qwen/Qwen2.5-VL-7B-Instruct".to_string(),
                        use_vision: true,
                        created_at: now,
                        updated_at: now,
                    };
                    let mut cfg = self.state.lock();
                    cfg.providers.push(provider);
                    cfg.active_id = "legacy-env".to_string();
                    drop(cfg);
                    let _ = self.persist();
                    log::info!("migrated provider from {:?}", env_path);
                    return;
                }
            }
        }
    }

    fn persist(&self) -> Result<()> {
        self.backup_current();
        let cfg = self.state.lock();
        let json = serde_json::to_string_pretty(&*cfg)?;
        drop(cfg);
        atomic_write(&self.config_path, json.as_bytes())?;
        set_permissions_600(&self.config_path);
        Ok(())
    }

    fn backup_current(&self) {
        if !self.config_path.exists() {
            return;
        }
        let ts = Utc::now().format("%Y%m%d-%H%M%S");
        let backup_name = format!("providers-{}.json", ts);
        let dest = self.backups_dir.join(&backup_name);
        let _ = fs::copy(&self.config_path, &dest);
        self.prune_backups();
    }

    fn prune_backups(&self) {
        if let Ok(mut entries) = self.list_backups() {
            while entries.len() > MAX_BACKUPS {
                if let Some(oldest) = entries.pop() {
                    let _ = fs::remove_file(self.backups_dir.join(&oldest));
                }
            }
        }
    }
}

fn atomic_write(path: &Path, data: &[u8]) -> Result<()> {
    let tmp_path = path.with_extension("json.tmp");
    let mut file = fs::File::create(&tmp_path)?;
    file.write_all(data)?;
    file.sync_all()?;
    fs::rename(&tmp_path, path)?;
    Ok(())
}

#[cfg(unix)]
fn set_permissions_600(path: &Path) {
    use std::os::unix::fs::PermissionsExt;
    let _ = fs::set_permissions(path, fs::Permissions::from_mode(0o600));
}

#[cfg(not(unix))]
fn set_permissions_600(_path: &Path) {
    // Windows: rely on user-profile ACLs
}
