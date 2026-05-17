import { createContext, useContext, useCallback, useState, useRef, type ReactNode } from "react";
import type { Toast } from "../types/toast";

interface ToastContextValue {
  success: (message: string, duration?: number) => string;
  error: (message: string, duration?: number) => string;
  info: (message: string, duration?: number) => string;
  remove: (id: string) => void;
  toasts: Toast[];
}

const ToastContext = createContext<ToastContextValue | null>(null);

let toastId = 0;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const timersRef = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());

  const remove = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
    const timer = timersRef.current.get(id);
    if (timer) {
      clearTimeout(timer);
      timersRef.current.delete(id);
    }
  }, []);

  const add = useCallback((toast: Omit<Toast, "id">) => {
    const id = `toast-${++toastId}`;
    const newToast: Toast = { ...toast, id };
    setToasts((prev) => [...prev, newToast]);

    const duration = toast.duration ?? 4000;
    const timer = setTimeout(() => {
      remove(id);
    }, duration);
    timersRef.current.set(id, timer);

    return id;
  }, [remove]);

  const success = useCallback((message: string, duration?: number) => {
    return add({ message, type: "success", duration });
  }, [add]);

  const error = useCallback((message: string, duration?: number) => {
    return add({ message, type: "error", duration });
  }, [add]);

  const info = useCallback((message: string, duration?: number) => {
    return add({ message, type: "info", duration });
  }, [add]);

  return (
    <ToastContext.Provider value={{ success, error, info, remove, toasts }}>
      {children}
    </ToastContext.Provider>
  );
}

export function useToastContext(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    throw new Error("useToastContext must be used within ToastProvider");
  }
  return ctx;
}
