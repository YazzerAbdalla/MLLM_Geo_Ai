import { useMutation } from "@tanstack/react-query";
import { classifyApi } from "@/api/endpoints";

export function useClassify() {
  return useMutation({ mutationFn: classifyApi });
}