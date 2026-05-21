import type { SystemStatus } from "../types";
import { relativeTime } from "../lib/format";

interface Props {
  status: SystemStatus | null;
  connectionLabel: string;
  lastEventAt: string | null;
}

function Pill({
  label,
  value,
  ok,
}: {
  label: string;
  value: string;
  ok?: boolean;
}) {
  return (
    <div className="flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/50 px-3 py-2">
      <span
        className={`h-2 w-2 rounded-full ${ok === false ? "bg-red-400" : ok ? "bg-emerald-400" : "bg-slate-500"}`}
      />
      <div>
        <p className="text-[10px] uppercase tracking-wider text-slate-500">{label}</p>
        <p className="mono text-xs font-medium text-slate-200">{value}</p>
      </div>
    </div>
  );
}

export function StatusStrip({ status, connectionLabel, lastEventAt }: Props) {
  return (
    <div className="grid grid-cols-2 gap-2 xl:grid-cols-6">
      <Pill label="Stream" value={connectionLabel} ok={connectionLabel === "Live"} />
      <Pill label="API" value={status?.api ?? "—"} ok={status?.api === "ok"} />
      <Pill label="Database" value={status?.database ?? "—"} ok={status?.database === "ok"} />
      <Pill label="Redis" value={status?.redis ?? "—"} ok={status?.redis === "ok"} />
      <Pill label="Queue depth" value={String(status?.queue_depth ?? "—")} />
      <Pill label="Last event" value={relativeTime(lastEventAt)} />
    </div>
  );
}
