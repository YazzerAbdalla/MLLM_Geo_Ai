import { api } from "./client";
import type {
  AreaStatusResponse,
  CancelResponse,
  ClassificationResult,
  ClassifyRequestBody,
  EvaluateResponse,
  ExportFormat,
  InternalPoiHeatmapResponse,
  JobId,
  LoadAreaRequest,
  PoiAnalysisResponse,
  PoiChatRequest,
  PoiChatResponse,
  PoiHeatmapResponse,
  PoiItem,
} from "./types";
import type {
  PoiPreviewResponse,
  PoiImportResponse,
  PoiQualityReviewRequest,
  PoiQualityReviewResponse,
} from "./poiDataManagerTypes";
import type { QueryRequest, QueryResponse } from "./types";

export async function loadAreaApi(body: LoadAreaRequest): Promise<JobId> {
  const { data } = await api.post<JobId>("/api/v1/load-area", body);
  return data;
}

export async function areaStatusApi(jobId: string): Promise<AreaStatusResponse> {
  const { data } = await api.get<AreaStatusResponse>(`/api/v1/area-status/${jobId}`);
  return data;
}

export async function classifyApi(body: ClassifyRequestBody): Promise<JobId> {
  const { data } = await api.post<JobId>("/api/v1/classify", body);
  return data;
}

export async function classificationResultApi(jobId: string): Promise<ClassificationResult> {
  const { data } = await api.get<ClassificationResult>(`/api/v1/classification-result/${jobId}`);
  return data;
}

export async function graphTopologyApi(
  gridId: string,
  opts: { maxNodes?: number; simplify?: boolean } = {}
): Promise<GeoJSON.FeatureCollection> {
  const { data } = await api.get<GeoJSON.FeatureCollection>(
    `/api/v1/grid/${gridId}/graph-topology`,
    { params: { max_nodes: opts.maxNodes, simplify: opts.simplify } }
  );
  return data;
}

export async function cancelJobApi(jobId: string): Promise<CancelResponse> {
  const { data } = await api.delete<CancelResponse>(`/api/v1/jobs/${jobId}`);
  return data;
}

export function exportJobUrl(jobId: string, format: ExportFormat): string {
  const base = (import.meta.env.VITE_API_URL as string) || "";
  return `${base.replace(/\/+$/, "")}/api/v1/export/${jobId}?format=${format}`;
}

export function evaluationExportUrl(jobId: string): string {
  const base = (import.meta.env.VITE_API_URL as string) || "";
  return `${base.replace(/\/+$/, "")}/api/v1/evaluate/${jobId}/export`;
}

export async function poiHeatmapApi(gridId: string): Promise<PoiHeatmapResponse> {
  const { data } = await api.get<PoiHeatmapResponse>(
    `/api/v1/grid/${gridId}/poi-heatmap`
  );
  return data;
}

export async function poiAnalysisApi(
  geometry: { type: "Polygon"; coordinates: number[][][] }
): Promise<PoiAnalysisResponse> {
  const { data } = await api.post<PoiAnalysisResponse>(
    "/api/v1/internal/poi-analysis",
    { geometry, include_location: false }
  );
  return data;
}

export async function internalPoiHeatmapApi(): Promise<InternalPoiHeatmapResponse> {
  const { data } = await api.get<InternalPoiHeatmapResponse>("/api/v1/internal/poi-heatmap");
  return data;
}

export async function gridPoisApi(gridId: string): Promise<PoiItem[]> {
  const { data } = await api.get<PoiItem[]>(`/api/v1/grid/${gridId}/pois`);
  return data;
}

export async function poiChatApi(body: PoiChatRequest): Promise<PoiChatResponse> {
  const { data } = await api.post<PoiChatResponse>("/api/v1/internal/poi-chat", body);
  return data;
}

export async function poiPreviewUploadApi(file: File): Promise<PoiPreviewResponse> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post<PoiPreviewResponse>("/api/v1/internal/poi-preview", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function poiImportConfirmApi(sessionId: string): Promise<PoiImportResponse> {
  const { data } = await api.post<PoiImportResponse>(`/api/v1/internal/poi-import/${sessionId}`);
  return data;
}

export async function poiQualityReviewApi(body: PoiQualityReviewRequest): Promise<PoiQualityReviewResponse> {
  const { data } = await api.post<PoiQualityReviewResponse>("/api/v1/internal/poi-quality-review", body);
  return data;
}

export function poiTemplateDownloadUrl(): string {
  const base = (import.meta.env.VITE_API_URL as string) || "";
  return `${base.replace(/\/+$/, "")}/api/v1/internal/poi-template`;
}

export function poiValidationReportUrl(previewId: string): string {
  const base = (import.meta.env.VITE_API_URL as string) || "";
  return `${base.replace(/\/+$/, "")}/api/v1/internal/poi-validation-report/${previewId}`;
}

export async function evaluateApi(jobId: string, file: File): Promise<EvaluateResponse> {
  const form = new FormData();
  form.append("job_id", jobId);
  form.append("ground_truth_file", file);
  const { data } = await api.post<EvaluateResponse>("/api/v1/evaluate", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function queryApi(body: QueryRequest): Promise<QueryResponse> {
  const { data } = await api.post<QueryResponse>("/api/v1/query", body);
  return data;
}