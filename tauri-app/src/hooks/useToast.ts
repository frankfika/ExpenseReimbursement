import { useState, useCallback, useRef } from "react";
import type { Toast } from "../types/toast";

let toastId = 0;

export function useToast() {
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

  return { toasts, success, error, info, remove };
}
