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
    return <div className="flex items-center justify-center py-20 text-sm text-slate-400">加载中...</div>;
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 py-20 text-center">
        <p className="text-sm text-slate-500">无法连接到桌面引擎</p>
        <p className="text-xs text-slate-400 max-w-sm">请确保通过桌面应用启动，而非直接在浏览器中打开。</p>
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
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold">Provider 管理</h2>
        <button className="btn-primary text-xs" onClick={() => setShowAdd(true)}>
          <Plus size={14} /> 添加
        </button>
      </div>

      {config.providers.length === 0 ? (
        <div className="card flex flex-col items-center gap-3 py-12 text-center text-sm text-slate-400">
          <p>尚未配置任何 Provider</p>
          <button className="btn-primary text-xs" onClick={() => setShowAdd(true)}>
            <Plus size={14} /> 添加第一个
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
    <div className={`card relative p-4 transition-shadow hover:shadow-card-hover ${isActive ? "ring-2 ring-brand-500" : ""}`}>
      {isActive && (
        <span className="badge-success absolute right-3 top-3">
          <Check size={12} /> 活跃
        </span>
      )}
      <div className="mb-2">
        <h3 className="text-sm font-semibold">{provider.name}</h3>
        <p className="text-xs text-slate-500 truncate">{provider.base_url}</p>
      </div>
      <div className="mb-3 space-y-0.5 text-xs text-slate-500">
        <p>文本: {provider.text_model || "—"}</p>
        <p>视觉: {provider.vision_model || "—"}</p>
        <p>Key: <code className="rounded bg-slate-100 px-1 dark:bg-slate-800">{provider.api_key_masked || "未设置"}</code></p>
      </div>

      {testResult && (
        <p className={`mb-2 text-xs ${testResult.ok ? "text-emerald-600" : "text-rose-600"}`}>
          {testResult.msg}
        </p>
      )}

      <div className="flex items-center gap-1.5">
        {!isActive && (
          <button className="btn-primary text-xs py-1 px-2" onClick={onActivate}>启用</button>
        )}
        <button className="btn-secondary text-xs py-1 px-2" onClick={onTest} disabled={testing}>
          <Zap size={12} /> {testing ? "..." : "测试"}
        </button>
        <div className="flex-1" />
        <button className="btn-danger text-xs py-1 px-2" onClick={onDelete}>
          <Trash2 size={12} />
        </button>
      </div>
    </div>
  );
}
