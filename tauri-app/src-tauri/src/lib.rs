mod commands;
mod providers;
mod setup;
mod sidecar;
mod sidecar_commands;
mod store;

use sidecar::Sidecar;
use store::Store;
use tauri::{
    menu::{Menu, MenuItem, Submenu},
    tray::TrayIconBuilder,
    Manager,
};

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let store = Store::new().expect("failed to initialize config store");
    let sidecar = Sidecar::new();

    tauri::Builder::default()
        .plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| {
            let _ = app
                .get_webview_window("main")
                .expect("no main window")
                .set_focus();
        }))
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_window_state::Builder::new().build())
        .manage(store)
        .manage(sidecar)
        .invoke_handler(tauri::generate_handler![
            commands::get_config,
            commands::add_provider,
            commands::update_provider,
            commands::delete_provider,
            commands::activate_provider,
            commands::update_ui_prefs,
            commands::get_presets,
            commands::list_backups,
            commands::restore_backup,
            commands::test_provider,
            commands::check_python_env,
            commands::install_python_deps,
            commands::use_system_python,
            sidecar_commands::start_sidecar,
            sidecar_commands::get_sidecar_port,
            sidecar_commands::stop_sidecar,
        ])
        .setup(|app| {
            setup_tray(app)?;
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

fn setup_tray(app: &tauri::App) -> Result<(), Box<dyn std::error::Error>> {
    let show = MenuItem::with_id(app, "show", "显示窗口", true, None::<&str>)?;
    let quit = MenuItem::with_id(app, "quit", "退出", true, None::<&str>)?;

    // Build provider submenu from store
    let store = app.state::<Store>();
    let cfg = store.get_config();
    let mut provider_items: Vec<MenuItem<tauri::Wry>> = Vec::new();
    for p in &cfg.providers {
        let label = if p.id == cfg.active_id {
            format!("✓ {}", p.name)
        } else {
            p.name.clone()
        };
        let item = MenuItem::with_id(app, &format!("provider_{}", p.id), &label, true, None::<&str>)?;
        provider_items.push(item);
    }

    let menu = if provider_items.is_empty() {
        Menu::with_items(app, &[&show, &quit])?
    } else {
        let provider_refs: Vec<&dyn tauri::menu::IsMenuItem<tauri::Wry>> =
            provider_items.iter().map(|i| i as &dyn tauri::menu::IsMenuItem<tauri::Wry>).collect();
        let providers_sub = Submenu::with_items(app, "切换 Provider", true, &provider_refs)?;
        Menu::with_items(app, &[&show, &providers_sub, &quit])?
    };

    TrayIconBuilder::new()
        .icon(app.default_window_icon().unwrap().clone())
        .menu(&menu)
        .tooltip("报销助手")
        .on_menu_event(move |app, event| {
            let id = event.id().as_ref();
            match id {
                "show" => {
                    if let Some(w) = app.get_webview_window("main") {
                        let _ = w.show();
                        let _ = w.set_focus();
                    }
                }
                "quit" => {
                    app.exit(0);
                }
                other if other.starts_with("provider_") => {
                    let provider_id = other.strip_prefix("provider_").unwrap_or("");
                    let store = app.state::<Store>();
                    let _ = store.activate_provider(provider_id);
                }
                _ => {}
            }
        })
        .build(app)?;

    Ok(())
}
