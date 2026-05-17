use serde::{Deserialize, Serialize};
use tauri::{AppHandle, State};

use crate::providers::{Provider, UiPrefs, PRESETS};
use crate::setup::{check_environment, check_missing_packages, setup_venv, EnvStatus};
use crate::store::Store;

#[derive(Debug, Serialize)]
pub struct ProviderSafe {
    pub id: String,
    pub name: String,
    pub preset: String,
    pub base_url: String,
    pub api_key_masked: String,
    pub text_model: String,
    pub vision_model: String,
    pub use_vision: bool,
    pub created_at: String,
    pub updated_at: String,
}

impl From<&Provider> for ProviderSafe {
    fn from(p: &Provider) -> Self {
        let masked = if p.api_key.len() > 8 {
            format!("{}...{}", &p.api_key[..3], &p.api_key[p.api_key.len()-4..])
        } else if !p.api_key.is_empty() {
            "***".to_string()
        } else {
            String::new()
        };
        Self {
            id: p.id.clone(),
            name: p.name.clone(),
            preset: p.preset.clone(),
            base_url: p.base_url.clone(),
            api_key_masked: masked,
            text_model: p.text_model.clone(),
            vision_model: p.vision_model.clone(),
            use_vision: p.use_vision,
            created_at: p.created_at.to_rfc3339(),
            updated_at: p.updated_at.to_rfc3339(),
        }
    }
}

#[derive(Debug, Serialize)]
pub struct ConfigResponse {
    pub active_id: String,
    pub providers: Vec<ProviderSafe>,
    pub ui: UiPrefs,
}

#[tauri::command]
pub fn get_config(store: State<'_, Store>) -> ConfigResponse {
    let cfg = store.get_config();
    ConfigResponse {
        active_id: cfg.active_id,
        providers: cfg.providers.iter().map(ProviderSafe::from).collect(),
        ui: cfg.ui,
    }
}

#[derive(Debug, Deserialize)]
pub struct AddProviderInput {
    pub name: String,
    pub preset: String,
    pub base_url: String,
    pub api_key: String,
    pub text_model: String,
    pub vision_model: String,
    pub use_vision: bool,
}

#[tauri::command]
pub fn add_provider(store: State<'_, Store>, input: AddProviderInput) -> Result<ProviderSafe, String> {
    let now = chrono::Utc::now();
    let provider = Provider {
        id: String::new(),
        name: input.name,
        preset: input.preset,
        base_url: input.base_url,
        api_key: input.api_key,
        text_model: input.text_model,
        vision_model: input.vision_model,
        use_vision: input.use_vision,
        created_at: now,
        updated_at: now,
    };
    store.add_provider(provider)
        .map(|p| ProviderSafe::from(&p))
        .map_err(|e| e.to_string())
}

#[derive(Debug, Deserialize)]
pub struct UpdateProviderInput {
    pub id: String,
    pub name: String,
    pub preset: String,
    pub base_url: String,
    pub api_key: Option<String>,
    pub text_model: String,
    pub vision_model: String,
    pub use_vision: bool,
}

#[tauri::command]
pub fn update_provider(store: State<'_, Store>, input: UpdateProviderInput) -> Result<(), String> {
    let cfg = store.get_config();
    let existing = cfg.providers.iter().find(|p| p.id == input.id)
        .ok_or("provider not found")?;

    let provider = Provider {
        id: input.id,
        name: input.name,
        preset: input.preset,
        base_url: input.base_url,
        api_key: input.api_key.unwrap_or_else(|| existing.api_key.clone()),
        text_model: input.text_model,
        vision_model: input.vision_model,
        use_vision: input.use_vision,
        created_at: existing.created_at,
        updated_at: chrono::Utc::now(),
    };
    store.update_provider(provider).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn delete_provider(store: State<'_, Store>, id: String) -> Result<(), String> {
    store.delete_provider(&id).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn activate_provider(store: State<'_, Store>, id: String) -> Result<(), String> {
    store.activate_provider(&id).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn update_ui_prefs(store: State<'_, Store>, prefs: UiPrefs) -> Result<(), String> {
    store.update_ui_prefs(prefs).map_err(|e| e.to_string())
}

#[derive(Debug, Serialize)]
pub struct PresetInfo {
    pub id: &'static str,
    pub name: &'static str,
    pub base_url: &'static str,
    pub text_model: &'static str,
    pub vision_model: &'static str,
    pub use_vision: bool,
}

#[tauri::command]
pub fn get_presets() -> Vec<PresetInfo> {
    PRESETS.iter().map(|p| PresetInfo {
        id: p.id,
        name: p.name,
        base_url: p.base_url,
        text_model: p.text_model,
        vision_model: p.vision_model,
        use_vision: p.use_vision,
    }).collect()
}

#[tauri::command]
pub fn list_backups(store: State<'_, Store>) -> Result<Vec<String>, String> {
    store.list_backups().map_err(|e| e.to_string())
}

#[tauri::command]
pub fn restore_backup(store: State<'_, Store>, filename: String) -> Result<(), String> {
    store.restore_backup(&filename).map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn test_provider(store: State<'_, Store>, id: String) -> Result<String, String> {
    let cfg = store.get_config();
    let provider = cfg.providers.iter().find(|p| p.id == id)
        .ok_or("provider not found")?;

    let client = reqwest::Client::new();
    let url = format!("{}/v1/models", provider.base_url.trim_end_matches('/'));
    let resp = client.get(&url)
        .header("Authorization", format!("Bearer {}", provider.api_key))
        .timeout(std::time::Duration::from_secs(10))
        .send()
        .await
        .map_err(|e| format!("连接失败: {}", e))?;

    if resp.status().is_success() {
        Ok("连接成功".to_string())
    } else {
        Err(format!("HTTP {}: {}", resp.status(), resp.status().canonical_reason().unwrap_or("")))
    }
}

#[tauri::command]
pub fn check_python_env(app_handle: AppHandle, store: State<'_, Store>) -> Result<EnvStatus, String> {
    // If already configured and ready, return stored path
    if store.is_env_ready() {
        let path = store.get_python_path();
        if !path.is_empty() {
            let missing = check_missing_packages(&path, &["flask", "paddle", "openpyxl"])
                .map_err(|e| e.to_string())?;
            return Ok(EnvStatus {
                python_found: true,
                python_path: path.clone(),
                packages_ready: missing.is_empty(),
                missing_packages: missing,
            });
        }
    }

    check_environment(&app_handle).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn install_python_deps(app_handle: AppHandle, store: State<'_, Store>) -> Result<String, String> {
    let venv_python = setup_venv(&app_handle).map_err(|e| e.to_string())?;
    store.set_python_path(venv_python.clone()).map_err(|e| e.to_string())?;
    store.set_env_ready(true).map_err(|e| e.to_string())?;
    Ok(venv_python)
}

#[tauri::command]
pub fn use_system_python(store: State<'_, Store>, path: String) -> Result<(), String> {
    store.set_python_path(path).map_err(|e| e.to_string())?;
    store.set_env_ready(true).map_err(|e| e.to_string())?;
    Ok(())
}
