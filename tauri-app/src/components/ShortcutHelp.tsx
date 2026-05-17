import { useEffect } from "react";
import { X, Command, CornerDownLeft } from "lucide-react";

interface Props {
  open: boolean;
  onClose: () => void;
}

const SHORTCUTS = [
  { keys: ["Ctrl/⌘", "1"], action: "切换到 Providers" },
  { keys: ["Ctrl/⌘", "2"], action: "切换到识别" },
  { keys: ["Ctrl/⌘", "3"], action: "切换到外观" },
  { keys: ["?"], action: "显示快捷键帮助" },
];

export function ShortcutHelp({ open, onClose }: Props) {
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="card w-full max-w-sm overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-white/[0.06] px-5 py-4">
          <h3 className="text-sm font-semibold text-surface-100">键盘快捷键</h3>
          <button
            className="rounded-lg p-1 text-surface-500 hover:bg-surface-800 hover:text-surface-300"
            onClick={onClose}
          >
            <X size={16} />
          </button>
        </div>
        <div className="px-5 py-4">
          <div className="space-y-2.5">
            {SHORTCUTS.map((s, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between text-sm"
              >
                <span className="text-surface-400">{s.action}</span>
                <span className="flex items-center gap-1">
                  {s.keys.map((k, i) => (
                    <span key={i} className="inline-flex items-center gap-0.5">
                      {k === "Ctrl/⌘" ? (
                        <kbd className="flex items-center gap-0.5 rounded-md bg-surface-800 px-1.5 py-0.5 text-[11px] font-medium text-surface-300 ring-1 ring-surface-700">
                          <Command size={10} />
                          Ctrl
                        </kbd>
                      ) : k === "CornerDownLeft" ? (
                        <kbd className="flex items-center rounded-md bg-surface-800 px-1.5 py-0.5 text-[11px] font-medium text-surface-300 ring-1 ring-surface-700">
                          <CornerDownLeft size={10} />
                        </kbd>
                      ) : (
                        <kbd className="rounded-md bg-surface-800 px-1.5 py-0.5 text-[11px] font-medium text-surface-300 ring-1 ring-surface-700">
                          {k}
                        </kbd>
                      )}
                    </span>
                  ))}
                </span>
              </div>
            ))}
          </div>
        </div>
        <div className="border-t border-white/[0.06] px-5 py-3 text-[11px] text-surface-600">
          按 <kbd className="rounded bg-surface-800 px-1 py-0.5 text-surface-500 ring-1 ring-surface-700">Esc</kbd> 或点击空白处关闭
        </div>
      </div>
    </div>
  );
}
