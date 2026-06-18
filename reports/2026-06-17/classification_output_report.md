# Classification Output Report | Date: 2026-06-17 | MLLM-Geo-AI Project

## 1. Output Schema Verification

Required fields per PRD v3.0:

| Field | Present | Type | Notes |
|-------|---------|------|-------|
| grid_id (cell_id) | ✅ YES | int | Named cell_id in output |
| dominant_class | ✅ YES | str | Residential/Commercial/Industrial |
| confidence | ✅ YES | float | From softmax output |
| geometry | ✅ YES | GeoJSON | __geo_interface__ format |
| road_density | ✅ YES | float | km/km² (projected CRS) |
| node_count | ✅ YES | int | Road network nodes |
| confidences | ✅ YES | dict | Per-class probabilities |
| poi_top_categories | ✅ YES | list | Top 3 from text |
| satellite_thumbnail_url | ✅ YES | str | URL to JPEG thumbnail |
| text_embedding_norm | ✅ YES | float | Added in this version |
| graph_embedding_norm | ✅ YES | float | Added in this version |
| degree_centrality | ✅ YES | float | Defaults to 0.0 |
| clustering_coeff | ✅ YES | float | Defaults to 0.0 |
| centroid | ✅ YES | tuple | (lat, lng) |

## 2. Field Validation

| Check | Status |
|-------|--------|
| dominant_class not null | ✅ Handled (always set from argmax) |
| confidence in [0,1] | ✅ Softmax output guarantees this |
| geometry valid GeoJSON | ✅ Uses __geo_interface__ |
| road_density >= 0 | ✅ Handled (defaults to 0.0) |

## 3. Issues Found

1. **degree_centrality and clustering_coeff** are hardcoded to 0.0 (fusion_service.py:401-403) — not computed from actual graph data.
2. **text_embedding_norm** and **graph_embedding_norm** are computed correctly now (fixed from earlier KeyError bug).
3. **road_density** calculation uses projected CRS correctly.

## 4. Evidence Matrix

| Item | Code Verified | Runtime Verified | Evidence Attached |
|------|:-------------:|:----------------:|:-----------------:|
| Schema Completeness | YES | PARTIAL | YES |
| Field Validation | YES | YES | YES |
| Classification Result | YES | NO | NO |
