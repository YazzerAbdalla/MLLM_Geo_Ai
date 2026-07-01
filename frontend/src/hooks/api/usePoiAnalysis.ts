import { useQuery } from "@tanstack/react-query";
import { poiAnalysisApi } from "@/api/endpoints";
import type { PoiAnalysisResponse } from "@/api/types";

export function usePoiAnalysis(
  geometry: { type: "Polygon"; coordinates: number[][][] } | null
) {
  return useQuery<PoiAnalysisResponse>({
    queryKey: ["poi-analysis", JSON.stringify(geometry)],
    queryFn: () => poiAnalysisApi(geometry!),
    enabled: !!geometry,
    staleTime: 5 * 60_000,
    gcTime: 10 * 60_000,
    retry: 1,
  });
}
