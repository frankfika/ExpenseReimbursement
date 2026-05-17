import { useState, useEffect } from "react";
import { Receipt, Settings, Upload, Sparkles } from "lucide-react";
import { ProviderList } from "./components/ProviderList";
import { UploadPanel } from "./components/UploadPanel";
import { SettingsPanel } from "./components/SettingsPanel";
import { SetupWizard } from "./components/SetupWizard";
import { ToastContainer } from "./components/ToastContainer";
import { ToastProvider, useToastContext } from "./context/ToastContext";
import { invoke } from "./lib/tauri";

type Tab = "providers" | "upload" | "settings";

function AppContent() {
  const [tab, setTab] = useState<Tab>("providers");
  const [envReady, setEnvReady] = useState<boolean | null>(null);
  const { toasts, remove } = useToastContext();

  useEffect(() => {
    invoke<{ packages_ready: boolean }>("check_python_env")
      .then((s) => setEnvReady(s.packages_ready ?? false))
      .catch(() => setEnvReady(false));
  }, []);

  if (envReady === null) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-brand-500 border-t-transparent" />
          <p className="text-sm text-surface-500">正在初始化...</p>
        </div>
      </div>
    );
  }

  if (!envReady) {
    return (
      <div className="flex h-full flex-col">
        <header className="flex items-center gap-3 border-b border-white/[0.06] bg-surface-950/80 px-6 py-3.5 backdrop-blur-xl">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 text-white shadow-glow">
            <Receipt size={18} />
          </div>
          <div>
            <h1 className="text-sm font-semibold leading-none text-surface-100">报销助手</h1>
            <p className="mt-0.5 text-[11px] text-surface-500">v2.0.3 · Tauri Edition</p>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto">
          <SetupWizard onReady={() => setEnvReady(true)} />
        </main>
        <ToastContainer toasts={toasts} onRemove={remove} />
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <header className="flex items-center gap-3 border-b border-white/[0.06] bg-surface-950/80 px-6 py-3.5 backdrop-blur-xl">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 text-white shadow-glow">
          <Receipt size={18} />
        </div>
        <div className="mr-auto">
          <h1 className="text-sm font-semibold leading-none text-surface-100">报销助手</h1>
          <p className="mt-0.5 text-[11px] text-surface-500">AI 智能发票识别与报销整理</p>
        </div>
        <nav className="flex gap-1.5">
          <button
            className={tab === "providers" ? "nav-item-active" : "nav-item-inactive"}
            onClick={() => setTab("providers")}
          >
            <Settings size={14} /> Providers
          </button>
          <button
            className={tab === "upload" ? "nav-item-active" : "nav-item-inactive"}
            onClick={() => setTab("upload")}
          >
            <Upload size={14} /> 识别
          </button>
          <button
            className={tab === "settings" ? "nav-item-active" : "nav-item-inactive"}
            onClick={() => setTab("settings")}
          >
            <Sparkles size={14} /> 外观
          </button>
        </nav>
      </header>

      <main className="flex-1 overflow-y-auto p-6">
        {tab === "providers" && <ProviderList />}
        {tab === "upload" && <UploadPanel />}
        {tab === "settings" && <SettingsPanel />}
      </main>
      <ToastContainer toasts={toasts} onRemove={remove} />
    </div>
  );
}

function App() {
  return (
    <ToastProvider>
      <AppContent />
    </ToastProvider>
  );
}

export default App;
