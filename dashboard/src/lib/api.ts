import type { DashboardConfig } from "../types";
import { CONFIG_STORAGE_KEY } from "../types";

function authHeaders(token: string): HeadersInit {
  return { "X-Stream-Token": token };
}

function apiBase(config: DashboardConfig): string {
  return config.apiUrl.replace(/\/$/, "");
}

export async function fetchBalance(config: DashboardConfig) {
  const res = await fetch(
    `${apiBase(config)}/api/v1/ledger/${config.merchantId}/balance`,
    { headers: authHeaders(config.streamToken) },
  );
  if (!res.ok) throw new Error(`Balance fetch failed (${res.status})`);
  return res.json();
}

export async function fetchTransactions(config: DashboardConfig, limit = 100) {
  const res = await fetch(
    `${apiBase(config)}/api/v1/ledger/${config.merchantId}/transactions?limit=${limit}`,
    { headers: authHeaders(config.streamToken) },
  );
  if (!res.ok) throw new Error(`Transactions fetch failed (${res.status})`);
  const data = await res.json();
  return data.items ?? [];
}

export async function fetchSystemStatus(config: DashboardConfig) {
  const res = await fetch(`${apiBase(config)}/api/v1/system/status`, {
    headers: authHeaders(config.streamToken),
  });
  if (!res.ok) throw new Error(`System status failed (${res.status})`);
  return res.json();
}

export async function fetchHealth(config: DashboardConfig): Promise<boolean> {
  try {
    const res = await fetch(`${apiBase(config)}/health`);
    return res.ok;
  } catch {
    return false;
  }
}

export function loadConfig(): DashboardConfig {
  const envDefaults: DashboardConfig = {
    apiUrl: import.meta.env.VITE_API_URL ?? "",
    wsUrl: import.meta.env.VITE_WS_URL ?? "",
    streamToken: import.meta.env.VITE_STREAM_TOKEN ?? "dev-stream-token-change-me",
    merchantId: import.meta.env.VITE_MERCHANT_ID ?? "merchant_demo",
  };

  try {
    const stored = localStorage.getItem(CONFIG_STORAGE_KEY);
    if (stored) return { ...envDefaults, ...JSON.parse(stored) };
  } catch {
    /* ignore */
  }
  return envDefaults;
}

export function saveConfig(config: DashboardConfig): void {
  localStorage.setItem(
    CONFIG_STORAGE_KEY,
    JSON.stringify({
      merchantId: config.merchantId,
      streamToken: config.streamToken,
      apiUrl: config.apiUrl,
      wsUrl: config.wsUrl,
    }),
  );
}

export function buildStreamUrl(config: DashboardConfig): string {
  const base = config.wsUrl || window.location.origin.replace(/^http/, "ws");
  const params = new URLSearchParams({
    token: config.streamToken,
    merchant_id: config.merchantId,
  });
  return `${base.replace(/\/$/, "")}/api/v1/stream?${params}`;
}

export function exportTransactionsCsv(
  transactions: Array<{
    settled_at: string;
    transaction_id: string;
    event_id: string;
    amount: string;
    currency: string;
    running_balance: string;
    status: string;
  }>,
  merchantId: string,
): void {
  const header = "settled_at,transaction_id,event_id,amount,currency,running_balance,status";
  const rows = transactions.map((t) =>
    [
      t.settled_at,
      t.transaction_id,
      t.event_id,
      t.amount,
      t.currency,
      t.running_balance,
      t.status,
    ].join(","),
  );
  const blob = new Blob([[header, ...rows].join("\n")], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `ingestx-${merchantId}-${Date.now()}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}
