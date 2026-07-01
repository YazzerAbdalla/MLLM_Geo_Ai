import { useEffect } from "react";
import { useDash } from "@/store/dashboardStore";

export function useKeyboardShortcuts(handlers: {
  onDraw?: () => void; onClassify?: () => void; onEvaluation?: () => void; onCancel?: () => void;
}) {
  const setSelected = useDash((s) => s.setSelectedCellId);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      if (target?.tagName === "INPUT" || target?.tagName === "TEXTAREA") return;
      switch (e.key.toLowerCase()) {
        case "d": handlers.onDraw?.(); break;
        case "c": handlers.onClassify?.(); break;
        case "e": handlers.onEvaluation?.(); break;
        case "escape": handlers.onCancel?.(); setSelected(null); break;
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [handlers, setSelected]);
}
