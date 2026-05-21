import type { AppView } from "../types";

const NAV: { id: AppView; label: string; description: string }[] = [
  { id: "overview", label: "Overview", description: "Balance & volume" },
  { id: "transactions", label: "Transactions", description: "Ledger explorer" },
  { id: "system", label: "System", description: "Health & pipeline" },
];

interface Props {
  active: AppView;
  onNavigate: (view: AppView) => void;
  merchantId: string;
}

export function Sidebar({ active, onNavigate, merchantId }: Props) {
  return (
    <aside className="glass flex h-full w-64 shrink-0 flex-col border-r border-slate-800/80">
      <div className="border-b border-slate-800/80 px-5 py-5">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-cyan-600 text-sm font-bold text-white shadow-lg shadow-emerald-900/30">
            IX
          </div>
          <div>
            <p className="text-sm font-semibold text-white">IngestX</p>
            <p className="text-[11px] text-slate-500">Ledger Command Center</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 space-y-1 p-3">
        {NAV.map((item) => {
          const isActive = active === item.id;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onNavigate(item.id)}
              className={`w-full rounded-xl px-3 py-3 text-left transition ${
                isActive
                  ? "bg-emerald-500/10 text-emerald-300 ring-1 ring-emerald-500/25"
                  : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
              }`}
            >
              <p className="text-sm font-medium">{item.label}</p>
              <p className="text-xs text-slate-500">{item.description}</p>
            </button>
          );
        })}
      </nav>

      <div className="border-t border-slate-800/80 p-4">
        <p className="text-[10px] font-medium uppercase tracking-wider text-slate-500">
          Active merchant
        </p>
        <p className="mono mt-1 truncate text-sm text-slate-200">{merchantId}</p>
      </div>
    </aside>
  );
}
