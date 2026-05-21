import { useEffect, useState } from "react";
import type { DashboardConfig } from "../types";

interface Props {
  open: boolean;
  config: DashboardConfig;
  onClose: () => void;
  onSave: (config: DashboardConfig) => void;
}

export function SettingsModal({ open, config, onClose, onSave }: Props) {
  const [draft, setDraft] = useState(config);

  useEffect(() => {
    if (open) setDraft(config);
  }, [open, config]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <button
        type="button"
        aria-label="Close settings"
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />
      <div className="glass relative w-full max-w-lg rounded-2xl p-6 shadow-2xl">
        <h2 className="text-lg font-semibold text-white">Connection settings</h2>
        <p className="mt-1 text-sm text-slate-500">
          Saved to browser local storage. Reloads stream on save.
        </p>

        <div className="mt-5 space-y-4">
          <Field
            label="Merchant ID"
            value={draft.merchantId}
            onChange={(v) => setDraft({ ...draft, merchantId: v })}
          />
          <Field
            label="Stream token"
            value={draft.streamToken}
            onChange={(v) => setDraft({ ...draft, streamToken: v })}
            type="password"
          />
          <Field
            label="API URL (optional)"
            value={draft.apiUrl}
            onChange={(v) => setDraft({ ...draft, apiUrl: v })}
            placeholder="Empty = same origin / proxy"
          />
          <Field
            label="WebSocket URL (optional)"
            value={draft.wsUrl}
            onChange={(v) => setDraft({ ...draft, wsUrl: v })}
            placeholder="Empty = same origin / proxy"
          />
        </div>

        <div className="mt-6 flex justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-slate-700 px-4 py-2 text-sm text-slate-300"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={() => onSave(draft)}
            className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500"
          >
            Save & reconnect
          </button>
        </div>
      </div>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  placeholder,
  type = "text",
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  type?: string;
}) {
  return (
    <label className="block">
      <span className="text-xs font-medium text-slate-400">{label}</span>
      <input
        type={type}
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900/80 px-3 py-2 text-sm text-slate-100"
      />
    </label>
  );
}
