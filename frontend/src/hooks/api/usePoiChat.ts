import { useMutation } from "@tanstack/react-query";
import { poiChatApi } from "@/api/endpoints";
import type { PoiChatRequest, PoiChatResponse } from "@/api/types";

export function usePoiChat() {
  return useMutation<PoiChatResponse, Error, PoiChatRequest>({
    mutationFn: poiChatApi,
  });
}
