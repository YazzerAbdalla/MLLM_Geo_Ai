/**
 * Feature flags for backend endpoints that are not yet live.
 * Stub pages can read these to render "Coming soon" instead of calling the API.
 */
export const FEATURES = {
  /** POST /api/v1/mllm/train */
  mllmTrain: false,
  /** POST /api/v1/query (Digital Twin NL query) */
  digitalTwin: false,
  /** GET  /api/v1/grid/{grid_id}/details — per-cell drill-down */
  gridDetailsApi: false,
  /** POST /api/v1/internal/poi-quality-review — AI data quality review */
  poiQualityReview: false,
} as const;

export type FeatureFlag = keyof typeof FEATURES;