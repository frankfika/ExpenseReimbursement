use tauri::State;
use crate::sidecar::Sidecar;

#[tauri::command]
pub fn start_sidecar(sidecar: State<'_, Sidecar>) -> Result<u16, String> {
    let project_root = std::env::current_dir()
        .map(|p| {
            // In dev, cwd is tauri-app/src-tauri; project root is two levels up
            let parent = p.parent().and_then(|pp| pp.parent()).unwrap_or(&p).to_path_buf();
            if parent.join("web_app.py").exists() {
                parent
            } else if p.join("web_app.py").exists() {
                p
            } else {
                // Fallback: look relative to executable
                p
            }
        })
        .unwrap_or_default();

    sidecar.start(project_root.to_str().unwrap_or(".")).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn get_sidecar_port(sidecar: State<'_, Sidecar>) -> u16 {
    sidecar.port()
}

#[tauri::command]
pub fn stop_sidecar(sidecar: State<'_, Sidecar>) {
    sidecar.stop();
}
