import { useState, useEffect } from "react";
import { Receipt, Settings, Upload, Palette } from "lucide-react";
import { ProviderList } from "./components/ProviderList";
import { UploadPanel } from "./components/UploadPanel";
import { SettingsPanel } from "./components/SettingsPanel";
import { SetupWizard } from "./components/SetupWizard";
import { invoke } from "./lib/tauri";

type Tab = "providers" | "upload" | "settings";

function App() {
  const [tab, setTab] = useState<Tab>("providers");
  const [envReady, setEnvReady] = useState<boolean | null>(null);

  useEffect(() => {
    invoke<{ packages_ready: boolean }>("check_python_env")
      .then((s) => setEnvReady(s.packages_ready ?? false))
      .catch(() => setEnvReady(false));
  }, []);

  if (envReady === null) {
    return (
      <div className="flex h-full items-center justify-center text-slate-500">
        <div className="animate-pulse text-sm">加载中...</div>
      </div>
    );
  }

  if (!envReady) {
    return (
      <div className="flex h-full flex-col">
        <header className="flex items-center gap-3 border-b border-slate-200 bg-white/80 px-6 py-3 backdrop-blur dark:border-slate-800 dark:bg-slate-900/80">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-white">
            <Receipt size={18} />
          </div>
          <div>
            <h1 className="text-sm font-semibold leading-none">报销助手</h1>
            <p className="text-xs text-slate-500 dark:text-slate-400">v2.0 · Tauri Edition</p>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto">
          <SetupWizard onReady={() => setEnvReady(true)} />
        </main>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <header className="flex items-center gap-3 border-b border-slate-200 bg-white/80 px-6 py-3 backdrop-blur dark:border-slate-800 dark:bg-slate-900/80">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-white">
          <Receipt size={18} />
        </div>
        <div className="mr-auto">
          <h1 className="text-sm font-semibold leading-none">报销助手</h1>
          <p className="text-xs text-slate-500 dark:text-slate-400">v2.0 · Tauri Edition</p>
        </div>
        <nav className="flex gap-1">
          <button
            className={`btn-ghost text-xs ${tab === "providers" ? "bg-slate-100 dark:bg-slate-800" : ""}`}
            onClick={() => setTab("providers")}
          >
            <Settings size={14} /> Providers
          </button>
          <button
            className={`btn-ghost text-xs ${tab === "upload" ? "bg-slate-100 dark:bg-slate-800" : ""}`}
            onClick={() => setTab("upload")}
          >
            <Upload size={14} /> 识别
          </button>
          <button
            className={`btn-ghost text-xs ${tab === "settings" ? "bg-slate-100 dark:bg-slate-800" : ""}`}
            onClick={() => setTab("settings")}
          >
            <Palette size={14} /> 外观
          </button>
        </nav>
      </header>

      <main className="flex-1 overflow-y-auto p-6">
        {tab === "providers" && <ProviderList />}
        {tab === "upload" && <UploadPanel />}
        {tab === "settings" && <SettingsPanel />}
      </main>
    </div>
  );
}

export default App;
