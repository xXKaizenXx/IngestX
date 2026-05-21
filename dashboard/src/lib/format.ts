import type { LedgerTransaction, TransactionFilters } from "../types";

export function formatCurrency(amount: string | number, currency = "ZAR"): string {
  const value = typeof amount === "string" ? parseFloat(amount) : amount;
  if (Number.isNaN(value)) return `${currency} 0.00`;
  return new Intl.NumberFormat("en-ZA", {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
  }).format(value);
}

export function formatTime(iso: string | null): string {
  if (!iso) return "—";
  return new Intl.DateTimeFormat("en-ZA", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    day: "2-digit",
    month: "short",
  }).format(new Date(iso));
}

export function formatDateTime(iso: string | null): string {
  if (!iso) return "—";
  return new Intl.DateTimeFormat("en-ZA", {
    dateStyle: "medium",
    timeStyle: "medium",
  }).format(new Date(iso));
}

export function truncateId(id: string, length = 12): string {
  if (id.length <= length) return id;
  return `${id.slice(0, length)}…`;
}

export function relativeTime(iso: string | null): string {
  if (!iso) return "Never";
  const diff = Date.now() - new Date(iso).getTime();
  if (diff < 5000) return "Just now";
  if (diff < 60_000) return `${Math.floor(diff / 1000)}s ago`;
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`;
  return formatTime(iso);
}

export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    return false;
  }
}

export function filterTransactions(
  transactions: LedgerTransaction[],
  filters: TransactionFilters,
): LedgerTransaction[] {
  let result = [...transactions];

  if (filters.status !== "all") {
    result = result.filter((t) => t.status === filters.status);
  }

  if (filters.query.trim()) {
    const q = filters.query.trim().toLowerCase();
    result = result.filter(
      (t) =>
        t.transaction_id.toLowerCase().includes(q) ||
        t.event_id.toLowerCase().includes(q) ||
        t.amount.includes(q),
    );
  }

  result.sort((a, b) => {
    switch (filters.sort) {
      case "oldest":
        return new Date(a.settled_at).getTime() - new Date(b.settled_at).getTime();
      case "amount_high":
        return parseFloat(b.amount) - parseFloat(a.amount);
      case "amount_low":
        return parseFloat(a.amount) - parseFloat(b.amount);
      default:
        return new Date(b.settled_at).getTime() - new Date(a.settled_at).getTime();
    }
  });

  return result;
}

export function computeVolumeBuckets(
  transactions: LedgerTransaction[],
  bucketCount = 12,
): { label: string; value: number }[] {
  if (transactions.length === 0) {
    return Array.from({ length: bucketCount }, (_, i) => ({
      label: `${i + 1}`,
      value: 0,
    }));
  }

  const sorted = [...transactions].sort(
    (a, b) => new Date(a.settled_at).getTime() - new Date(b.settled_at).getTime(),
  );
  const chunkSize = Math.max(1, Math.ceil(sorted.length / bucketCount));
  const buckets: { label: string; value: number }[] = [];

  for (let i = 0; i < bucketCount; i++) {
    const chunk = sorted.slice(i * chunkSize, (i + 1) * chunkSize);
    const value = chunk.reduce((sum, t) => sum + parseFloat(t.amount), 0);
    buckets.push({ label: `T${i + 1}`, value });
  }

  return buckets;
}
