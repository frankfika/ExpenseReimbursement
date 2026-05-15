import { useState, useEffect } from "react";
import { invoke } from "../lib/tauri";
import { open } from "@tauri-apps/plugin-dialog";
import { Upload as UploadIcon, FolderOpen, FileText, Download, Loader2 } from "lucide-react";

interface TaskStatus {
  status: string;
  total: number;
  current: number;
  current_file: string;
  summary?: Record<string, { count: number; amount: number }>;
  total_amount?: number;
  error?: string;
}

export function UploadPanel() {
  const [port, setPort] = useState<number>(0);
  const [starting, setStarting] = useState(false);
  const [files, setFiles] = useState<string[]>([]);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [status, setStatus] = useState<TaskStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notTauri, setNotTauri] = useState(false);

  useEffect(() => {
    invoke<number>("get_sidecar_port").then((p) => {
      if (p > 0) setPort(p);
    }).catch(() => setNotTauri(true));
  }, []);

  // Poll status
  useEffect(() => {
    if (!taskId || !port) return;
    const interval = setInterval(async () => {
      try {
        const resp = await fetch(`http://127.0.0.1:${port}/status/${taskId}`);
        if (resp.ok) {
          const data: TaskStatus = await resp.json();
          setStatus(data);
          if (data.status === "completed" || data.status === "error") {
            clearInterval(interval);
          }
        }
      } catch {}
    }, 800);
    return () => clearInterval(interval);
  }, [taskId, port]);

  // All hooks above — safe to early-return below

  if (notTauri) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 py-20 text-center">
        <p className="text-sm text-slate-500">识别功能需要桌面应用环境</p>
        <p className="text-xs text-slate-400">请通过 Tauri 桌面应用启动，而非浏览器直接访问。</p>
      </div>
    );
  }

  const ensureSidecar = async (): Promise<number> => {
    if (port > 0) return port;
    setStarting(true);
    try {
      const p = await invoke<number>("start_sidecar");
      setPort(p);
      return p;
    } finally {
      setStarting(false);
    }
  };

  const selectFolder = async () => {
    const selected = await open({ directory: true, multiple: false });
    if (!selected) return;
    const folder = selected as string;
    const resp = await fetch(`http://127.0.0.1:${await ensureSidecar()}/scan-folder`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: folder }),
    }).catch(() => null);

    if (resp && resp.ok) {
      const data = await resp.json();
      setFiles(data.files || []);
    } else {
      setFiles([folder]);
    }
  };

  const startProcessing = async () => {
    setError(null);
    const p = await ensureSidecar();
    const resp = await fetch(`http://127.0.0.1:${p}/upload`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ paths: files }),
    });
    if (!resp.ok) {
      const data = await resp.json();
      setError(data.error || "上传失败");
      return;
    }
    const data = await resp.json();
    setTaskId(data.task_id);
  };

  const handleDownload = () => {
    if (!taskId || !port) return;
    window.open(`http://127.0.0.1:${port}/download/${taskId}`, "_blank");
  };

  const reset = () => {
    setFiles([]);
    setTaskId(null);
    setStatus(null);
    setError(null);
  };

  if (taskId && status) {
    return (
      <div className="mx-auto max-w-lg space-y-4">
        <h2 className="text-base font-semibold">处理进度</h2>
        <div className="card p-5 space-y-3">
          {status.status === "completed" ? (
            <>
              <p className="text-sm text-emerald-600 font-medium">处理完成</p>
              {status.summary && (
                <div className="space-y-1 text-xs text-slate-600">
                  {Object.entries(status.summary).map(([cat, info]) => (
                    <div key={cat} className="flex justify-between">
                      <span>{cat}</span>
                      <span>{info.count} 张 · ¥{info.amount.toFixed(2)}</span>
                    </div>
                  ))}
                  <div className="border-t pt-1 font-medium flex justify-between">
                    <span>合计</span>
                    <span>¥{status.total_amount?.toFixed(2)}</span>
                  </div>
                </div>
              )}
              <div className="flex gap-2 pt-2">
                <button className="btn-primary text-xs" onClick={handleDownload}>
                  <Download size={14} /> 下载结果
                </button>
                <button className="btn-secondary text-xs" onClick={reset}>重新开始</button>
              </div>
            </>
          ) : status.status === "error" ? (
            <>
              <p className="text-sm text-rose-600">{status.error}</p>
              <button className="btn-secondary text-xs" onClick={reset}>重试</button>
            </>
          ) : (
            <>
              <div className="flex items-center gap-2">
                <Loader2 size={16} className="animate-spin text-brand-500" />
                <span className="text-sm">{status.current}/{status.total}</span>
              </div>
              <p className="text-xs text-slate-500 truncate">{status.current_file}</p>
              <div className="h-1.5 rounded-full bg-slate-100 overflow-hidden">
                <div
                  className="h-full rounded-full bg-brand-500 transition-all"
                  style={{ width: `${status.total ? (status.current / status.total) * 100 : 0}%` }}
                />
              </div>
            </>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-lg space-y-4">
      <h2 className="text-base font-semibold">发票识别</h2>

      {starting && (
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <Loader2 size={14} className="animate-spin" /> 正在启动识别引擎...
        </div>
      )}

      <div
        className="card flex flex-col items-center gap-3 border-2 border-dashed border-slate-200 p-10 text-center cursor-pointer hover:border-brand-400 transition-colors"
        onClick={selectFolder}
      >
        <FolderOpen size={32} className="text-slate-300" />
        <p className="text-sm text-slate-600">点击选择发票文件夹</p>
        <p className="text-xs text-slate-400">支持 JPG、PNG、PDF</p>
      </div>

      {files.length > 0 && (
        <div className="card p-4 space-y-2">
          <p className="text-xs font-medium text-slate-600">
            <FileText size={12} className="inline mr-1" />
            已选 {files.length} 个文件
          </p>
          {error && <p className="text-xs text-rose-600">{error}</p>}
          <div className="flex gap-2">
            <button className="btn-primary text-xs" onClick={startProcessing}>
              <UploadIcon size={14} /> 开始处理
            </button>
            <button className="btn-secondary text-xs" onClick={reset}>清空</button>
          </div>
        </div>
      )}
    </div>
  );
}