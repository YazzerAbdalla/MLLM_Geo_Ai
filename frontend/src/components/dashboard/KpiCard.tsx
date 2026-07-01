import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { Info } from "lucide-react";

interface KpiCardProps {
  label: string;
  value: number;
  format?: "percent" | "decimal";
  tooltip?: string;
  detail?: string;
}

function statusForPercent(pct: number) {
  if (pct >= 90) return "success" as const;
  if (pct >= 80) return "warning" as const;
  return "attention" as const;
}

const statusColors = {
  success: { dot: "bg-primary", text: "text-primary", border: "border-primary/30" },
  warning: { dot: "bg-accent", text: "text-accent", border: "border-accent/30" },
  attention: { dot: "bg-destructive", text: "text-destructive", border: "border-destructive/30" },
};

export function KpiCard({ label, value, format = "percent", tooltip, detail }: KpiCardProps) {
  const pct = format === "percent" ? value * 100 : value * 100;
  const status = statusForPercent(pct);
  const c = statusColors[status];
  const displayValue = format === "percent" ? `${(value * 100).toFixed(1)}%` : value.toFixed(3);

  return (
    <div className={cn("rounded border bg-secondary/40 p-3 space-y-1.5", c.border)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <span className={cn("h-1.5 w-1.5 rounded-full", c.dot)} />
          <span className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</span>
        </div>
        {tooltip && (
          <TooltipProvider delayDuration={200}>
            <Tooltip>
              <TooltipTrigger asChild>
                <Info className="h-3 w-3 text-muted-foreground cursor-help" />
              </TooltipTrigger>
              <TooltipContent side="top" className="max-w-[220px] text-[11px] leading-relaxed">
                {tooltip}
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}
      </div>
      <div className={cn("mono text-base font-semibold", c.text)}>{displayValue}</div>
      {detail && <p className="text-[10px] text-muted-foreground leading-tight">{detail}</p>}
    </div>
  );
}
