import { useState } from "react";
import { Sparkles, ChevronDown, ChevronUp, AlertTriangle, Info, XCircle, Wand2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import type { PoiQualityReviewResponse, PoiQualityReviewFinding } from "@/api/poiDataManagerTypes";

interface DataQualityReviewProps {
  t: (key: string) => string;
  onReview: () => void;
  onFix: () => void;
  result: PoiQualityReviewResponse | null;
  loading: boolean;
  fixing: boolean;
}

function FindingIcon({ severity }: { severity: PoiQualityReviewFinding["severity"] }) {
  switch (severity) {
    case "error":
      return <XCircle className="h-3.5 w-3.5 text-red-500 shrink-0 mt-0.5" />;
    case "warning":
      return <AlertTriangle className="h-3.5 w-3.5 text-amber-500 shrink-0 mt-0.5" />;
    case "info":
      return <Info className="h-3.5 w-3.5 text-blue-500 shrink-0 mt-0.5" />;
  }
}

function ScoreBadge({ score }: { score: number }) {
  const color =
    score >= 80
      ? "text-green-600 bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-900"
      : score >= 50
        ? "text-amber-600 bg-amber-50 dark:bg-amber-950/20 border-amber-200 dark:border-amber-900"
        : "text-red-600 bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-900";

  return (
    <span className={cn("text-xs font-bold px-2 py-0.5 rounded-full border", color)}>
      {score}/100
    </span>
  );
}

export function DataQualityReview({
  t,
  onReview,
  onFix,
  result,
  loading,
  fixing,
}: DataQualityReviewProps) {
  const [open, setOpen] = useState(false);

  return (
    <div className="border border-border rounded-lg">
      <button
        onClick={() => {
          if (!result && !loading) onReview();
          setOpen(!open);
        }}
        className="w-full flex items-center justify-between px-3 py-2 text-xs font-medium text-left hover:bg-secondary/40 transition-colors rounded-lg"
      >
        <div className="flex items-center gap-2">
          <Sparkles className="h-3.5 w-3.5 text-primary" />
          <span>{t("poi_manager_quality_title")}</span>
          {result && <ScoreBadge score={result.overall_score} />}
          {loading && <Loader2 className="h-3 w-3 animate-spin text-muted-foreground" />}
        </div>
        {open ? <ChevronUp className="h-3.5 w-3.5 text-muted-foreground" /> : <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />}
      </button>

      {open && (
        <div className="px-3 pb-3 space-y-3 border-t border-border pt-2">
          {loading && (
            <div className="space-y-2">
              <Skeleton className="h-3 w-3/4" />
              <Skeleton className="h-3 w-full" />
              <Skeleton className="h-3 w-2/3" />
            </div>
          )}

          {result && !loading && (
            <>
              {result.findings.length > 0 && (
                <div>
                  <h4 className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1.5">
                    {t("poi_manager_quality_findings")}
                  </h4>
                  <div className="space-y-1">
                    {result.findings.map((finding, i) => (
                      <div key={i} className="flex items-start gap-1.5 text-xs">
                        <FindingIcon severity={finding.severity} />
                        <span className="text-muted-foreground">
                          {finding.message}
                          {finding.suggestion && (
                            <span className="block text-[10px] text-muted-foreground/60 mt-0.5">
                              💡 {finding.suggestion}
                            </span>
                          )}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {result.suggestions.length > 0 && (
                <div>
                  <h4 className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1.5">
                    {t("poi_manager_quality_suggestions")}
                  </h4>
                  <ul className="space-y-0.5 text-xs text-muted-foreground">
                    {result.suggestions.map((s, i) => (
                      <li key={i} className="flex items-start gap-1.5">
                        <span className="text-green-500">✓</span>
                        <span>{s}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {result.fixable && (
                <Button
                  size="sm"
                  variant="outline"
                  className="w-full h-7 text-xs gap-1.5"
                  onClick={onFix}
                  disabled={fixing}
                >
                  {fixing ? (
                    <Loader2 className="h-3 w-3 animate-spin" />
                  ) : (
                    <Wand2 className="h-3 w-3" />
                  )}
                  {t("poi_manager_quality_fix")}
                </Button>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
