import { computeVolumeBuckets } from "../lib/format";
import type { LedgerTransaction } from "../types";

interface Props {
  transactions: LedgerTransaction[];
}

export function VolumeChart({ transactions }: Props) {
  const buckets = computeVolumeBuckets(transactions);
  const max = Math.max(...buckets.map((b) => b.value), 1);

  return (
    <section className="glass rounded-2xl p-5">
      <div className="mb-4 flex items-end justify-between">
        <div>
          <h2 className="text-sm font-semibold text-white">Settlement volume</h2>
          <p className="text-xs text-slate-500">Aggregated buckets from loaded ledger</p>
        </div>
        <span className="text-xs text-slate-500">{transactions.length} txns</span>
      </div>

      <div className="flex h-36 items-end gap-1.5">
        {buckets.map((bucket) => {
          const height = `${Math.max(4, (bucket.value / max) * 100)}%`;
          return (
            <div key={bucket.label} className="group flex flex-1 flex-col items-center gap-1">
              <div className="relative flex h-full w-full items-end">
                <div
                  className="w-full rounded-t-md bg-gradient-to-t from-emerald-600/80 to-cyan-500/50 transition hover:from-emerald-500 hover:to-cyan-400"
                  style={{ height }}
                  title={`${bucket.label}: ${bucket.value.toFixed(2)}`}
                />
              </div>
              <span className="text-[9px] text-slate-600">{bucket.label}</span>
            </div>
          );
        })}
      </div>
    </section>
  );
}
