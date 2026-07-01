export interface PoiCsvRow {
  name: string;
  category: string;
  lat: number;
  lng: number;
  place_type?: string;
  label?: string;
  weight?: number;
}

export interface PoiUploadValidation {
  valid: boolean;
  total_rows: number;
  errors: Array<{ row: number; message: string }>;
  warnings: Array<{ row: number; message: string }>;
}

export type PoiValidationResult = PoiUploadValidation;

export interface PoiPreviewFeatureProperties {
  name: string;
  category: string;
  place_type: string;
  osm_id: string;
  label: string;
  weight: number;
  status: "new" | "valid_imported" | "duplicate_poi" | "duplicate_coord" | "invalid";
}

export interface PoiPreviewStatistics {
  total: number;
  valid: number;
  skipped: number;
  duplicate_pois: number;
  duplicate_coords: number;
  categories: Record<string, number>;
  category_count: number;
  center?: { lat: number; lng: number };
  bbox?: { north: number; south: number; east: number; west: number };
}

export interface PoiPreviewResponse {
  session_id?: string;
  validation: PoiValidationResult;
  features?: GeoJSON.FeatureCollection<GeoJSON.Point, PoiPreviewFeatureProperties>;
  statistics?: PoiPreviewStatistics;
  category_counts?: Record<string, number>;
}

export interface PoiImportResponse {
  imported: number;
  skipped: number;
  duplicate_coordinates: number;
  duplicate_pois: number;
  warnings: string[];
  total_pois: number;
  processing_time_ms: number;
}

export interface PoiQualityReviewFinding {
  type: "duplicate_name" | "near_duplicate" | "category_dominance" | "missing_field";
  severity: "info" | "warning" | "error";
  message: string;
  affected_rows?: number[];
  suggestion?: string;
}

export interface PoiQualityReviewResponse {
  overall_score: number;
  findings: PoiQualityReviewFinding[];
  suggestions: string[];
  fixable: boolean;
}

export interface PoiQualityReviewRequest {
  preview_id: string;
  features: GeoJSON.FeatureCollection<GeoJSON.Point, PoiPreviewFeatureProperties>;
}

export interface PoiValidationReportRow {
  row: number;
  problem: string;
  reason: string;
  suggested_fix: string;
}
