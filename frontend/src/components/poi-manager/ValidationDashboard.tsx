import { useState } from "react";
import { CheckCircle2, AlertTriangle, XCircle, Building2, ChevronDown, ChevronUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";

interface PoiValidationError {
  row: number;
  message: string;
}

interface ValidationDashboardProps {
  validation: {
    valid: boolean;
    total_rows: number;
    errors: PoiValidationError[];
    warnings: PoiValidationError[];
  } | null;
  t: (key: string) => string;
}

function StatCard({
  icon,
  label,
  count,
  pct,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  count: number;
  pct?: string;
  color: string;
}) {
  return (
    <div className={cn("rounded-lg border px-3 py-2.5 space-y-1 flex-1 min-w-[120px]", color)}>
      <div className="flex items-center gap-1.5 text-xs text-primary">
        {icon}
        <span className="font-medium">{label}</span>
      </div>
      <div className="flex items-baseline gap-1.5">
        <span className="text-lg font-bold" style={{ color: "#10121a" }}>{count.toLocaleString()}</span>
        {pct && <span className="text-xs" style={{ color: "#10121a" }}>({pct})</span>}
      </div>
    </div>
  );
}

export function ValidationDashboard({ validation, t }: ValidationDashboardProps) {
  const [expanded, setExpanded] = useState(false);

  if (!validation) {
    console.log("[ValidationDashboard] No validation data");
    return null;
  }
  console.log("[ValidationDashboard] Rendering with:", validation);

  const errors = validation.errors ?? [];
  const warnings = validation.warnings ?? [];
  const hasDetails = errors.length > 0 || warnings.length > 0;

  return (
    <div className="p-4 space-y-3">
      <div className="flex flex-wrap gap-2">
        <StatCard
          icon={<CheckCircle2 className="h-3.5 w-3.5 text-green-600" />}
          label={t("poi_manager_valid_pct")}
          count={validation.valid ? validation.total_rows : 0}
          pct={validation.valid ? "100%" : "0%"}
          color={
            validation.valid
              ? "bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-900"
              : "bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-900"
          }
        />
        <StatCard
          icon={<XCircle className="h-3.5 w-3.5 text-red-600" />}
          label={t("poi_manager_errors")}
          count={errors.length}
          color="bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-900"
        />
        <StatCard
          icon={<AlertTriangle className="h-3.5 w-3.5 text-amber-600" />}
          label={t("poi_manager_warnings")}
          count={warnings.length}
          color="bg-amber-50 dark:bg-amber-950/20 border-amber-200 dark:border-amber-900"
        />
        <StatCard
          icon={<Building2 className="h-3.5 w-3.5 text-primary" />}
          label={t("poi_manager_summary_uploaded")}
          count={validation.total_rows}
          color="bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-900"
        />
      </div>

      {hasDetails && (
        <div>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 text-xs gap-1"
            onClick={() => setExpanded(!expanded)}
          >
            {expanded ? (
              <ChevronUp className="h-3 w-3" />
            ) : (
              <ChevronDown className="h-3 w-3" />
            )}
            {expanded
              ? t("poi_manager_validation_hide")
              : t("poi_manager_validation_detail")}
          </Button>
          {expanded && (
            <ScrollArea className="max-h-48 mt-2">
              <div className="space-y-1 text-xs">
                {errors.map((err, i) => (
                  <div
                    key={i}
                    className="flex items-start gap-2 px-2 py-1 rounded bg-red-50 dark:bg-red-950/20"
                  >
                    <XCircle className="h-3 w-3 text-red-500 mt-0.5 shrink-0" />
                    <span style={{ color: "#10121a" }}>
                      <strong>Row {err.row}:</strong> {err.message}
                    </span>
                  </div>
                ))}
                {warnings.map((w, i) => (
                  <div
                    key={i}
                    className="flex items-start gap-2 px-2 py-1 rounded bg-amber-50 dark:bg-amber-950/20"
                  >
                    <AlertTriangle className="h-3 w-3 text-amber-500 mt-0.5 shrink-0" />
                    <span style={{ color: "#10121a" }}>
                      <strong>Row {w.row}:</strong> {w.message}
                    </span>
                  </div>
                ))}
              </div>
            </ScrollArea>
          )}
        </div>
      )}
    </div>
  );
}
