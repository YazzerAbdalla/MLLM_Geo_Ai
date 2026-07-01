import { useQuery } from "@tanstack/react-query";
import { classificationResultApi } from "@/api/endpoints";
import { featureToCell } from "@/lib/adapters";

export function useClassification(jobId: string | null) {
  return useQuery({
    queryKey: ["classification", jobId],
    queryFn: async () => {
      const raw = await classificationResultApi(jobId!);
      const cells = raw.features.map(featureToCell);
      // Current backend returns one grid per classification result.
      // All cells share the same gridId, derived from the thumbnail URL.
      const gridId = cells[0]?.gridId ?? null;
      return { raw, cells, gridId };
    },
    enabled: !!jobId,
    staleTime: 5 * 60_000,
  });
}
