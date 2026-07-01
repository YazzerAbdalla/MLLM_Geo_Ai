import { cn } from "@/lib/utils";
import { useI18n } from "@/lib/i18n";

interface AccuracyComparisonProps {
  overallAccuracy: number;
  spatialAccuracy: number;
}

export function AccuracyComparison({ overallAccuracy, spatialAccuracy }: AccuracyComparisonProps) {
  const { t } = useI18n();
  const items = [
    { label: t("accuracy"), value: overallAccuracy, color: "bg-primary" },
    { label: t("spatial_accuracy"), value: spatialAccuracy, color: "bg-accent" },
  ];
  return (
    <div className="rounded border border-border bg-secondary/40 p-3 space-y-2.5">
      <h4 className="text-[10px] uppercase tracking-wider font-semibold text-muted-foreground">
        {t("accuracy")} vs {t("spatial_accuracy")}
      </h4>
      <div className="space-y-2">
        {items.map((item) => (
          <div key={item.label} className="space-y-0.5">
            <div className="flex justify-between text-[11px]">
              <span className="text-muted-foreground">{item.label}</span>
              <span className="mono font-semibold">{(item.value * 100).toFixed(1)}%</span>
            </div>
            <div className="h-2 bg-secondary rounded-full overflow-hidden">
              <div
                className={cn("h-full rounded-full transition-all", item.color)}
                style={{ width: `${item.value * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>
      <p className="text-[10px] text-muted-foreground leading-tight">
        {overallAccuracy > spatialAccuracy
          ? t("overall_higher")
          : overallAccuracy < spatialAccuracy
            ? t("spatial_higher")
            : t("accuracy_equal")}
      </p>
    </div>
  );
}
