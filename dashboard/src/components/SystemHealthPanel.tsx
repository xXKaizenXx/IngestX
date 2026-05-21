import type { SystemStatus } from "../types";

interface Props {
  status: SystemStatus | null;
  loading: boolean;
}

function Row({
  label,
  value,
  description,
  ok,
}: {
  label: string;
  value: string | number;
  description?: string;
  ok?: boolean;
}) {
  return (
    <div className="flex items-center justify-between border-b border-slate-800/70 py-4 last:border-0">
      <div>
        <p className="text-sm font-medium text-slate-200">{label}</p>
        {description && <p className="text-xs text-slate-500">{description}</p>}
      </div>
      <div className="flex items-center gap-2">
        {ok !== undefined && (
          <span className={`h-2 w-2 rounded-full ${ok ? "bg-emerald-400" : "bg-red-400"}`} />
        )}
        <span className="mono text-sm text-slate-100">{value}</span>
      </div>
    </div>
  );
}

export function SystemHealthPanel({ status, loading }: Props) {
  if (loading && !status) {
    return (
      <section className="glass rounded-2xl p-6">
        <div className="h-8 w-48 skeleton rounded-lg" />
        <div className="mt-6 space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-12 skeleton rounded-lg" />
          ))}
        </div>
      </section>
    );
  }

  return (
    <section className="glass rounded-2xl p-6">
      <h2 className="text-sm font-semibold text-white">Pipeline health</h2>
      <p className="text-xs text-slate-500">Auto-refreshes every 10 seconds</p>

      <div className="mt-4">
        <Row label="API gateway" value={status?.api ?? "unknown"} ok={status?.api === "ok"} />
        <Row
          label="PostgreSQL"
          value={status?.database ?? "unknown"}
          description="Ledger & outbox persistence"
          ok={status?.database === "ok"}
        />
        <Row
          label="Redis"
          value={status?.redis ?? "unknown"}
          description="Queue, idempotency, pub/sub"
          ok={status?.redis === "ok"}
        />
        <Row
          label="RQ queue"
          value={`${status?.queue_name ?? "—"} (${status?.queue_depth ?? 0})`}
          description="Pending webhook jobs"
        />
        <Row
          label="Outbox pending"
          value={status?.outbox_pending ?? 0}
          description="Failed settlements awaiting retry"
          ok={(status?.outbox_pending ?? 0) === 0}
        />
        <Row label="Ledger entries" value={status?.ledger_entries ?? 0} />
        <Row label="Active merchants" value={status?.active_merchants ?? 0} />
      </div>
    </section>
  );
}
