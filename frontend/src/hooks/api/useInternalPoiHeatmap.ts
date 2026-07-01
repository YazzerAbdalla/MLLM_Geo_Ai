import { useQuery } from "@tanstack/react-query";
import { internalPoiHeatmapApi } from "@/api/endpoints";
import type { InternalPoiHeatmapResponse } from "@/api/types";

export function useInternalPoiHeatmap() {
  return useQuery<InternalPoiHeatmapResponse>({
    queryKey: ["internal-poi-heatmap"],
    queryFn: internalPoiHeatmapApi,
    staleTime: 30 * 60_000,
    gcTime: 60 * 60_000,
    retry: 1,
  });
}
