import { useMutation } from "@tanstack/react-query";
import { evaluateApi } from "@/api/endpoints";

export function useEvaluate() {
  return useMutation({
    mutationFn: ({ jobId, file }: { jobId: string; file: File }) => evaluateApi(jobId, file),
  });
}