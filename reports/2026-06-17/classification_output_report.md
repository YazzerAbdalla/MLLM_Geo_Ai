# Classification Output Report

**Date:** 2026-06-17  
**Audit scope:** Output field schema, ML pipeline output, runtime classification behavior, existing result files

---

## Required Output Fields

| Field | Type | Description | Status |
|---|---|---|---|
| `grid_id` | string | Grid identifier (added by API layer) | ✅ |
| `dominant_class` | string | One of `"Residential"`, `"Commercial"`, `"Industrial"` | ✅ |
| `confidence` | float | Probability of the dominant class (0–1) | ✅ |
| `geometry` | GeoJSON Polygon | Cell geometry preserved from input grid | ✅ |
| `road_density` | float | Average road length per cell (may be 0 if no road data) | ✅ |

## Additional Output Fields

The model pipeline also produces:
- `cell_id` — Cell index within the grid
- `confidences` — Dict of all class probabilities (`residential`, `commercial`, `industrial`)
- `node_count`, `degree_centrality`, `clustering_coeff` — Graph metrics
- `total_road_length_m` — Total road length in meters
- `poi_top_categories` — Top POI category labels
- `text_embedding_norm`, `graph_embedding_norm` — Embedding statistics
- `centroid` — Cell centroid coordinates
- `satellite_thumbnail_url` — Link to satellite image thumbnail

## Code Verification

- ✅ Output schema defined in `app/models/result.py` (Pydantic model)
- ✅ Pipeline produces these fields in `app/application/fusion_service.py:379-421`
- ✅ Results saved as GeoJSON at `data/results/{job_id}.geojson`
- ✅ Geometry is preserved from the original grid cells (no modification)
- ✅ Dominant class and confidence computed by ML model in the classify pipeline

## Runtime Verification

| Check | Result |
|---|---|
| Classification endpoint available | ✅ `POST /api/v1/classify` |
| Output schema matches model | ✅ |
| **Classification pipeline runtime** | ❌ **FAILS with memory error** (OS paging file issue) |
| Completed result files exist from prior runs | ✅ 61 GeoJSON files in `data/results/` |

## Existing Result File Analysis

- **Total result files:** 61 GeoJSON files in `data/results/`
- **File size range:** 212 B (empty/minimal) to 65 KB (full grid with many cells)
- **Small files (~200–730 B):** Typically grids with no features (all road_density=0, all confidences uniform)
- **Medium files (~3–20 KB):** Grids with a few cells containing diverse classifications
- **Large files (~27–65 KB):** Full grids with 50+ cells, rich metadata
- **All sampled files have correct schema:** `dominant_class`, `confidence`, `road_density`, `geometry` present

### Example feature from a completed result:
```json
{
  "cell_id": 0,
  "dominant_class": "Commercial",
  "confidence": 0.3734,
  "confidences": {"residential": 0.3662, "commercial": 0.3734, "industrial": 0.2604},
  "road_density": 0.0,
  "geometry": {"type": "Polygon", "coordinates": [[...]]}
}
```

## Classification Pipeline Flow

1. Grid cells loaded from storage
2. POI/text embeddings generated via SentenceTransformer model
3. (Optional) Satellite imagery downloaded and encoded
4. (Optional) Road network graph features computed
5. Feature fusion via specified method (`concat`, `attention`, `weighted`)
6. MLP classifier predicts class probabilities per cell
7. Dominant class selected via argmax
8. Results saved to GeoJSON file
9. Job marked as completed in Redis

## Status Summary

| Check | Status |
|---|---|
| Output schema verified in code | ✅ |
| Required fields present | ✅ |
| Geometry preserved from grid cells | ✅ |
| Dominant class + confidence by ML model | ✅ |
| Classification runs successfully | ❌ (memory error) |
| Prior result files exist with correct schema | ✅ |
| For full validation, classify must succeed | ⚠️ |

## Evidence Matrix

| Item | Source | Status |
|---|---|---|
| Output schema (Pydantic) | `app/models/result.py` | ✅ |
| Pipeline output construction | `app/application/fusion_service.py:408-421` | ✅ |
| Result file save | `app/application/fusion_service.py:75` | ✅ |
| DOMINANT_CLASS field | Sampled result GeoJSON | ✅ |
| CONFIDENCE field | Sampled result GeoJSON | ✅ |
| ROAD_DENSITY field | Sampled result GeoJSON | ✅ |
| GEOMETRY field | Sampled result GeoJSON | ✅ |
| 61 prior result files exist | `data/results/` | ✅ |
| Runtime classification success | Session test | ❌ |
