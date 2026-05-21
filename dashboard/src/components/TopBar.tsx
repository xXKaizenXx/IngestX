import type { ConnectionState } from "../types";
import { ConnectionBadge } from "./ConnectionBadge";

interface Props {
  title: string;
  subtitle: string;
  connection: ConnectionState;
  paused: boolean;
  onRefresh: () => void;
  onReconnect: () => void;
  onTogglePause: () => void;
  onOpenSettings: () => void;
}

export function TopBar({
  title,
  subtitle,
  connection,
  paused,
  onRefresh,
  onReconnect,
  onTogglePause,
  onOpenSettings,
}: Props) {
  return (
    <header className="glass sticky top-0 z-20 border-b border-slate-800/80 px-6 py-4">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="text-lg font-semibold text-white">{title}</h1>
          <p className="text-sm text-slate-500">{subtitle}</p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <ConnectionBadge state={connection} />
          {paused && (
            <span className="rounded-full bg-amber-500/10 px-2.5 py-1 text-xs font-medium text-amber-400">
              Stream paused
            </span>
          )}
          <button
            type="button"
            onClick={onTogglePause}
            className="rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-2 text-xs font-medium text-slate-200 hover:border-slate-600"
          >
            {paused ? "Resume" : "Pause"}
          </button>
          <button
            type="button"
            onClick={onReconnect}
            className="rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-2 text-xs font-medium text-slate-200 hover:border-slate-600"
          >
            Reconnect
          </button>
          <button
            type="button"
            onClick={onRefresh}
            className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-xs font-medium text-emerald-300 hover:bg-emerald-500/15"
          >
            Sync ledger
          </button>
          <button
            type="button"
            onClick={onOpenSettings}
            className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-xs font-medium text-slate-300 hover:border-slate-600"
          >
            Settings
          </button>
        </div>
      </div>
    </header>
  );
}
