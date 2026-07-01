import { useMemo } from "react";
import { useClassification } from "./useClassification";

export function useCell(jobId: string | null, cellId: string | null) {
  const clsQ = useClassification(jobId);
  const cell = useMemo(() => {
    if (!clsQ.data || !cellId) return null;
    return clsQ.data.cells.find((c) => c.id === cellId) ?? null;
  }, [clsQ.data, cellId]);
  return { ...clsQ, cell };
}
