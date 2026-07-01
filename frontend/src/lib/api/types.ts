export type LandUseClass = "Residential" | "Commercial" | "Industrial";
export type Modality = "poi" | "image" | "graph" | "text";
export type ModelType = "mlp" | "gnn";
export type FusionMethod = "concat" | "weighted" | "attention";
export type LoadingStep =
  | "downloading_poi"
  | "mapping_poi_to_nodes"
  | "building_graph"
  | "classifying";

export interface CellDatum {
  id: string;
  row: number;
  col: number;
  class: LandUseClass;
  confidence: number;
  confidences: Record<LandUseClass, number>;
  top5_poi: string[];
  road_density: number;
  node_count: number;
  degree_centrality: number;
  clustering_coeff: number;
  total_road_length_m: number;
  graph_embedding_norm: number;
  text_embedding_norm: number;
  satellite_thumb: string;
  gridId: string;
  geometry: { type: "Polygon"; coordinates: number[][][] };
  centroid: [number, number];
}

export interface ClassifyRequest {
  grid_id: string;
  modalities: Modality[];
  model_type: ModelType;
  fusion_method: FusionMethod;
  /** Optional user-drawn geometry to clip the classification grid (PRD §6.1) */
  area_geometry?: { type: "Polygon"; coordinates: number[][][] } | null;
}

export interface EvaluateResponse {
  accuracy: number;
  macro_f1: number;
  weighted_f1: number;
  spatial_accuracy: number;
  per_class_f1: Record<LandUseClass, number>;
  confusion_matrix: number[][];
  class_labels: LandUseClass[];
}