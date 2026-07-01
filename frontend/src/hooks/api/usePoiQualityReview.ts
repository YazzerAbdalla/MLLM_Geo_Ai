import { useMutation } from "@tanstack/react-query";
import { api } from "@/api/client";
import type {
  PoiQualityReviewRequest,
  PoiQualityReviewResponse,
} from "@/api/poiDataManagerTypes";

async function poiQualityReviewApi(
  body: PoiQualityReviewRequest
): Promise<PoiQualityReviewResponse> {
  const { data } = await api.post<PoiQualityReviewResponse>(
    "/api/v1/internal/poi-quality-review",
    body
  );
  return data;
}

export function usePoiQualityReview() {
  return useMutation<PoiQualityReviewResponse, Error, PoiQualityReviewRequest>({
    mutationFn: poiQualityReviewApi,
  });
}
