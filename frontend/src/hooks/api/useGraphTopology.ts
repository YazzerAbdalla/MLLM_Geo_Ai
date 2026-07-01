import { useQuery } from "@tanstack/react-query";
import { graphTopologyApi } from "@/api/endpoints";

export function useGraphTopology(
  gridId: string | null,
  opts: { enabled?: boolean; maxNodes?: number; simplify?: boolean } = {}
) {
  const { enabled = true, maxNodes = 500, simplify = true } = opts;
  return useQuery({
    queryKey: ["graph-topology", gridId, maxNodes, simplify],
    queryFn: () => graphTopologyApi(gridId!, { maxNodes, simplify }),
    enabled: !!gridId && enabled,
    staleTime: 5 * 60_000,
  });
}