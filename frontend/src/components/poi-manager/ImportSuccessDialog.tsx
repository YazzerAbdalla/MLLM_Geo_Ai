import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { CheckCircle2, Clock, ArrowRight, Upload, RotateCcw } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import type { PoiImportResponse } from "@/api/poiDataManagerTypes";

interface ImportSuccessDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  result: PoiImportResponse;
  processingTimeMs: number;
  onImportAnother: () => void;
  t: (key: string) => string;
}

export function ImportSuccessDialog({
  open,
  onOpenChange,
  result,
  processingTimeMs,
  onImportAnother,
  t,
}: ImportSuccessDialogProps) {
  const navigate = useNavigate();
  const [redirecting, setRedirecting] = useState(false);

  useEffect(() => {
    if (!open) {
      setRedirecting(false);
      return;
    }
    const timer = setTimeout(() => {
      setRedirecting(true);
      setTimeout(() => navigate("/"), 500);
    }, 10000);
    return () => clearTimeout(timer);
  }, [open, navigate]);

  const timeStr =
    processingTimeMs < 1000
      ? `${processingTimeMs}ms`
      : `${(processingTimeMs / 1000).toFixed(1)}s`;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <div className="flex flex-col items-center gap-3 py-2">
            <div className="flex items-center justify-center w-14 h-14 rounded-full bg-green-100 dark:bg-green-900/30">
              <CheckCircle2 className="h-8 w-8 text-green-600" />
            </div>
            <DialogTitle className="text-lg">
              {t("poi_manager_success_title")}
            </DialogTitle>
          </div>
        </DialogHeader>
        <div className="space-y-2 px-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">
              {t("poi_manager_success_imported")}
            </span>
            <span className="font-semibold text-green-600">
              {result.imported.toLocaleString()}
            </span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">
              {t("poi_manager_summary_skipped")}
            </span>
            <span className="font-semibold text-muted-foreground">
              {result.skipped.toLocaleString()}
            </span>
          </div>
          {result.duplicate_pois > 0 && (
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">
                {t("poi_manager_success_duplicate_pois")}
              </span>
              <span className="font-semibold text-orange-600">
                {result.duplicate_pois.toLocaleString()}
              </span>
            </div>
          )}
          {result.duplicate_coordinates > 0 && (
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">
                {t("poi_manager_success_duplicate_coords")}
              </span>
              <span className="font-semibold text-rose-600">
                {result.duplicate_coordinates.toLocaleString()}
              </span>
            </div>
          )}
          <div className="flex justify-between text-sm border-t border-border pt-2 mt-2">
            <span className="text-muted-foreground flex items-center gap-1">
              <Clock className="h-3.5 w-3.5" />
              {t("poi_manager_success_time")}
            </span>
            <span className="font-semibold mono">{timeStr}</span>
          </div>
        </div>
        <div className="flex flex-col gap-2 pt-2">
          <Button
            size="sm"
            className="gap-2"
            onClick={() => {
              setRedirecting(true);
              setTimeout(() => navigate("/"), 500);
            }}
            disabled={redirecting}
          >
            {redirecting ? (
              <>
                <span className="animate-pulse">{t("poi_manager_success_redirecting")}</span>
              </>
            ) : (
              <>
                <ArrowRight className="h-4 w-4" />
                {t("poi_manager_success_go_dashboard")}
              </>
            )}
          </Button>
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="outline"
              className="flex-1 gap-1"
              onClick={onImportAnother}
            >
              <Upload className="h-3.5 w-3.5" />
              {t("poi_manager_success_import_another")}
            </Button>
            <Button
              size="sm"
              variant="ghost"
              className="flex-1 gap-1"
              onClick={() => onOpenChange(false)}
            >
              <RotateCcw className="h-3.5 w-3.5" />
              {t("poi_manager_success_stay")}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
