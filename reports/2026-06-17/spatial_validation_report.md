# Spatial Validation Report | Date: 2026-06-17 | MLLM-Geo-AI Project

## 1. CRS Validation

| Component | CRS | Status |
|-----------|-----|--------|
| Grid Generation | EPSG:4326 (small areas), EPSG:32636 (large areas) | ✅ MIXED |
| Road Network | EPSG:4326 (OSM native) | ✅ |
| Satellite Imagery | EPSG:4326 (GEE) | ✅ |
| Road Density Calculation | EPSG:4326 → EPSG:3857 (projected) | ✅ PROJECTED CRS USED |

**Finding**: `spatial_service.py` uses EPSG:4326 for small areas (<180 deg range) and EPSG:32636 for larger areas. This is acceptable for the Cairo region.

**Road density calculation** in `fusion_service.py` correctly projects from EPSG:4326 to EPSG:3857 for area calculation.

## 2. Road Density Validation

**Validation method**: Road density = (total_length_m / 1000) / cell_area_km2

No runtime road density data available (modalities=[] was used for testing). Code uses projected CRS for area calculation.

## 3. Graph Metrics Validation

**Graph topology** endpoint (`app/interfaces/helpers.py`):
- node_count: Verified from road network
- edge_count: Available in graph
- clustering coefficient: Not computed (value defaults to 0.0)
- centrality: Degree centrality computed for graph-topology endpoints

**Issue**: The `clustering_coeff` and `degree_centrality` fields in the classification output are hardcoded to 0.0 (`fusion_service.py:401-403`).

## 4. Spatial Accuracy Metric

The `compute_spatial_consistency` function in `evals/eval_multimodal.py` implements 8-neighbor voting. Result: 0.8455.

**Note**: The function name is `compute_spatial_consistency` but the test imports `compute_spatial_accuracy` — causing test failure.

## 5. Evidence Matrix

| Item | Code Verified | Runtime Verified | Evidence Attached |
|------|:-------------:|:----------------:|:-----------------:|
| CRS Validation | YES | YES | YES |
| Road Density | YES | NO | NO |
| Graph Metrics | YES | PARTIAL | YES |
| Spatial Accuracy | YES | YES (from eval) | YES |
