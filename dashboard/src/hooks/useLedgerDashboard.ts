import { useCallback, useEffect, useRef, useState } from "react";
import type {
  BalanceSnapshot,
  BalanceUpdateEvent,
  ConnectionState,
  DashboardConfig,
  LedgerTransaction,
  StreamStats,
  SystemStatus,
  ToastMessage,
} from "../types";
import {
  buildStreamUrl,
  fetchBalance,
  fetchSystemStatus,
  fetchTransactions,
} from "../lib/api";

function makeToast(
  title: string,
  description?: string,
  type: ToastMessage["type"] = "info",
): ToastMessage {
  return { id: crypto.randomUUID(), title, description, type };
}

export function useLedgerDashboard(config: DashboardConfig) {
  const [connection, setConnection] = useState<ConnectionState>("disconnected");
  const [balance, setBalance] = useState<BalanceSnapshot | null>(null);
  const [transactions, setTransactions] = useState<LedgerTransaction[]>([]);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [stats, setStats] = useState<StreamStats>({
    eventsReceived: 0,
    totalVolume: 0,
    lastEventAt: null,
    sessionStartedAt: new Date().toISOString(),
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  const [paused, setPaused] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<number | null>(null);
  const reconnectAttempt = useRef(0);
  const pausedRef = useRef(false);

  const pushToast = useCallback((toast: ToastMessage) => {
    setToasts((prev) => [...prev.slice(-4), toast]);
    window.setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== toast.id));
    }, 4500);
  }, []);

  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const bootstrap = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [bal, txns, status] = await Promise.all([
        fetchBalance(config),
        fetchTransactions(config),
        fetchSystemStatus(config),
      ]);
      setBalance(bal);
      setTransactions(txns);
      setSystemStatus(status);
      setStats((prev) => ({
        ...prev,
        totalVolume: txns.reduce(
          (sum: number, t: LedgerTransaction) => sum + parseFloat(t.amount),
          0,
        ),
      }));
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to load ledger";
      setError(message);
      pushToast(makeToast("Load failed", message, "error"));
    } finally {
      setLoading(false);
    }
  }, [config, pushToast]);

  const refreshSystemStatus = useCallback(async () => {
    try {
      const status = await fetchSystemStatus(config);
      setSystemStatus(status);
    } catch {
      /* silent background poll */
    }
  }, [config]);

  const handleEvent = useCallback(
    (event: BalanceUpdateEvent) => {
      if (pausedRef.current) return;

      setBalance({
        merchant_id: event.merchant_id,
        balance: String(event.balance),
        currency: event.currency,
        updated_at: event.timestamp,
      });

      const txn: LedgerTransaction = {
        transaction_id: event.transaction.transaction_id,
        event_id: event.transaction.event_id,
        amount: String(event.transaction.amount),
        currency: event.currency,
        status: "settled",
        running_balance: String(event.balance),
        settled_at: event.timestamp,
      };

      setTransactions((prev) => {
        if (prev.some((t) => t.transaction_id === txn.transaction_id)) return prev;
        return [txn, ...prev].slice(0, 200);
      });

      setStats((prev) => ({
        ...prev,
        eventsReceived: prev.eventsReceived + 1,
        totalVolume: prev.totalVolume + parseFloat(String(event.transaction.amount)),
        lastEventAt: event.timestamp,
      }));

      pushToast(
        makeToast(
          "Settlement received",
          `+${event.transaction.amount} ${event.currency} · ${event.transaction.transaction_id.slice(0, 14)}…`,
          "success",
        ),
      );
    },
    [pushToast],
  );

  const disconnect = useCallback(() => {
    if (reconnectTimer.current) {
      window.clearTimeout(reconnectTimer.current);
      reconnectTimer.current = null;
    }
    wsRef.current?.close();
    wsRef.current = null;
  }, []);

  const connect = useCallback(() => {
    if (pausedRef.current) {
      setConnection("paused");
      return;
    }
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    setConnection("connecting");
    const ws = new WebSocket(buildStreamUrl(config));
    wsRef.current = ws;

    ws.onopen = () => {
      setConnection("connected");
      reconnectAttempt.current = 0;
    };

    ws.onmessage = (msg) => {
      try {
        const data = JSON.parse(msg.data) as BalanceUpdateEvent;
        if (data.type === "balance_update") handleEvent(data);
      } catch {
        /* ignore */
      }
    };

    ws.onerror = () => setConnection("error");

    ws.onclose = () => {
      wsRef.current = null;
      if (pausedRef.current) {
        setConnection("paused");
        return;
      }
      setConnection("disconnected");
      const delay = Math.min(1000 * 2 ** reconnectAttempt.current, 30_000);
      reconnectAttempt.current += 1;
      reconnectTimer.current = window.setTimeout(connect, delay);
    };
  }, [config, handleEvent]);

  const reconnect = useCallback(() => {
    disconnect();
    reconnectAttempt.current = 0;
    connect();
  }, [connect, disconnect]);

  const togglePause = useCallback(() => {
    setPaused((prev) => {
      const next = !prev;
      pausedRef.current = next;
      if (next) {
        disconnect();
        setConnection("paused");
      } else {
        connect();
      }
      return next;
    });
  }, [connect, disconnect]);

  useEffect(() => {
    bootstrap();
  }, [bootstrap]);

  useEffect(() => {
    connect();
    return disconnect;
  }, [connect, disconnect]);

  useEffect(() => {
    const interval = window.setInterval(refreshSystemStatus, 10_000);
    return () => window.clearInterval(interval);
  }, [refreshSystemStatus]);

  return {
    connection,
    balance,
    transactions,
    systemStatus,
    stats,
    loading,
    error,
    toasts,
    paused,
    refresh: bootstrap,
    refreshSystemStatus,
    reconnect,
    togglePause,
    dismissToast,
  };
}
