import { useMutation } from "@tanstack/react-query";
import { cancelJobApi } from "@/api/endpoints";

export function useCancelJob() {
  return useMutation({ mutationFn: cancelJobApi });
}