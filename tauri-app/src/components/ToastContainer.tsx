import { X, CheckCircle, AlertCircle, Info } from "lucide-react";
import type { Toast } from "../types/toast";

interface Props {
  toasts: Toast[];
  onRemove: (id: string) => void;
}

export function ToastContainer({ toasts, onRemove }: Props) {
  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-5 right-5 z-[100] flex flex-col gap-2">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onRemove={onRemove} />
      ))}
    </div>
  );
}

function ToastItem({ toast, onRemove }: { toast: Toast; onRemove: (id: string) => void }) {
  const icon =
    toast.type === "success" ? (
      <CheckCircle size={16} className="text-emerald-400" />
    ) : toast.type === "error" ? (
      <AlertCircle size={16} className="text-rose-400" />
    ) : (
      <Info size={16} className="text-brand-400" />
    );

  const bgClass =
    toast.type === "success"
      ? "bg-surface-900/95 ring-emerald-500/20"
      : toast.type === "error"
      ? "bg-surface-900/95 ring-rose-500/20"
      : "bg-surface-900/95 ring-brand-500/20";

  return (
    <div
      className={`flex w-[280px] items-start gap-2.5 rounded-xl px-4 py-3 text-sm text-surface-200 shadow-lg backdrop-blur-xl ring-1 ${bgClass} animate-in fade-in slide-in-from-bottom-2`}
    >
      {icon}
      <span className="flex-1 leading-snug">{toast.message}</span>
      <button
        onClick={() => onRemove(toast.id)}
        className="mt-0.5 text-surface-500 hover:text-surface-300"
      >
        <X size={14} />
      </button>
    </div>
  );
}
