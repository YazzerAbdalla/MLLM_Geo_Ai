import { useQuery } from "@tanstack/react-query";
import { poiHeatmapApi } from "@/api/endpoints";
import type { PoiHeatmapResponse } from "@/api/types";

export function usePoiHeatmap(
  gridId: string | null,
  opts: { enabled?: boolean } = {}
) {
  const { enabled = true } = opts;
  return useQuery<PoiHeatmapResponse>({
    queryKey: ["poi-heatmap", gridId],
    queryFn: () => poiHeatmapApi(gridId!),
    enabled: !!gridId && enabled,
    staleTime: 5 * 60_000,
    gcTime: 10 * 60_000,
    refetchOnMount: false,
    retry: 1,
  });
}
