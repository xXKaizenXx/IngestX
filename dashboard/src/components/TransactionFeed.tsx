import { useMemo, useState } from "react";
import { exportTransactionsCsv } from "../lib/api";
import {
  copyToClipboard,
  filterTransactions,
  formatCurrency,
  formatTime,
  truncateId,
} from "../lib/format";
import type { DashboardConfig, LedgerTransaction, TransactionFilters } from "../types";

interface Props {
  transactions: LedgerTransaction[];
  loading: boolean;
  config: DashboardConfig;
  filters: TransactionFilters;
  onFiltersChange: (filters: TransactionFilters) => void;
}

export function TransactionFeed({
  transactions,
  loading,
  config,
  filters,
  onFiltersChange,
}: Props) {
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const filtered = useMemo(
    () => filterTransactions(transactions, filters),
    [transactions, filters],
  );

  const handleCopy = async (id: string) => {
    const ok = await copyToClipboard(id);
    if (ok) {
      setCopiedId(id);
      window.setTimeout(() => setCopiedId(null), 1500);
    }
  };

  return (
    <section className="glass overflow-hidden rounded-2xl">
      <div className="border-b border-slate-800/80 p-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h2 className="text-sm font-semibold text-white">Transaction ledger</h2>
            <p className="text-xs text-slate-500">
              {filtered.length} of {transactions.length} entries · live + historical
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => exportTransactionsCsv(filtered, config.merchantId)}
              disabled={filtered.length === 0}
              className="rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-2 text-xs font-medium text-slate-200 disabled:opacity-40"
            >
              Export CSV
            </button>
          </div>
        </div>

        <div className="mt-4 grid gap-2 md:grid-cols-3">
          <input
            type="search"
            placeholder="Search txn / event / amount…"
            value={filters.query}
            onChange={(e) => onFiltersChange({ ...filters, query: e.target.value })}
            className="rounded-lg border border-slate-700 bg-slate-900/80 px-3 py-2 text-sm text-slate-200 placeholder:text-slate-600"
          />
          <select
            value={filters.status}
            onChange={(e) =>
              onFiltersChange({
                ...filters,
                status: e.target.value as TransactionFilters["status"],
              })
            }
            className="rounded-lg border border-slate-700 bg-slate-900/80 px-3 py-2 text-sm text-slate-200"
          >
            <option value="all">All statuses</option>
            <option value="settled">Settled</option>
            <option value="failed">Failed</option>
            <option value="duplicate">Duplicate</option>
          </select>
          <select
            value={filters.sort}
            onChange={(e) =>
              onFiltersChange({
                ...filters,
                sort: e.target.value as TransactionFilters["sort"],
              })
            }
            className="rounded-lg border border-slate-700 bg-slate-900/80 px-3 py-2 text-sm text-slate-200"
          >
            <option value="newest">Newest first</option>
            <option value="oldest">Oldest first</option>
            <option value="amount_high">Amount high → low</option>
            <option value="amount_low">Amount low → high</option>
          </select>
        </div>
      </div>

      <div className="max-h-[520px] overflow-auto">
        {loading && transactions.length === 0 ? (
          <div className="space-y-2 p-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-12 skeleton rounded-lg" />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <div className="px-6 py-16 text-center">
            <p className="text-sm text-slate-400">No matching transactions</p>
            <p className="mt-1 text-xs text-slate-600">
              Adjust filters or ingest a webhook to populate the ledger.
            </p>
          </div>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="sticky top-0 z-10 bg-slate-950/95 text-[10px] uppercase tracking-wider text-slate-500">
              <tr>
                <th className="px-4 py-3 font-semibold">Settled</th>
                <th className="px-4 py-3 font-semibold">Transaction ID</th>
                <th className="px-4 py-3 font-semibold">Event ID</th>
                <th className="px-4 py-3 font-semibold">Amount</th>
                <th className="px-4 py-3 font-semibold">Balance</th>
                <th className="px-4 py-3 font-semibold">Status</th>
                <th className="px-4 py-3 font-semibold" />
              </tr>
            </thead>
            <tbody>
              {filtered.map((txn, idx) => (
                <tr
                  key={txn.transaction_id}
                  className={`border-t border-slate-800/70 hover:bg-slate-800/30 ${
                    idx === 0 ? "animate-slide-in bg-emerald-500/5" : ""
                  }`}
                >
                  <td className="mono px-4 py-3 whitespace-nowrap text-slate-400">
                    {formatTime(txn.settled_at)}
                  </td>
                  <td className="mono px-4 py-3 text-slate-200" title={txn.transaction_id}>
                    {truncateId(txn.transaction_id, 18)}
                  </td>
                  <td className="mono px-4 py-3 text-slate-400" title={txn.event_id}>
                    {truncateId(txn.event_id, 14)}
                  </td>
                  <td className="mono px-4 py-3 font-medium text-emerald-400">
                    +{formatCurrency(txn.amount, txn.currency)}
                  </td>
                  <td className="mono px-4 py-3 text-slate-300">
                    {formatCurrency(txn.running_balance, txn.currency)}
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={txn.status} />
                  </td>
                  <td className="px-4 py-3">
                    <button
                      type="button"
                      onClick={() => handleCopy(txn.transaction_id)}
                      className="rounded-md border border-slate-700 px-2 py-1 text-[10px] text-slate-400 hover:text-slate-200"
                    >
                      {copiedId === txn.transaction_id ? "Copied" : "Copy"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </section>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    settled: "bg-emerald-500/10 text-emerald-400",
    failed: "bg-red-500/10 text-red-400",
    duplicate: "bg-amber-500/10 text-amber-400",
  };
  return (
    <span
      className={`inline-flex rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ${
        styles[status] ?? "bg-slate-700 text-slate-300"
      }`}
    >
      {status}
    </span>
  );
}
