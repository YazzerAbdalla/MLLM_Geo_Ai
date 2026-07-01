/**
 * @file adapters.ts
 * @description Maps raw backend classification features (GeoJSON) to the
 * internal {@link CellDatum} shape used by the UI.
 *
 * The real backend returns a **flat** feature object where fields like
 * `cell_id`, `dominant_class`, and `confidences` sit directly on the
 * feature alongside `geometry` — **not** inside a `properties` wrapper.
 * This module handles both the legacy `properties`-wrapped shape and the
 * current flat shape transparently.
 */

import type { BackendFeatureFlat, ClassificationFeature } from "@/api/types";
import type { CellDatum, LandUseClass } from "@/lib/api/types";
import { extractGridIdFromThumbnail } from "@/lib/gridUtils";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Computes the centroid of a GeoJSON Polygon by averaging its outer ring.
 *
 * @param polygon GeoJSON Polygon geometry
 * @returns [lng, lat] centroid pair
 */
function centroidOf(polygon: GeoJSON.Polygon): [number, number] {
  const ring = polygon.coordinates[0];
  let x = 0, y = 0;
  for (const [lng, lat] of ring) { x += lng; y += lat; }
  const n = ring.length || 1;
  return [x / n, y / n];
}

/**
 * Capitalises the first letter of a string.
 *
 * @param s Input string
 * @returns Capitalised string
 */
