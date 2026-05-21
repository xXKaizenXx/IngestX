import { formatCurrency, relativeTime } from "../lib/format";
import type { StreamStats, SystemStatus } from "../types";

interface Props {
  stats: StreamStats;
  transactionCount: number;
  systemStatus: SystemStatus | null;
}

export function StatsGrid({ stats, transactionCount, systemStatus }: Props) {
  const cards = [
    {
      label: "Stream events",
      value: stats.eventsReceived.toLocaleString(),
      sub: "Since page load",
    },
    {
      label: "Session volume",
      value: formatCurrency(stats.totalVolume),
      sub: "Settled in stream",
    },
    {
      label: "Ledger rows",
      value: (systemStatus?.ledger_entries ?? transactionCount).toLocaleString(),
      sub: "PostgreSQL entries",
    },
    {
      label: "Outbox pending",
      value: String(systemStatus?.outbox_pending ?? 0),
      sub: "Awaiting retry",
      alert: (systemStatus?.outbox_pending ?? 0) > 0,
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-3">
      {cards.map((card) => (
        <div
          key={card.label}
          className={`rounded-xl border p-4 ${
            card.alert
              ? "border-amber-500/30 bg-amber-500/5"
              : "border-slate-800 bg-slate-900/40"
          }`}
        >
          <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
            {card.label}
          </p>
          <p className="mono mt-2 text-xl font-semibold text-slate-100">{card.value}</p>
          <p className="mt-1 text-xs text-slate-600">{card.sub}</p>
        </div>
      ))}
      <div className="col-span-2 rounded-xl border border-slate-800 bg-slate-900/40 p-4">
        <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
          Session uptime
        </p>
        <p className="mt-2 text-sm text-slate-300">
          Started {relativeTime(stats.sessionStartedAt)} · Last event{" "}
          {relativeTime(stats.lastEventAt)}
        </p>
      </div>
    </div>
  );
}
