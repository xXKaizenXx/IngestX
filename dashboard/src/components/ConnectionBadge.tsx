import type { ConnectionState } from "../types";

const LABELS: Record<ConnectionState, string> = {
  connected: "Live",
  connecting: "Connecting",
  disconnected: "Offline",
  error: "Error",
  paused: "Paused",
};

const COLORS: Record<ConnectionState, string> = {
  connected: "bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)]",
  connecting: "bg-amber-400 animate-pulse-dot",
  disconnected: "bg-slate-500",
  error: "bg-red-400",
  paused: "bg-amber-500",
};

interface Props {
  state: ConnectionState;
}

export function ConnectionBadge({ state }: Props) {
  return (
    <div className="inline-flex items-center gap-2 rounded-full border border-slate-700/80 bg-slate-900/80 px-3 py-1.5 text-xs font-medium text-slate-300">
      <span className={`h-2 w-2 rounded-full ${COLORS[state]}`} />
      {LABELS[state]}
    </div>
  );
}
