import { useQuery } from "@tanstack/react-query";
import { classificationResultApi } from "@/api/endpoints";

export function useClassificationResult(jobId: string | null, enabled: boolean) {
  return useQuery({
    queryKey: ["classification-result", jobId],
    queryFn: () => classificationResultApi(jobId!),
    enabled: !!jobId && enabled,
    staleTime: 60_000,
  });
}