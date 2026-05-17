use tauri::{AppHandle, Manager, State};
use crate::sidecar::Sidecar;
use crate::store::Store;

fn resolve_project_root(app_handle: &AppHandle) -> Result<std::path::PathBuf, String> {
    // 1. Try bundled resources first (release builds)
    let resource_dir = app_handle.path().resource_dir()
        .map_err(|e| format!("无法获取资源目录: {}", e))?;

    if resource_dir.join("web_app.py").exists() {
        return Ok(resource_dir);
    }

    // 2. Dev fallback: walk up from CWD
    let cwd = std::env::current_dir().map_err(|e| e.to_string())?;
    let dev_root = cwd.parent().and_then(|p| p.parent())
        .filter(|p| p.join("web_app.py").exists())
        .unwrap_or(&cwd);

    if dev_root.join("web_app.py").exists() {
        return Ok(dev_root.to_path_buf());
    }

    Err("找不到 web_app.py。请确认应用已正确打包或处于开发目录。".to_string())
}

#[tauri::command]
pub fn start_sidecar(
    app_handle: AppHandle,
    sidecar: State<'_, Sidecar>,
    store: State<'_, Store>,
) -> Result<u16, String> {
    let project_root = resolve_project_root(&app_handle)?;
    let project_root_str = project_root.to_str().unwrap_or(".");

    // Use configured python path if available
    let python_cmd = store.get_python_path();
    let python_cmd = if !python_cmd.is_empty() {
        python_cmd
    } else {
        // Fallback: auto-detect
        if std::process::Command::new("python3").arg("--version").output().is_ok() {
            "python3".to_string()
        } else if std::process::Command::new("python").arg("--version").output().is_ok() {
            "python".to_string()
        } else {
            return Err(
                "未检测到 Python。报销助手的识别功能依赖 Python 后端。\n\
                 请安装 Python 3.9+ 并确保 `python3` 或 `python` 命令可用。\n\
                 macOS: brew install python3\n\
                 Windows: https://python.org/downloads".to_string()
            );
        }
    };

    // Pre-flight: check required packages
    let check = std::process::Command::new(&python_cmd)
        .args([
            "-c",
            "import flask, paddle, openpyxl",
        ])
        .output();

    if let Ok(out) = check {
        if !out.status.success() {
            let stderr = String::from_utf8_lossy(&out.stderr);
            return Err(format!(
                "Python 依赖缺失。请在设置中完成环境安装，或在项目根目录运行:\n\
                 pip install -r requirements.txt\n\n\
                 详情: {}",
                stderr
            ));
        }
    }

    sidecar.start(&python_cmd, project_root_str).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn get_sidecar_port(sidecar: State<'_, Sidecar>) -> u16 {
    sidecar.port()
}

#[tauri::command]
pub fn stop_sidecar(sidecar: State<'_, Sidecar>) {
    sidecar.stop();
}
