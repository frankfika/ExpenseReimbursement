import { useState, useEffect } from "react";
import { invoke } from "../lib/tauri";
import { Sun, Moon, Monitor, RotateCcw } from "lucide-react";
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
        <h2 className="text-base font-semibold mb-3">外观</h2>
        <div className="flex gap-2">
          {themes.map((t) => (
            <button
              key={t.id}
              className={`card flex flex-1 flex-col items-center gap-1.5 p-3 transition-shadow hover:shadow-card-hover ${theme === t.id ? "ring-2 ring-brand-500" : ""}`}
              onClick={() => changeTheme(t.id)}
            >
              <t.icon size={20} className={theme === t.id ? "text-brand-600" : "text-slate-400"} />
              <span className="text-xs">{t.label}</span>
            </button>
          ))}
        </div>
      </div>

      <div>
        <h2 className="text-base font-semibold mb-3">备份恢复</h2>
        {backups.length === 0 ? (
          <p className="text-xs text-slate-400">暂无备份</p>
        ) : (
          <div className="card divide-y divide-slate-100 dark:divide-slate-800">
            {backups.slice(0, 10).map((b) => (
              <div key={b} className="flex items-center justify-between px-4 py-2.5">
                <span className="text-xs text-slate-600 dark:text-slate-300 font-mono">{b}</span>
                <button
                  className="btn-ghost text-xs"
                  onClick={() => handleRestore(b)}
                  disabled={restoring}
                >
                  <RotateCcw size={12} /> 恢复
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
