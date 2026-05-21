export interface LedgerTransaction {
  transaction_id: string;
  event_id: string;
  amount: string;
  currency: string;
  status: string;
  running_balance: string;
  settled_at: string;
}

export interface BalanceSnapshot {
  merchant_id: string;
  balance: string;
  currency: string;
  updated_at: string | null;
}

export interface BalanceUpdateEvent {
  type: "balance_update";
  merchant_id: string;
  balance: string;
  currency: string;
  transaction: {
    transaction_id: string;
    amount: string;
    event_id: string;
  };
  timestamp: string;
}

export interface SystemStatus {
  api: string;
  database: string;
  redis: string;
  queue_name: string;
  queue_depth: number;
  outbox_pending: number;
  ledger_entries: number;
  active_merchants: number;
}

export type ConnectionState = "connecting" | "connected" | "disconnected" | "error" | "paused";

export type AppView = "overview" | "transactions" | "system";

export interface DashboardConfig {
  apiUrl: string;
  wsUrl: string;
  streamToken: string;
  merchantId: string;
}

export interface StreamStats {
  eventsReceived: number;
  totalVolume: number;
  lastEventAt: string | null;
  sessionStartedAt: string;
}

export interface ToastMessage {
  id: string;
  title: string;
  description?: string;
  type: "success" | "info" | "error";
}

export interface TransactionFilters {
  query: string;
  status: "all" | "settled" | "failed" | "duplicate";
  sort: "newest" | "oldest" | "amount_high" | "amount_low";
}

export const DEFAULT_FILTERS: TransactionFilters = {
  query: "",
  status: "all",
  sort: "newest",
};

export const CONFIG_STORAGE_KEY = "ingestx.dashboard.config";
