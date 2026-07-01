import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

const STEPS = [
  { key: 1, labelKey: "poi_manager_step_download" },
  { key: 2, labelKey: "poi_manager_step_upload" },
  { key: 3, labelKey: "poi_manager_step_validate" },
  { key: 4, labelKey: "poi_manager_step_preview" },
  { key: 5, labelKey: "poi_manager_step_import" },
] as const;

interface WizardHeaderProps {
  currentStep: number;
  t: (key: string) => string;
}

export function WizardHeader({ currentStep, t }: WizardHeaderProps) {
  return (
    <div className="flex items-center justify-center gap-0 px-4 py-3 border-b border-border bg-card">
      {STEPS.map((step, i) => {
        const isCompleted = currentStep > step.key;
        const isActive = currentStep === step.key;
        const isLast = i === STEPS.length - 1;
        return (
          <div key={step.key} className="flex items-center gap-0">
            <div className="flex items-center gap-2">
              <div
                className={cn(
                  "flex items-center justify-center w-7 h-7 rounded-full text-xs font-semibold transition-colors shrink-0",
                  isCompleted && "bg-primary text-primary-foreground",
                  isActive && "bg-primary text-primary-foreground ring-2 ring-primary/30",
                  !isCompleted && !isActive && "bg-secondary text-muted-foreground"
                )}
              >
                {isCompleted ? <Check className="h-3.5 w-3.5" /> : step.key}
              </div>
              <span
                className={cn(
                  "text-xs font-medium hidden sm:inline transition-colors",
                  isActive && "text-foreground",
                  isCompleted && "text-muted-foreground",
                  !isCompleted && !isActive && "text-muted-foreground/60"
                )}
              >
                {t(step.labelKey)}
              </span>
            </div>
            {!isLast && (
              <div
                className={cn(
                  "w-6 sm:w-10 h-px mx-1 sm:mx-2 transition-colors",
                  currentStep > step.key ? "bg-primary" : "bg-border"
                )}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
