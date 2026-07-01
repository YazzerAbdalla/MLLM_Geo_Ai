import { useDash } from "@/store/dashboardStore";
import { useI18n } from "@/lib/i18n";
import { CellDetailPanel } from "./CellDetailPanel";
import { EvaluationPanel } from "./EvaluationPanel";
import { cn } from "@/lib/utils";

export function RightPanel() {
  const tab = useDash((s) => s.activeTab);
  const setTab = useDash((s) => s.setActiveTab);
  const cells = useDash((s) => s.cells);
  const selected = useDash((s) => s.selectedCellId);
  const { t } = useI18n();
  if (cells.length === 0 && !selected) return null;
  return (
    <aside className="w-[360px] shrink-0 border-l border-border bg-card flex flex-col">
      <div className="flex border-b border-border">
        <TabBtn active={tab === "detail"} onClick={() => setTab("detail")}>{t("cell_detail")}</TabBtn>
        <TabBtn active={tab === "evaluation"} onClick={() => setTab("evaluation")}>{t("evaluation")}</TabBtn>
      </div>
      <div className="flex-1 overflow-hidden">
        {tab === "detail" ? <CellDetailPanel /> : <EvaluationPanel />}
      </div>
    </aside>
  );
}

function TabBtn({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button onClick={onClick}
      className={cn("flex-1 py-2.5 text-xs font-semibold uppercase tracking-wider transition-colors",
        active ? "text-foreground border-b-2 border-primary" : "text-muted-foreground hover:text-foreground")}>{children}</button>
  );
}
