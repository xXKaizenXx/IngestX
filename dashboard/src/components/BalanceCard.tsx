import { formatCurrency, formatDateTime } from "../lib/format";
import type { BalanceSnapshot } from "../types";

interface Props {
  balance: BalanceSnapshot | null;
  loading: boolean;
  recentDelta?: string;
}

export function BalanceCard({ balance, loading, recentDelta }: Props) {
  return (
    <section className="glass relative overflow-hidden rounded-2xl p-6">
      <div className="absolute -right-10 -top-10 h-36 w-36 rounded-full bg-emerald-500/10 blur-3xl" />
      <div className="relative">
        <div className="flex items-start justify-between">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Available balance
          </p>
          {recentDelta && (
            <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-xs font-medium text-emerald-400">
              {recentDelta}
            </span>
          )}
        </div>

        {loading && !balance ? (
          <div className="mt-4 h-12 w-56 skeleton rounded-lg" />
        ) : (
          <p className="mono mt-3 text-4xl font-semibold tracking-tight text-white">
            {formatCurrency(balance?.balance ?? "0", balance?.currency ?? "ZAR")}
          </p>
        )}

        <div className="mt-5 grid grid-cols-2 gap-3 border-t border-slate-800/80 pt-4">
          <div>
            <p className="text-[10px] uppercase tracking-wider text-slate-500">Merchant</p>
            <p className="mono mt-1 text-sm text-slate-200">{balance?.merchant_id ?? "—"}</p>
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-wider text-slate-500">Last sync</p>
            <p className="mono mt-1 text-sm text-slate-200">
              {formatDateTime(balance?.updated_at ?? null)}
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
