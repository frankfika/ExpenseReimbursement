import { useState, useEffect } from "react";
import { invoke } from "../lib/tauri";
import { Terminal, Loader2, CheckCircle, AlertCircle, Download } from "lucide-react";

interface EnvStatus {
  python_found: boolean;
  python_path: string;
  packages_ready: boolean;
  missing_packages: string[];
}

export function SetupWizard({ onReady }: { onReady: () => void }) {
  const [status, setStatus] = useState<EnvStatus | null>(null);
  const [checking, setChecking] = useState(true);
  const [installing, setInstalling] = useState(false);
  const [installLog, setInstallLog] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    checkEnv();
  }, []);

  const checkEnv = async () => {
    setChecking(true);
    setError(null);
    try {
      const s: EnvStatus = await invoke("check_python_env");
      setStatus(s);
      if (s.python_found && s.packages_ready) {
        await invoke("use_system_python", { path: s.python_path });
        onReady();
      }
    } catch (e) {
      setError(String(e));
    } finally {
      setChecking(false);
    }
  };

  const installVenv = async () => {
    setInstalling(true);
    setInstallLog("正在创建虚拟环境并安装依赖，请稍候...");
    setError(null);
    try {
      const path: string = await invoke("install_python_deps");
      setInstallLog(`安装完成！Python 路径: ${path}`);
      setTimeout(() => onReady(), 800);
    } catch (e) {
      setError(String(e));
      setInstalling(false);
    }
  };

  const useSystem = async () => {
    if (!status?.python_path) return;
    try {
      await invoke("use_system_python", { path: status.python_path });
      onReady();
    } catch (e) {
      setError(String(e));
    }
  };

  if (checking) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-3 text-slate-500">
        <Loader2 size={24} className="animate-spin text-brand-500" />
        <p className="text-sm">正在检测 Python 环境...</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-md space-y-5 py-12">
      <div className="text-center">
        <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-brand-50 text-brand-600">
          <Terminal size={24} />
        </div>
        <h2 className="text-base font-semibold">环境配置</h2>
        <p className="mt-1 text-xs text-slate-500">
          发票识别功能依赖 Python 后端，需要完成一次性环境配置
        </p>
      </div>

      {status?.python_found ? (
        <div className="card space-y-3 p-4">
          <div className="flex items-center gap-2 text-sm text-emerald-600">
            <CheckCircle size={16} />
            <span>检测到 Python: {status.python_path}</span>
          </div>

          {status.packages_ready ? (
            <div className="flex items-center gap-2 text-sm text-emerald-600">
              <CheckCircle size={16} />
              <span>依赖已就绪</span>
            </div>
          ) : (
            <>
              <div className="flex items-center gap-2 text-sm text-amber-600">
                <AlertCircle size={16} />
                <span>缺少依赖: {status.missing_packages.join(", ")}</span>
              </div>

              {!installing ? (
                <div className="flex gap-2 pt-1">
                  <button className="btn-primary text-xs flex-1" onClick={installVenv}>
                    <Download size={14} /> 自动安装到虚拟环境
                  </button>
                  {status.python_path && (
                    <button className="btn-secondary text-xs" onClick={useSystem}>
                      使用当前 Python
                    </button>
                  )}
                </div>
              ) : (
                <div className="flex items-center gap-2 text-xs text-slate-500">
                  <Loader2 size={14} className="animate-spin" />
                  {installLog}
                </div>
              )}
            </>
          )}
        </div>
      ) : (
        <div className="card space-y-3 p-4">
          <div className="flex items-center gap-2 text-sm text-rose-600">
            <AlertCircle size={16} />
            <span>未检测到 Python</span>
          </div>
          <p className="text-xs text-slate-500">
            请安装 Python 3.9+ 后重新打开应用。
          </p>
          <div className="space-y-1 text-xs text-slate-600">
            <p><strong>macOS:</strong> brew install python3</p>
            <p><strong>Windows:</strong> <a href="https://python.org/downloads" target="_blank" rel="noreferrer" className="text-brand-600 underline">python.org/downloads</a></p>
          </div>
          <button className="btn-secondary text-xs w-full" onClick={checkEnv}>
            重新检测
          </button>
        </div>
      )}

      {error && (
        <div className="rounded-lg bg-rose-50 p-3 text-xs text-rose-700">
          {error}
        </div>
      )}
    </div>
  );
}
