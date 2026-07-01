import type { FusionMethod, LandUseClass, LoadingStep, Modality, ModelType } from "@/lib/api/types";

export type { FusionMethod, LandUseClass, LoadingStep, Modality, ModelType };

export type JobStatus =
  | "queued"
  | "loading"
  | "running"
  | "processing"
  | "done"
  | "completed"
  | "failed"
  | "cancelled";

export interface JobId { job_id: string }

export interface LoadAreaRequest {
  /** [west, south, east, north] */
  bbox: [number, number, number, number];
  place_name?: string;
}

export interface AreaStatusResponse {
  status: JobStatus;
  step?: LoadingStep | string;
  progress?: number;
  message?: string;
  /** Generated grid ID when status is completed/done */
  grid_id?: string;
}

export interface ClassifyRequestBody {
  grid_id: string;
  cell_size: number;
  modalities: Modality[];
  model_type?: ModelType;
  fusion_method?: FusionMethod;
  area_geometry?: { type: "Polygon"; coordinates: number[][][] } | null;
}

/**
 * Backend v1 classification result — fields arrive as GeoJSON Feature properties.
 * Some backends return the same fields *flat* on the feature object itself;
 * see {@link BackendFeatureFlat} for that shape.
 */
export interface ClassificationFeatureProps {
  cell_id: string;
  class: LandUseClass;
  confidences: Record<LandUseClass, number>;
  road_density?: number;
  node_count?: number;
  top_poi?: string[];
  graph_embedding_norm?: number;
  text_embedding_norm?: number;
  degree_centrality?: number;
  clustering_coeff?: number;
  total_road_length_m?: number;
  satellite_thumb?: string;
}

/**
 * Real backend response shape — all classification fields sit *flat* on the
 * GeoJSON Feature alongside `geometry` (no `properties` wrapper).
 * Confidences use lowercase class names; class identity comes from
 * `dominant_class`; POI list is `poi_top_categories`; thumbnail is
 * `satellite_thumbnail_url`.
 */
export interface BackendFeatureFlat {
  cell_id: number;
  dominant_class: string;
  confidence: number;
  confidences: Record<string, number>;
  road_density?: number;
  node_count?: number;
  degree_centrality?: number;
  clustering_coeff?: number;
  total_road_length_m?: number;
  poi_top_categories?: string[];
  text_embedding_norm?: number;
  graph_embedding_norm?: number;
  satellite_thumbnail_url?: string;
  geometry: GeoJSON.Polygon;
  centroid?: [number, number];
}

export type ClassificationFeature = GeoJSON.Feature<GeoJSON.Polygon, ClassificationFeatureProps>;
export type ClassificationResult = GeoJSON.FeatureCollection<GeoJSON.Polygon, ClassificationFeatureProps>;

export interface EvaluateResponse {
  overall_accuracy: number;
  macro_f1: number;
  weighted_f1: number;
  spatial_accuracy: number;
  per_class_f1: Record<LandUseClass, number>;
  confusion_matrix: number[][];
  class_labels?: LandUseClass[];
}

export interface PoiItem {
  name: string;
  category: string;
  lat: number;
  lng: number;
}

export type PoiHeatmapResponse =
  GeoJSON.FeatureCollection<GeoJSON.Point> & {
    metadata?: {
      total_pois: number;
    };
  };

export interface InternalPoiHeatmapPoiProperties {
  name: string;
  category: string;
  place_type: string;
  osm_id: string;
  label: string;
  weight?: number;
}

export interface InternalPoiHeatmapResponse {
  type: "FeatureCollection";
  features: GeoJSON.Feature<GeoJSON.Point, InternalPoiHeatmapPoiProperties>[];
  metadata: {
    total_pois: number;
    num_categories: number;
    dataset_source: string;
  };
}

export interface PoiAnalysisCategory {
  category: string;
  count: number;
}

export interface PoiAnalysisResponse {
  type: "FeatureCollection";
  features: GeoJSON.Feature<GeoJSON.Point, InternalPoiHeatmapPoiProperties>[];
  analysis: {
    total_pois: number;
    area_m2?: number;
    area_km2?: number;
    perimeter_m?: number;
    poi_density?: number;
    centroid?: { type: string; coordinates: [number, number] };
    category_counts?: PoiAnalysisCategory[];
    top_categories?: PoiAnalysisCategory[];
    reverse_geocoding?: {
      area_name?: string;
      city?: string;
      country?: string;
    } | null;
    returned_pois?: number;
    truncated?: boolean;
  };
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  status: "pending" | "completed" | "failed";
  request?: PoiChatRequest;
}

export interface PoiChatRequest {
  analysis: PoiAnalysisResponse["analysis"];
  question: string;
  history?: { role: "user" | "assistant"; content: string }[];
}

export interface PoiChatResponse {
  summary: string;
  answer: string;
  model: string;
}

export interface CancelResponse {
  status: "cancelled";
  job_id: string;
}

export interface QueryRequest {
  question: string;
  grid_id: string;
}

export interface QueryMatchedCell {
  cell_id: string;
  dominant_class: string;
  confidence: number;
  centroid: [number, number];
  road_density: number;
  poi_categories: string[];
}

export interface QueryResponse {
  answer: string;
  query_type: string;
  confidence: number;
  matched_cells: QueryMatchedCell[];
}

export type ExportFormat = "geojson" | "csv" | "shapefile";

export const TERMINAL_STATUSES: JobStatus[] = ["done", "completed", "failed", "cancelled"];
export const isTerminal = (s?: JobStatus | string): boolean =>
  !!s && (TERMINAL_STATUSES as string[]).includes(s);
export const isSuccess = (s?: JobStatus | string): boolean =>
  s === "done" || s === "completed";