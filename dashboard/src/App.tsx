import { useState } from "react";
import { loadConfig, saveConfig } from "./lib/api";
import { useLedgerDashboard } from "./hooks/useLedgerDashboard";
import { BalanceCard } from "./components/BalanceCard";
import { SettingsModal } from "./components/SettingsModal";
import { Sidebar } from "./components/Sidebar";
import { StatsGrid } from "./components/StatsGrid";
import { StatusStrip } from "./components/StatusStrip";
import { SystemHealthPanel } from "./components/SystemHealthPanel";
import { ToastContainer } from "./components/ToastContainer";
import { TopBar } from "./components/TopBar";
import { TransactionFeed } from "./components/TransactionFeed";
import { VolumeChart } from "./components/VolumeChart";
import type { AppView, DashboardConfig, TransactionFilters } from "./types";
import { DEFAULT_FILTERS } from "./types";

const VIEW_META: Record<AppView, { title: string; subtitle: string }> = {
  overview: {
    title: "Overview",
    subtitle: "Real-time balance, volume trends, and pipeline signals",
  },
  transactions: {
    title: "Transactions",
    subtitle: "Search, filter, sort, and export the merchant ledger",
  },
  system: {
    title: "System health",
    subtitle: "Queue depth, outbox backlog, and infrastructure status",
  },
};

export default function App() {
  const [config, setConfig] = useState<DashboardConfig>(() => loadConfig());
  const [view, setView] = useState<AppView>("overview");
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [filters, setFilters] = useState<TransactionFilters>(DEFAULT_FILTERS);

  const {
    connection,
    balance,
    transactions,
    systemStatus,
    stats,
    loading,
    error,
    toasts,
    paused,
    refresh,
    reconnect,
    togglePause,
    dismissToast,
  } = useLedgerDashboard(config);

  const handleSaveSettings = (next: DashboardConfig) => {
    saveConfig(next);
    setConfig(next);
    setSettingsOpen(false);
    setFilters(DEFAULT_FILTERS);
  };

  const connectionLabel =
    connection === "connected" ? "Live" : connection === "paused" ? "Paused" : connection;

  const meta = VIEW_META[view];

  return (
    <div className="flex min-h-screen">
      <Sidebar active={view} onNavigate={setView} merchantId={config.merchantId} />

      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar
          title={meta.title}
          subtitle={meta.subtitle}
          connection={connection}
          paused={paused}
          onRefresh={refresh}
          onReconnect={reconnect}
          onTogglePause={togglePause}
          onOpenSettings={() => setSettingsOpen(true)}
        />

        <div className="flex-1 space-y-5 p-6">
          {error && (
            <div className="rounded-xl border border-red-500/30 bg-red-950/40 px-4 py-3 text-sm text-red-200">
              {error}
            </div>
          )}

          <StatusStrip
            status={systemStatus}
            connectionLabel={connectionLabel}
            lastEventAt={stats.lastEventAt}
          />

          {view === "overview" && (
            <div className="grid gap-5 xl:grid-cols-3">
              <BalanceCard balance={balance} loading={loading} />
              <div className="xl:col-span-2">
                <StatsGrid
                  stats={stats}
                  transactionCount={transactions.length}
                  systemStatus={systemStatus}
                />
              </div>
              <div className="xl:col-span-2">
                <VolumeChart transactions={transactions} />
              </div>
              <div className="xl:col-span-1">
                <SystemHealthPanel status={systemStatus} loading={loading} />
              </div>
            </div>
          )}

          {view === "transactions" && (
            <TransactionFeed
              transactions={transactions}
              loading={loading}
              config={config}
              filters={filters}
              onFiltersChange={setFilters}
            />
          )}

          {view === "system" && (
            <div className="grid gap-5 lg:grid-cols-2">
              <SystemHealthPanel status={systemStatus} loading={loading} />
              <section className="glass rounded-2xl p-6">
                <h2 className="text-sm font-semibold text-white">Architecture map</h2>
                <pre className="mono mt-4 overflow-x-auto rounded-xl bg-slate-950/80 p-4 text-[11px] leading-relaxed text-slate-400">
{`Webhooks → FastAPI (202) → Redis Queue
                ↓
           RQ Workers → Idempotency (Redis)
                ↓
         PostgreSQL Ledger + Outbox
                ↓
      Redis Pub/Sub → WebSocket → Dashboard`}
                </pre>
                <p className="mt-4 text-xs text-slate-500">
                  Queue: <span className="text-slate-300">{systemStatus?.queue_name ?? "—"}</span>
                  {" · "}
                  Depth: <span className="text-slate-300">{systemStatus?.queue_depth ?? 0}</span>
                </p>
              </section>
            </div>
          )}
        </div>
      </div>

      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
      <SettingsModal
        open={settingsOpen}
        config={config}
        onClose={() => setSettingsOpen(false)}
        onSave={handleSaveSettings}
      />
    </div>
  );
}