function capitalise(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

/**
 * Normalises a confidences map whose keys may be lowercase (backend) or
 * title-case (legacy) into a `Record<LandUseClass, number>`.
 *
 * @param raw Raw confidences object from the backend
 * @returns Normalised confidences keyed by title-case LandUseClass
 */
function normaliseConfidences(
  raw: Record<string, number> | undefined,
): Record<LandUseClass, number> {
  const defaults: Record<LandUseClass, number> = { Residential: 0, Commercial: 0, Industrial: 0 };
  if (!raw) return defaults;
  // Build a normalised copy — capitalise each key to match LandUseClass union
  const result = { ...defaults };
  for (const [k, v] of Object.entries(raw)) {
    const key = capitalise(k) as LandUseClass;
    if (key in result) result[key] = v;
  }
  return result;
}

// ---------------------------------------------------------------------------
// Main adapter
// ---------------------------------------------------------------------------

/**
 * Maps a backend classification feature to the internal {@link CellDatum}.
 *
 * Supports two backend shapes:
 * 1. **Flat shape** – fields (`cell_id`, `dominant_class`, etc.) sit directly
 *    on the feature object (no `properties` wrapper).  This is what the current
 *    FastAPI backend returns.
 * 2. **Wrapped shape** – fields sit inside `feature.properties` as standard
 *    GeoJSON.  Used by legacy/mock responses.
 *
 * Field differences handled:
 * - `dominant_class`  → `class`      (flat shape)
 * - `poi_top_categories` → `top5_poi`  (flat shape)
 * - `satellite_thumbnail_url` → `satellite_thumb` (flat shape)
 * - `cell_id` number  → string `id`  (flat shape)
 * - `confidences` lowercase keys → title-case `LandUseClass` keys
 *
 * @param f Raw GeoJSON Feature from the classification result endpoint
 * @returns Normalised CellDatum for the UI
 */
export function featureToCell(f: ClassificationFeature | BackendFeatureFlat): CellDatum {
  // --- Detect shape: flat (BackendFeatureFlat) vs wrapped (ClassificationFeature) ---
  // The real backend returns fields flat on the feature object (no properties wrapper).
  // Check for the hallmark flat field `dominant_class` to be robust against
  // GeoJSON features that carry an empty `properties: {}` (which is truthy).
  const anyF = f as Record<string, unknown>;
  const isFlat = "dominant_class" in anyF ||
    !(f as ClassificationFeature).properties ||
    (f as ClassificationFeature).properties === null;

  // Pull the geometry — present on both shapes
  const geometry = f.geometry as GeoJSON.Polygon;

  if (isFlat) {
    // -----------------------------------------------------------------------
    // Flat shape — all fields directly on the feature object
    // -----------------------------------------------------------------------
    const flat = f as unknown as BackendFeatureFlat;
    const confidences = normaliseConfidences(flat.confidences);

    if (import.meta.env.DEV) {
      console.log("[featureToCell] flat shape — dominant_class:", flat.dominant_class, "cell_id:", flat.cell_id);
    }

    // dominant_class from backend → resolve to known LandUseClass (title-case)
    const dominantRaw = flat.dominant_class ?? "";
    const dominantClass: LandUseClass =
      (capitalise(dominantRaw) as LandUseClass) in confidences
        ? (capitalise(dominantRaw) as LandUseClass)
        : (Object.entries(confidences).sort((a, b) => b[1] - a[1])[0]?.[0] as LandUseClass) ?? "Commercial";

    // Max confidence from the normalised map
    const confidence = Math.max(...Object.values(confidences));

    // Backend centroid is [lat, lng] — we need [lng, lat]
    const centroid: [number, number] = flat.centroid
      ? [flat.centroid[1], flat.centroid[0]]
      : centroidOf(geometry);

    const satThumb = flat.satellite_thumbnail_url ?? "";

    return {
      id: String(flat.cell_id),
      row: 0,
      col: 0,
      class: dominantClass,
      confidence,
      confidences,
      top5_poi: flat.poi_top_categories ?? [],
      road_density: flat.road_density ?? 0,
      node_count: flat.node_count ?? 0,
      degree_centrality: flat.degree_centrality ?? 0,
      clustering_coeff: flat.clustering_coeff ?? 0,
      total_road_length_m: flat.total_road_length_m ?? 0,
      graph_embedding_norm: flat.graph_embedding_norm ?? 0,
      text_embedding_norm: flat.text_embedding_norm ?? 0,
      satellite_thumb: satThumb,
      gridId: extractGridIdFromThumbnail(satThumb) ?? "",
      geometry: geometry as CellDatum["geometry"],
      centroid,
    };
  }

  // -------------------------------------------------------------------------
  // Wrapped shape — fields inside feature.properties (legacy / mock / real backend)
  // -------------------------------------------------------------------------
  const p = (f as ClassificationFeature).properties as Record<string, unknown>;
  const confidences = normaliseConfidences(p.confidences as unknown as Record<string, number>);
  const confidence = Math.max(...Object.values(confidences));

  // Backend may use "dominant_class" (real) or "class" (legacy mock)
  const rawClass = (p.class ?? p.dominant_class ?? "") as string;
  const safeClass: LandUseClass =
    (capitalise(rawClass) as LandUseClass) in confidences
      ? (capitalise(rawClass) as LandUseClass)
      : (Object.entries(confidences).sort((a, b) => b[1] - a[1])[0]?.[0] as LandUseClass) ?? "Commercial";

  // Backend may use "satellite_thumbnail_url" (real) or "satellite_thumb" (legacy mock)
  const satThumb = (p.satellite_thumbnail_url ?? p.satellite_thumb ?? "") as string;

  // Backend may use "poi_top_categories" (real) or "top_poi" (legacy mock)
  const topPoi = (p.poi_top_categories ?? p.top_poi ?? []) as string[];

  if (import.meta.env.DEV) {
    console.log("[featureToCell] wrapped shape — class:", p.class, "dominant_class:", p.dominant_class, "normalised:", safeClass, "cell_id:", p.cell_id);
  }

  return {
    id: String(p.cell_id),
    row: 0,
    col: 0,
    class: safeClass,
    confidence,
    confidences,
    top5_poi: topPoi,
    road_density: (p.road_density ?? 0) as number,
    node_count: (p.node_count ?? 0) as number,
    degree_centrality: (p.degree_centrality ?? 0) as number,
    clustering_coeff: (p.clustering_coeff ?? 0) as number,
    total_road_length_m: (p.total_road_length_m ?? 0) as number,
    graph_embedding_norm: (p.graph_embedding_norm ?? 0) as number,
    text_embedding_norm: (p.text_embedding_norm ?? 0) as number,
    satellite_thumb: satThumb,
    gridId: extractGridIdFromThumbnail(satThumb) ?? "",
    geometry: geometry as CellDatum["geometry"],
    centroid: centroidOf(geometry),
  };
}