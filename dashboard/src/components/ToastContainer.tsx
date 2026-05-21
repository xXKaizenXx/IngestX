import type { ToastMessage } from "../types";

interface Props {
  toasts: ToastMessage[];
  onDismiss: (id: string) => void;
}

const styles: Record<ToastMessage["type"], string> = {
  success: "border-emerald-500/30 bg-emerald-950/90",
  info: "border-cyan-500/30 bg-slate-900/95",
  error: "border-red-500/30 bg-red-950/90",
};

export function ToastContainer({ toasts, onDismiss }: Props) {
  return (
    <div className="pointer-events-none fixed bottom-4 right-4 z-50 flex w-full max-w-sm flex-col gap-2">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`animate-toast-in pointer-events-auto rounded-xl border p-4 shadow-xl ${styles[toast.type]}`}
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold text-white">{toast.title}</p>
              {toast.description && (
                <p className="mono mt-1 text-xs text-slate-400">{toast.description}</p>
              )}
            </div>
            <button
              type="button"
              onClick={() => onDismiss(toast.id)}
              className="text-slate-500 hover:text-slate-300"
            >
              ×
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
