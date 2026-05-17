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
    pub can_auto_install: bool,
    pub install_cmd: String,
}

/// Detect available python command and check required packages.
pub fn check_environment(_app_handle: &AppHandle) -> Result<EnvStatus> {
    let python_cmd = find_python_cmd();
    let mut status = EnvStatus {
        python_found: false,
        python_path: String::new(),
        packages_ready: false,
        missing_packages: Vec::new(),
        can_auto_install: false,
        install_cmd: String::new(),
    };

    let Some(python) = python_cmd else {
        // No Python found - check if we can auto-install
        status.can_auto_install = can_auto_install();
        if cfg!(target_os = "macos") && has_homebrew() {
            status.install_cmd = "brew install python3".to_string();
        } else if cfg!(target_os = "linux") {
            if Command::new("apt-get").arg("--version").output().is_ok() {
                status.install_cmd = "sudo apt-get update && sudo apt-get install -y python3 python3-venv python3-pip".to_string();
            } else if Command::new("dnf").arg("--version").output().is_ok() {
                status.install_cmd = "sudo dnf install -y python3 python3-pip".to_string();
            } else if Command::new("pacman").arg("--version").output().is_ok() {
                status.install_cmd = "sudo pacman -S --noconfirm python python-pip".to_string();
            }
        }
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

pub fn find_python_cmd() -> Option<String> {
    // 1. Check PATH first
    for cmd in ["python3", "python"] {
        if Command::new(cmd).arg("--version").output().is_ok() {
            return Some(cmd.to_string());
        }
    }

    // 2. Search common installation locations
    let candidates: Vec<std::path::PathBuf> = {
        let mut v = Vec::new();

        if cfg!(target_os = "macos") {
            // Homebrew (Apple Silicon)
            v.push("/opt/homebrew/bin/python3".into());
            // Homebrew (Intel)
            v.push("/usr/local/bin/python3".into());
            // System Python
            v.push("/usr/bin/python3".into());
            // MacPorts
            v.push("/opt/local/bin/python3".into());
            // pyenv
            if let Ok(home) = std::env::var("HOME") {
                v.push(format!("{}/.pyenv/shims/python3", home).into());
                v.push(format!("{}/.pyenv/versions/*/bin/python3", home).into());
            }
            // conda
            if let Ok(home) = std::env::var("HOME") {
                v.push(format!("{}/anaconda3/bin/python3", home).into());
                v.push(format!("{}/miniconda3/bin/python3", home).into());
                v.push(format!("{}/opt/anaconda3/bin/python3", home).into());
                v.push(format!("{}/opt/miniconda3/bin/python3", home).into());
            }
        }

        if cfg!(target_os = "windows") {
            // Common Windows install paths
            v.push("C:\\Python311\\python.exe".into());
            v.push("C:\\Python312\\python.exe".into());
            v.push("C:\\Python313\\python.exe".into());
            v.push("C:\\Python310\\python.exe".into());
            v.push("C:\\Python39\\python.exe".into());
            // Windows Store / User install
            if let Ok(local_app_data) = std::env::var("LOCALAPPDATA") {
                v.push(format!("{}\\Programs\\Python\\Python311\\python.exe", local_app_data).into());
                v.push(format!("{}\\Programs\\Python\\Python312\\python.exe", local_app_data).into());
                v.push(format!("{}\\Programs\\Python\\Python313\\python.exe", local_app_data).into());
                v.push(format!("{}\\Programs\\Python\\Python310\\python.exe", local_app_data).into());
                v.push(format!("{}\\Programs\\Python\\Python39\\python.exe", local_app_data).into());
            }
            // pyenv-win
            if let Ok(userprofile) = std::env::var("USERPROFILE") {
                v.push(format!("{}\\.pyenv\\pyenv-win\\versions\\*\\python.exe", userprofile).into());
            }
        }

        if cfg!(target_os = "linux") {
            v.push("/usr/bin/python3".into());
            v.push("/usr/local/bin/python3".into());
            v.push("/opt/python3/bin/python3".into());
            if let Ok(home) = std::env::var("HOME") {
                v.push(format!("{}/.pyenv/shims/python3", home).into());
                v.push(format!("{}/anaconda3/bin/python3", home).into());
                v.push(format!("{}/miniconda3/bin/python3", home).into());
            }
        }

        v
    };

    for candidate in candidates {
        if candidate.exists() {
            if Command::new(&candidate).arg("--version").output().is_ok() {
                return Some(candidate.to_string_lossy().to_string());
            }
        }
        // Handle wildcard paths (e.g. pyenv versions)
        if let Some(parent) = candidate.parent() {
            if candidate.to_string_lossy().contains('*') {
                if let Ok(entries) = std::fs::read_dir(parent) {
                    for entry in entries.flatten() {
                        let path = entry.path();
                        if path.is_dir() {
                            let python_bin = path.join("bin").join("python3");
                            if python_bin.exists() {
                                if Command::new(&python_bin).arg("--version").output().is_ok() {
                                    return Some(python_bin.to_string_lossy().to_string());
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    None
}

/// Check if Homebrew is available (macOS only).
pub fn has_homebrew() -> bool {
    cfg!(target_os = "macos") && Command::new("brew").arg("--version").output().is_ok()
}

/// Check if we can auto-install Python via available package managers.
pub fn can_auto_install() -> bool {
    if cfg!(target_os = "macos") {
        has_homebrew()
    } else if cfg!(target_os = "windows") {
        // On Windows, we could potentially download the installer
        // but this requires admin privileges. For now, report false.
        false
    } else if cfg!(target_os = "linux") {
        // Check for apt, yum, dnf, pacman
        ["apt-get", "yum", "dnf", "pacman"]
            .iter()
            .any(|cmd| Command::new(cmd).arg("--version").output().is_ok())
    } else {
        false
    }
}
