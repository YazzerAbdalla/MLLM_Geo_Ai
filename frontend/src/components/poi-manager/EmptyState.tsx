import { useRef, useState, useCallback, type DragEvent } from "react";
import { Upload, FileDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface EmptyStateProps {
  t: (key: string) => string;
  onDownloadTemplate: () => void;
  onUpload: (file: File) => void;
  dragging: boolean;
  onDragChange: (dragging: boolean) => void;
}

export function EmptyState({
  t,
  onDownloadTemplate,
  onUpload,
  dragging,
  onDragChange,
}: EmptyStateProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dragCounterRef = useRef(0);

  const handleDragEnter = useCallback(
    (e: DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      dragCounterRef.current++;
      if (e.dataTransfer.items?.length > 0) {
        onDragChange(true);
      }
    },
    [onDragChange]
  );

  const handleDragLeave = useCallback(
    (e: DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      dragCounterRef.current--;
      if (dragCounterRef.current === 0) {
        onDragChange(false);
      }
    },
    [onDragChange]
  );

  const handleDragOver = useCallback((e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback(
    (e: DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      dragCounterRef.current = 0;
      onDragChange(false);
      const file = e.dataTransfer.files?.[0];
      if (file && file.name.endsWith(".csv")) {
        if (file.size > 10 * 1024 * 1024) return;
        onUpload(file);
      }
    },
    [onUpload, onDragChange]
  );

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        if (file.size > 10 * 1024 * 1024) return;
        onUpload(file);
      }
      e.target.value = "";
    },
    [onUpload]
  );

  return (
    <div
      className="flex-1 flex items-center justify-center"
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
    >
      <div
        className={cn(
          "flex flex-col items-center gap-5 p-12 rounded-2xl border-2 border-dashed transition-all max-w-md w-full mx-4",
          dragging
            ? "border-primary bg-primary/5 scale-[1.02]"
            : "border-border bg-card/50"
        )}
      >
        <div className="flex items-center justify-center w-16 h-16 rounded-full bg-primary/10">
          <Upload className="h-8 w-8 text-primary" />
        </div>
        <div className="text-center space-y-1">
          <h2 className="text-lg font-semibold">{t("poi_manager_empty_title")}</h2>
          <p className="text-sm text-muted-foreground">
            {t("poi_manager_empty_desc")}
          </p>
        </div>
        <div className="flex flex-col sm:flex-row gap-3 w-full">
          <Button
            variant="outline"
            size="sm"
            className="gap-2"
            onClick={onDownloadTemplate}
          >
            <FileDown className="h-4 w-4" />
            {t("poi_manager_download_template")}
          </Button>
          <Button size="sm" className="gap-2" onClick={() => fileInputRef.current?.click()}>
            <Upload className="h-4 w-4" />
            {t("poi_manager_upload_csv")}
          </Button>
        </div>
        <p className="text-xs text-muted-foreground/60">
          {t("poi_manager_drag_zone")}
        </p>
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv"
          className="hidden"
          onChange={handleFileSelect}
        />
      </div>
    </div>
  );
}
