import { useQuery } from "@tanstack/react-query";
import { gridPoisApi } from "@/api/endpoints";

export function usePois(gridId: string | null) {
  return useQuery({
    queryKey: ["grid-pois", gridId],
    queryFn: () => gridPoisApi(gridId!),
    enabled: !!gridId,
    staleTime: 5 * 60_000,
  });
}
