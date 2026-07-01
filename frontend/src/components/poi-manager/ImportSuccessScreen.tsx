import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { CheckCircle2, Clock, ArrowRight, Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { PoiImportResponse } from "@/api/poiDataManagerTypes";

interface ImportSuccessScreenProps {
  result: PoiImportResponse;
  processingTimeMs: number;
  onDashboard: () => void;
  onImportAnother: () => void;
  t: (key: string) => string;
}

export function ImportSuccessScreen({
  result,
  processingTimeMs,
  onDashboard,
  onImportAnother,
  t,
}: ImportSuccessScreenProps) {
  const navigate = useNavigate();
  const [redirecting, setRedirecting] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setRedirecting(true);
      setTimeout(() => navigate("/"), 500);
    }, 10000);
    return () => clearTimeout(timer);
  }, [navigate]);

  const timeStr =
    processingTimeMs < 1000
      ? `${processingTimeMs}ms`
      : `${(processingTimeMs / 1000).toFixed(1)}s`;

  return (
    <div className="max-w-md w-full mx-auto flex flex-col items-center gap-6 py-8">
      <div className="flex items-center justify-center w-16 h-16 rounded-full bg-green-100 dark:bg-green-900/30">
        <CheckCircle2 className="h-10 w-10 text-green-600" />
      </div>
      <h2 className="text-xl font-semibold">{t("poi_manager_success_title")}</h2>
      <div className="w-full space-y-3 bg-card border border-border rounded-lg p-5">
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">{t("poi_manager_success_imported")}</span>
          <span className="font-semibold text-green-600">{result.imported.toLocaleString()}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">{t("poi_manager_summary_skipped")}</span>
          <span className="font-semibold text-muted-foreground">{result.skipped.toLocaleString()}</span>
        </div>
        {result.duplicate_pois > 0 && (
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">{t("poi_manager_success_duplicate_pois")}</span>
            <span className="font-semibold text-orange-600">{result.duplicate_pois.toLocaleString()}</span>
          </div>
        )}
        {result.duplicate_coordinates > 0 && (
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">{t("poi_manager_success_duplicate_coords")}</span>
            <span className="font-semibold text-rose-600">{result.duplicate_coordinates.toLocaleString()}</span>
          </div>
        )}
        <div className="flex justify-between text-sm border-t border-border pt-3 mt-3">
          <span className="text-muted-foreground flex items-center gap-1">
            <Clock className="h-3.5 w-3.5" />
            {t("poi_manager_success_time")}
          </span>
          <span className="font-semibold mono">{timeStr}</span>
        </div>
      </div>
      <div className="flex flex-col gap-2 w-full">
        <Button size="sm" className="gap-2" onClick={onDashboard} disabled={redirecting}>
          {redirecting ? (
            <span className="animate-pulse">{t("poi_manager_success_redirecting")}</span>
          ) : (
            <>
              <ArrowRight className="h-4 w-4" />
              {t("poi_manager_success_go_dashboard")}
            </>
          )}
        </Button>
        <Button size="sm" variant="outline" className="gap-1" onClick={onImportAnother}>
          <Upload className="h-3.5 w-3.5" />
          {t("poi_manager_success_import_another")}
        </Button>
      </div>
    </div>
  );
}
