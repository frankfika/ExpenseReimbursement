import { useState } from "react";
import { X, ArrowLeft, Check } from "lucide-react";
import type { Preset, AddProviderInput } from "../types/provider";

interface Props {
  presets: Preset[];
  onAdd: (input: AddProviderInput) => Promise<void>;
  onClose: () => void;
}

export function AddProviderDialog({ presets, onAdd, onClose }: Props) {
  const [step, setStep] = useState<"preset" | "form">("preset");
  const [selected, setSelected] = useState<Preset | null>(null);
  const [name, setName] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [textModel, setTextModel] = useState("");
  const [visionModel, setVisionModel] = useState("");
  const [useVision, setUseVision] = useState(true);
  const [saving, setSaving] = useState(false);

  const selectPreset = (p: Preset) => {
    setSelected(p);
    setName(p.name);
    setBaseUrl(p.base_url);
    setTextModel(p.text_model);
    setVisionModel(p.vision_model);
    setUseVision(p.use_vision);
    setStep("form");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await onAdd({
        name,
        preset: selected?.id || "custom",
        base_url: baseUrl,
        api_key: apiKey,
        text_model: textModel,
        vision_model: visionModel,
        use_vision: useVision,
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div className="card w-full max-w-lg max-h-[85vh] overflow-y-auto p-6" onClick={(e) => e.stopPropagation()}>
        <div className="mb-5 flex items-center justify-between">
          <div className="flex items-center gap-2">
            {step === "form" && (
              <button className="rounded-lg p-1 text-surface-500 hover:bg-surface-800 hover:text-surface-300" onClick={() => setStep("preset")}>
                <ArrowLeft size={18} />
              </button>
            )}
            <h3 className="text-base font-semibold text-surface-100">{step === "preset" ? "选择预设" : "配置 Provider"}</h3>
          </div>
          <button className="rounded-lg p-1 text-surface-500 hover:bg-surface-800 hover:text-surface-300" onClick={onClose}><X size={18} /></button>
        </div>

        {step === "preset" ? (
          <div className="grid gap-2 sm:grid-cols-2">
            {presets.map((p) => (
              <button
                key={p.id}
                className={`card p-4 text-left transition-all hover:ring-1 hover:ring-brand-500/30 ${selected?.id === p.id ? "ring-1 ring-brand-500" : ""}`}
                onClick={() => selectPreset(p)}
              >
                <p className="text-sm font-medium text-surface-200">{p.name}</p>
                <p className="mt-0.5 text-[11px] text-surface-500 truncate">{p.base_url}</p>
              </button>
            ))}
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label">名称</label>
              <input className="input" value={name} onChange={(e) => setName(e.target.value)} required />
            </div>
            <div>
              <label className="label">API Key *</label>
              <input className="input" type="password" value={apiKey} onChange={(e) => setApiKey(e.target.value)} placeholder="sk-..." required />
            </div>
            <div>
              <label className="label">Base URL</label>
              <input className="input" value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label">文本模型</label>
                <input className="input" value={textModel} onChange={(e) => setTextModel(e.target.value)} />
              </div>
              <div>
                <label className="label">视觉模型</label>
                <input className="input" value={visionModel} onChange={(e) => setVisionModel(e.target.value)} />
              </div>
            </div>
            <label className="flex items-center gap-2.5 text-sm text-surface-300">
              <div className={`flex h-5 w-5 items-center justify-center rounded-md border transition-colors ${useVision ? "border-brand-500 bg-brand-600" : "border-surface-600 bg-surface-800"}`} onClick={() => setUseVision(!useVision)}>
                {useVision && <Check size={12} className="text-white" />}
              </div>
              <input type="checkbox" checked={useVision} onChange={(e) => setUseVision(e.target.checked)} className="sr-only" />
              启用视觉模型（推荐）
            </label>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" className="btn-secondary text-xs" onClick={() => setStep("preset")}>返回</button>
              <button type="submit" className="btn-primary text-xs" disabled={saving}>
                {saving ? "保存中..." : "保存"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
