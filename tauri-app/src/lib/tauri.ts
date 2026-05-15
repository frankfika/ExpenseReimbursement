import { invoke as tauriInvoke } from "@tauri-apps/api/core";

const isTauri = !!(window as any).__TAURI_INTERNALS__;

export async function invoke<T>(cmd: string, args?: Record<string, unknown>): Promise<T> {
  if (!isTauri) {
    throw new Error(`Tauri not available (command: ${cmd}). Please run inside the desktop app.`);
  }
  return tauriInvoke<T>(cmd, args);
}
