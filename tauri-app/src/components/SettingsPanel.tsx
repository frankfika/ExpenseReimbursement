import { useState, useEffect } from "react";
import { invoke } from "../lib/tauri";
import { Sun, Moon, Monitor, RotateCcw, Clock } from "lucide-react";
import type { UiPrefs } from "../types/provider";

export function SettingsPanel() {
  const [theme, setTheme] = useState<string>("system");
  const [backups, setBackups] = useState<string[]>([]);
  const [restoring, setRestoring] = useState(false);

  useEffect(() => {
    invoke<{ active_id: string; providers: any[]; ui: UiPrefs }>("get_config").then((cfg) => {
      setTheme(cfg.ui.theme);
      applyTheme(cfg.ui.theme);
    }).catch(() => {});
    invoke<string[]>("list_backups").then(setBackups).catch(() => {});
  }, []);

  const applyTheme = (t: string) => {
    const root = document.documentElement;
    if (t === "dark") {
      root.classList.add("dark");
    } else if (t === "light") {
      root.classList.remove("dark");
    } else {
      if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
        root.classList.add("dark");
      } else {
        root.classList.remove("dark");
      }
    }
  };

  const changeTheme = async (t: string) => {
    setTheme(t);
    applyTheme(t);
    try { await invoke("update_ui_prefs", { prefs: { theme: t, language: "zh" } }); } catch {}
  };

  const handleRestore = async (filename: string) => {
    if (!confirm(`确定恢复备份 ${filename}？当前配置将被覆盖。`)) return;
    setRestoring(true);
    try {
      await invoke("restore_backup", { filename });
      window.location.reload();
    } catch (e: any) {
      alert("恢复失败: " + e);
    } finally {
      setRestoring(false);
    }
  };

  const themes = [
    { id: "light", label: "浅色", icon: Sun },
    { id: "dark", label: "深色", icon: Moon },
    { id: "system", label: "跟随系统", icon: Monitor },
  ];

  return (
    <div className="mx-auto max-w-lg space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-surface-100 mb-1">外观</h2>
        <p className="text-xs text-surface-500 mb-4">选择您喜欢的界面主题</p>
        <div className="flex gap-2">
          {themes.map((t) => (
            <button
              key={t.id}
              className={`card flex flex-1 flex-col items-center gap-2 p-4 transition-all ${theme === t.id ? "ring-1 ring-brand-500 shadow-glow" : "hover:ring-1 hover:ring-white/[0.06]"}`}
              onClick={() => changeTheme(t.id)}
            >
              <t.icon size={20} className={theme === t.id ? "text-brand-400" : "text-surface-500"} />
              <span className="text-xs text-surface-300">{t.label}</span>
            </button>
          ))}
        </div>
      </div>

      <div>
        <h2 className="text-lg font-semibold text-surface-100 mb-1">备份恢复</h2>
        <p className="text-xs text-surface-500 mb-4">从自动备份中恢复 Provider 配置</p>
        {backups.length === 0 ? (
          <div className="card flex items-center gap-3 p-4">
            <Clock size={16} className="text-surface-600" />
            <p className="text-xs text-surface-500">暂无备份</p>
          </div>
        ) : (
          <div className="card divide-y divide-white/[0.04]">
            {backups.slice(0, 10).map((b) => (
              <div key={b} className="flex items-center justify-between px-4 py-3">
                <div className="flex items-center gap-2">
                  <Clock size={13} className="text-surface-600" />
                  <span className="text-xs text-surface-400 font-mono">{b}</span>
                </div>
                <button
                  className="rounded-lg px-2.5 py-1 text-xs text-surface-500 hover:bg-surface-800 hover:text-surface-300 transition-colors"
                  onClick={() => handleRestore(b)}
                  disabled={restoring}
                >
                  <RotateCcw size={11} className="inline mr-1" /> 恢复
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
