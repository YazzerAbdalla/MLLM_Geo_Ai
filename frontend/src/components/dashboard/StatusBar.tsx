import { useDash } from "@/store/dashboardStore";
import { classHex } from "@/lib/colors";
import { useI18n } from "@/lib/i18n";

export function StatusBar() {
  const cells = useDash((s) => s.cells);
  const progress = useDash((s) => s.classifyProgress);
  const { t } = useI18n();
  const counts: Record<string, number> = { Residential: 0, Commercial: 0, Industrial: 0 };
  cells.forEach((c) => (counts[c.class] += 1));
  const total = cells.length || 1;
  return (
    <div className="h-9 shrink-0 border-t border-border bg-card flex items-center px-4 gap-4 text-xs">
      <span className="text-muted-foreground">{t("distribution")}:</span>
      <div className="flex-1 max-w-md flex h-3 rounded overflow-hidden border border-border">
        {(["Residential", "Commercial", "Industrial"] as const).map((k) => (
          <div key={k} title={`${k}: ${counts[k]}`} style={{ width: `${(counts[k] / total) * 100}%`, backgroundColor: classHex[k] }} />
        ))}
      </div>
      <div className="flex gap-3 mono">
        {(["Residential", "Commercial", "Industrial"] as const).map((k) => (
          <span key={k} className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-sm" style={{ backgroundColor: classHex[k] }} />
            {k.slice(0, 3)} <span className="text-muted-foreground">{counts[k]}</span>
          </span>
        ))}
      </div>
      <div className="ml-auto mono text-muted-foreground">{Math.round(progress * 100)}% · {cells.length} cells</div>
    </div>
  );
}
