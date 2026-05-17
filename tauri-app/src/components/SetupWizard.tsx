import { useState, useEffect } from "react";
import { invoke } from "../lib/tauri";
import { Terminal, Loader2, CheckCircle, AlertCircle, Download, ExternalLink } from "lucide-react";

interface EnvStatus {
  python_found: boolean;
  python_path: string;
  packages_ready: boolean;
  missing_packages: string[];
  can_auto_install: boolean;
  install_cmd: string;
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

  const autoInstall = async () => {
    setInstalling(true);
    setInstallLog("正在自动安装 Python，请稍候...");
    setError(null);
    try {
      const path: string = await invoke("auto_install_python");
      setInstallLog(`Python 安装完成: ${path}`);
      setTimeout(() => onReady(), 800);
    } catch (e) {
      setError(String(e));
      setInstalling(false);
    }
  };

  if (checking) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-3">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-brand-500 border-t-transparent" />
        <p className="text-sm text-surface-500">正在检测 Python 环境...</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-md space-y-5 py-12">
      <div className="text-center">
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-600/10 text-brand-400 ring-1 ring-brand-500/20">
          <Terminal size={26} />
        </div>
        <h2 className="text-lg font-semibold text-surface-100">环境配置</h2>
        <p className="mt-1 text-xs text-surface-500">
          发票识别功能依赖 Python 后端，需要完成一次性环境配置
        </p>
      </div>

      {status?.python_found ? (
        <div className="card space-y-4 p-5">
          <div className="flex items-center gap-2 text-sm text-emerald-400">
            <div className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500/10">
              <CheckCircle size={13} />
            </div>
            <span>检测到 Python: <code className="rounded-md bg-surface-800 px-1.5 py-0.5 text-[11px] text-surface-300">{status.python_path}</code></span>
          </div>

          {status.packages_ready ? (
            <div className="flex items-center gap-2 text-sm text-emerald-400">
              <div className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500/10">
                <CheckCircle size={13} />
              </div>
              <span>依赖已就绪</span>
            </div>
          ) : (
            <>
              <div className="flex items-center gap-2 text-sm text-amber-400">
                <div className="flex h-5 w-5 items-center justify-center rounded-full bg-amber-500/10">
                  <AlertCircle size={13} />
                </div>
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
                <div className="flex items-center gap-2 text-xs text-surface-500">
                  <Loader2 size={14} className="animate-spin text-brand-500" />
                  {installLog}
                </div>
              )}
            </>
          )}
        </div>
      ) : (
        <div className="card space-y-4 p-5">
          <div className="flex items-center gap-2 text-sm text-rose-400">
            <div className="flex h-5 w-5 items-center justify-center rounded-full bg-rose-500/10">
              <AlertCircle size={13} />
            </div>
            <span>未检测到 Python</span>
          </div>
          <p className="text-xs text-surface-500">
            已扩大搜索范围（PATH、Homebrew、pyenv、conda、常见安装目录），仍未找到 Python 3.9+。
          </p>

          {status?.can_auto_install ? (
            <>
              <div className="rounded-xl bg-brand-600/5 p-3 text-xs text-brand-300 ring-1 ring-brand-500/20">
                <p className="mb-1.5 font-medium">检测到你的系统支持自动安装</p>
                <code className="block rounded-md bg-surface-800 px-2 py-1.5 text-[11px] text-surface-400 font-mono">
                  {status.install_cmd}
                </code>
              </div>
              {!installing ? (
                <button className="btn-primary text-xs w-full" onClick={autoInstall}>
                  <Download size={14} /> 自动安装 Python
                </button>
              ) : (
                <div className="flex items-center gap-2 text-xs text-surface-500">
                  <Loader2 size={14} className="animate-spin text-brand-500" />
                  {installLog}
                </div>
              )}
            </>
          ) : (
            <div className="space-y-1.5 text-xs text-surface-400">
              <p><span className="text-surface-500">macOS:</span> brew install python3</p>
              <p className="flex items-center gap-1">
                <span className="text-surface-500">Windows:</span>
                <a href="https://python.org/downloads" target="_blank" rel="noreferrer" className="inline-flex items-center gap-0.5 text-brand-400 hover:text-brand-300">
                  python.org/downloads <ExternalLink size={10} />
                </a>
              </p>
              <p><span className="text-surface-500">Linux:</span> sudo apt-get install python3 python3-pip</p>
            </div>
          )}
          <button className="btn-secondary text-xs w-full" onClick={checkEnv}>
            重新检测
          </button>
        </div>
      )}

      {error && (
        <div className="rounded-xl bg-rose-500/10 p-3 text-xs text-rose-400 ring-1 ring-rose-500/20">
          {error}
        </div>
      )}
    </div>
  );
}
