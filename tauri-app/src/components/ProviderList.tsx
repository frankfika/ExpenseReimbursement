import { useState } from "react";
import { Check, Plus, Trash2, Zap } from "lucide-react";
import { useProviders } from "../hooks/useProviders";
import type { Provider } from "../types/provider";
import { AddProviderDialog } from "./AddProviderDialog";

export function ProviderList() {
  const { config, presets, loading, error, addProvider, deleteProvider, activateProvider, testProvider } = useProviders();
  const [showAdd, setShowAdd] = useState(false);
  const [testing, setTesting] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<{ id: string; ok: boolean; msg: string } | null>(null);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-5 w-5 animate-spin rounded-full border-2 border-brand-500 border-t-transparent" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 py-20 text-center">
        <p className="text-sm text-surface-400">无法连接到桌面引擎</p>
        <p className="max-w-sm text-xs text-surface-600">请确保通过桌面应用启动，而非直接在浏览器中打开。</p>
      </div>
    );
  }

  if (!config) {
    return null;
  }

  const handleTest = async (id: string) => {
    setTesting(id);
    setTestResult(null);
    try {
      const msg = await testProvider(id);
      setTestResult({ id, ok: true, msg });
    } catch (e: any) {
      setTestResult({ id, ok: false, msg: e });
    } finally {
      setTesting(null);
    }
  };

  const handleDelete = async (p: Provider) => {
    if (!confirm(`确定删除 "${p.name}" 吗？`)) return;
    await deleteProvider(p.id);
  };

  return (
    <div className="mx-auto max-w-3xl space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-surface-100">Provider 管理</h2>
          <p className="mt-0.5 text-xs text-surface-500">配置 AI 服务提供商，支持一键切换</p>
        </div>
        <button className="btn-primary text-xs" onClick={() => setShowAdd(true)}>
          <Plus size={14} /> 添加
        </button>
      </div>

      {config.providers.length === 0 ? (
        <div className="card flex flex-col items-center gap-3 py-16 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-surface-800">
            <Plus size={24} className="text-surface-500" />
          </div>
          <p className="text-sm text-surface-400">尚未配置任何 Provider</p>
          <button className="btn-primary text-xs" onClick={() => setShowAdd(true)}>
            添加第一个
          </button>
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {config.providers.map((p) => (
            <ProviderCard
              key={p.id}
              provider={p}
              isActive={p.id === config.active_id}
              onActivate={() => activateProvider(p.id)}
              onTest={() => handleTest(p.id)}
              onDelete={() => handleDelete(p)}
              testing={testing === p.id}
              testResult={testResult?.id === p.id ? testResult : null}
            />
          ))}
        </div>
      )}

      {showAdd && (
        <AddProviderDialog
          presets={presets}
          onAdd={async (input) => { await addProvider(input); setShowAdd(false); }}
          onClose={() => setShowAdd(false)}
        />
      )}
    </div>
  );
}

interface ProviderCardProps {
  provider: Provider;
  isActive: boolean;
  onActivate: () => void;
  onTest: () => void;
  onDelete: () => void;
  testing: boolean;
  testResult: { ok: boolean; msg: string } | null;
}

function ProviderCard({ provider, isActive, onActivate, onTest, onDelete, testing, testResult }: ProviderCardProps) {
  return (
    <div className={`card relative p-5 transition-all hover:ring-1 hover:ring-white/[0.08] ${isActive ? "ring-1 ring-brand-500/50 shadow-glow" : ""}`}>
      {isActive && (
        <span className="badge-success absolute right-4 top-4">
          <Check size={10} /> 活跃
        </span>
      )}
      <div className="mb-3">
        <h3 className="text-sm font-semibold text-surface-100">{provider.name}</h3>
        <p className="mt-0.5 text-[11px] text-surface-500 truncate">{provider.base_url}</p>
      </div>
      <div className="mb-3 space-y-1 text-[11px] text-surface-500">
        <p>
          <span className="text-surface-600">文本:</span> {provider.text_model || "—"}
        </p>
        <p>
          <span className="text-surface-600">视觉:</span> {provider.vision_model || "—"}
        </p>
        <p>
          <span className="text-surface-600">Key:</span>{" "}
          <code className="rounded-md bg-surface-800 px-1.5 py-0.5 text-surface-400">{provider.api_key_masked || "未设置"}</code>
        </p>
      </div>

      {testResult && (
        <div className={`mb-3 rounded-lg px-3 py-2 text-xs ${testResult.ok ? "bg-emerald-500/10 text-emerald-400" : "bg-rose-500/10 text-rose-400"}`}>
          {testResult.msg}
        </div>
      )}

      <div className="flex items-center gap-2">
        {!isActive && (
          <button className="btn-primary py-1.5 px-3 text-[11px]" onClick={onActivate}>启用</button>
        )}
        <button className="btn-secondary py-1.5 px-3 text-[11px]" onClick={onTest} disabled={testing}>
          <Zap size={11} /> {testing ? "..." : "测试"}
        </button>
        <div className="flex-1" />
        <button className="rounded-lg p-1.5 text-surface-600 hover:bg-rose-950/30 hover:text-rose-400" onClick={onDelete}>
          <Trash2 size={13} />
        </button>
      </div>
    </div>
  );
}
