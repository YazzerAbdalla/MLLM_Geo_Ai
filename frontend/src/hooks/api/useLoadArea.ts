import { useMutation } from "@tanstack/react-query";
import { loadAreaApi } from "@/api/endpoints";

export function useLoadArea() {
  return useMutation({ mutationFn: loadAreaApi });
}