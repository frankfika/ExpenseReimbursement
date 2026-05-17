use std::path::PathBuf;
use std::process::Command;

use anyhow::{Context, Result};
use serde::Serialize;
use tauri::{AppHandle, Manager};

#[derive(Debug, Clone, Serialize)]
pub struct EnvStatus {
    pub python_found: bool,
    pub python_path: String,
    pub packages_ready: bool,
    pub missing_packages: Vec<String>,
}

/// Detect available python command and check required packages.
pub fn check_environment(_app_handle: &AppHandle) -> Result<EnvStatus> {
    let python_cmd = find_python_cmd();
    let mut status = EnvStatus {
        python_found: false,
        python_path: String::new(),
        packages_ready: false,
        missing_packages: Vec::new(),
    };

    let Some(python) = python_cmd else {
        return Ok(status);
    };

    status.python_found = true;
    status.python_path = python.clone();

    // Check required packages
    let required = vec!["flask", "paddle", "openpyxl"];
    let missing = check_missing_packages(&python, &required)?;
    status.packages_ready = missing.is_empty();
    status.missing_packages = missing;

    // If system python has all packages, great. Otherwise we'll create a venv later.
    Ok(status)
}

/// Create a venv in the app config dir and install requirements.txt into it.
pub fn setup_venv(app_handle: &AppHandle) -> Result<String> {
    let config_dir = app_handle
        .path()
        .app_config_dir()
        .context("cannot get app config dir")?;
    let venv_dir = config_dir.join("venv");
    let python_cmd = find_python_cmd().context("Python not found")?;

    // 1. Create venv if not exists
    if !venv_dir.join("bin").exists() && !venv_dir.join("Scripts").exists() {
        let output = Command::new(&python_cmd)
            .args(["-m", "venv", venv_dir.to_str().unwrap()])
            .output()
            .context("failed to create venv")?;
        if !output.status.success() {
            anyhow::bail!(
                "创建虚拟环境失败: {}",
                String::from_utf8_lossy(&output.stderr)
            );
        }
    }

    // 2. Determine venv python/pip path
    let venv_python = if cfg!(windows) {
        venv_dir.join("Scripts").join("python.exe")
    } else {
        venv_dir.join("bin").join("python3")
    };

    // 3. Find requirements.txt in bundled resources
    let resource_dir = app_handle
        .path()
        .resource_dir()
        .context("cannot get resource dir")?;
    let req_path = resource_dir.join("requirements.txt");

    if !req_path.exists() {
        // Fallback: try a few common locations
        let fallback_paths = [
            resource_dir.join("../requirements.txt"),
            resource_dir.join("../../requirements.txt"),
            PathBuf::from("requirements.txt"),
        ];
        let mut found = false;
        for p in &fallback_paths {
            if p.exists() {
                found = true;
                break;
            }
        }
        if !found {
            anyhow::bail!("找不到 requirements.txt。请手动安装依赖: pip install -r requirements.txt");
        }
    }

    // 4. Install requirements
    let output = Command::new(&venv_python)
        .args([
            "-m",
            "pip",
            "install",
            "--upgrade",
            "pip",
        ])
        .output()
        .context("failed to upgrade pip")?;
    if !output.status.success() {
        log::warn!("pip upgrade warning: {}", String::from_utf8_lossy(&output.stderr));
    }

    let output = Command::new(&venv_python)
        .args([
            "-m",
            "pip",
            "install",
            "-r",
            req_path.to_str().unwrap(),
        ])
        .output()
        .context("failed to install requirements")?;

    if !output.status.success() {
        anyhow::bail!(
            "依赖安装失败: {}",
            String::from_utf8_lossy(&output.stderr)
        );
    }

    Ok(venv_python.to_string_lossy().to_string())
}

/// Check if system Python already has all required packages.
pub fn check_missing_packages(python: &str, packages: &[&str]) -> Result<Vec<String>> {
    let script = format!(
        "import importlib; missing = []; {}\nprint(','.join(missing))",
        packages
            .iter()
            .map(|p| format!("importlib.util.find_spec('{}') or missing.append('{}')", p, p))
            .collect::<Vec<_>>()
            .join("; ")
    );
    let output = Command::new(python)
        .args(["-c", &script])
        .output()
        .context("failed to check packages")?;

    let stdout = String::from_utf8_lossy(&output.stdout);
    Ok(if stdout.trim().is_empty() {
        Vec::new()
    } else {
        stdout.trim().split(',').map(|s| s.to_string()).collect()
    })
}

fn find_python_cmd() -> Option<String> {
    for cmd in ["python3", "python"] {
        if Command::new(cmd).arg("--version").output().is_ok() {
            return Some(cmd.to_string());
        }
    }
    None
}
