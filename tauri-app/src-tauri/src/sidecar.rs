use std::net::TcpListener;
use std::process::{Child, Command};
use std::sync::atomic::{AtomicU16, Ordering};
use std::time::Duration;

use anyhow::{Context, Result};
use parking_lot::Mutex;

static SIDECAR_PORT: AtomicU16 = AtomicU16::new(0);

pub struct Sidecar {
    process: Mutex<Option<Child>>,
}

impl Sidecar {
    pub fn new() -> Self {
        Self {
            process: Mutex::new(None),
        }
    }

    pub fn start(&self, python_cmd: &str, project_root: &str) -> Result<u16> {
        let port = find_free_port(5100).context("no free port")?;
        SIDECAR_PORT.store(port, Ordering::SeqCst);

        let child = Command::new(python_cmd)
            .args([
                "-c",
                &format!(
                    "import sys; sys.path.insert(0, '{}'); from web_app import app; app.run(host='127.0.0.1', port={}, debug=False, threaded=True)",
                    project_root, port
                ),
            ])
            .spawn()
            .context(format!("failed to spawn {} sidecar", python_cmd))?;

        *self.process.lock() = Some(child);

        // Wait for server to be ready
        let ready = wait_for_port(port, Duration::from_secs(30));
        if !ready {
            self.stop();
            anyhow::bail!("sidecar did not start within 30s");
        }

        log::info!("Python sidecar started on port {}", port);
        Ok(port)
    }

    pub fn port(&self) -> u16 {
        SIDECAR_PORT.load(Ordering::SeqCst)
    }

    pub fn stop(&self) {
        if let Some(mut child) = self.process.lock().take() {
            let _ = child.kill();
            let _ = child.wait();
        }
    }
}

impl Drop for Sidecar {
    fn drop(&mut self) {
        self.stop();
    }
}

fn find_free_port(start: u16) -> Option<u16> {
    for port in start..start + 100 {
        if TcpListener::bind(("127.0.0.1", port)).is_ok() {
            return Some(port);
        }
    }
    None
}

fn wait_for_port(port: u16, timeout: Duration) -> bool {
    let start = std::time::Instant::now();
    while start.elapsed() < timeout {
        if std::net::TcpStream::connect(("127.0.0.1", port)).is_ok() {
            return true;
        }
        std::thread::sleep(Duration::from_millis(100));
    }
    false
}
