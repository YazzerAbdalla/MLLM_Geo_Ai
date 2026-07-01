import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { AlertTriangle } from "lucide-react";
interface PoiUploadValidation {
  valid: boolean;
  total_rows: number;
  errors: Array<{ row: number; message: string }>;
  warnings: Array<{ row: number; message: string }>;
}

interface ImportConfirmationDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
  validation: PoiUploadValidation;
  t: (key: string) => string;
}

export function ImportConfirmationDialog({
  open,
  onOpenChange,
  onConfirm,
  validation,
  t,
}: ImportConfirmationDialogProps) {
  if (!validation) {
    console.log("[ImportConfirmationDialog] No validation data");
    return null;
  }
  console.log("[ImportConfirmationDialog] Open:", open, "validation:", validation);
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>
            {t("poi_manager_confirm_title")}
          </AlertDialogTitle>
          <AlertDialogDescription>
            <div className="space-y-2 pt-2 text-sm text-muted-foreground">
              <p>
                {(validation.valid
                  ? t("poi_manager_confirm_new")
                  : "Validation failed"
                ).replace("{count}", validation.total_rows.toLocaleString())}
              </p>
              <div className="flex flex-col gap-1 text-xs">
                {validation.errors.length > 0 && (
                  <span className="flex items-center gap-2 text-red-600">
                    <AlertTriangle className="h-3.5 w-3.5" />
                    {validation.errors.length.toLocaleString()} {t("poi_manager_errors")}
                  </span>
                )}
                {validation.warnings.length > 0 && (
                  <span className="flex items-center gap-2 text-amber-600">
                    <AlertTriangle className="h-3.5 w-3.5" />
                    {validation.warnings.length.toLocaleString()} {t("poi_manager_warnings")}
                  </span>
                )}
              </div>
            </div>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel className="text-xs">
            {t("cancel")}
          </AlertDialogCancel>
          <AlertDialogAction className="text-xs" onClick={onConfirm}>
            {t("poi_manager_import")}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
