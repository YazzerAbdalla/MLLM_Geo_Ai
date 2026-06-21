# Spatial Validation Report

**Date:** 2026-06-17
**Project:** MLLM-Geo-AI

## Coordinate Reference System

| Property           | Value       |
|--------------------|-------------|
| CRS                | EPSG:4326 (WGS84) |
| Used throughout    | Grid generation, spatial joins, POI queries |
| Projected CRS      | ❌ **Not used** — area calculations use geographic coordinates |

## Area Calculation Concern

The grid generation code in `app/domain/spatial_service.py` converts grid size from meters to degrees using:

```python
cell_size = cell_size_m / 111000.0
```

This is an approximation valid only at the equator. At latitude 30°N (Cairo region), the actual degree-to-meter conversion factor for longitude is approximately 96,486 m/deg (111,320 * cos(30°)). This introduces ~15% error in longitudinal cell dimensions.

**Impact:** Grid cells in the Cairo region are not truly square in projected units; they are wider in the east-west direction than intended.

## Grid Generation

| Parameter       | Value             |
|-----------------|-------------------|
| Bounding box    | `[31.20, 30.00, 31.22, 30.02]` |
| Grid size       | 500m              |
| Cell size (deg) | 500 / 111000.0 ≈ 0.0045045° |
| Columns         | ceil(0.02 / 0.0045045) = 5 |
| Rows            | ceil(0.02 / 0.0045045) = 5 |
| **Total cells** | **25** ✅ (matches expectations) |

## Road Network

| Property         | Value                               |
|------------------|-------------------------------------|
| File             | `data/raw/roads.graphml`           |
| Size             | 584,632,898 bytes (~584MB)          |
| Format           | GraphML (XML-based)                 |
| CRS              | EPSG:4326                           |
| Assessment       | Very large file — causes 13.5s timeout + 500 error on graph-topology endpoint |

Road density is calculated from the `total_length` column in each grid GeoJSON file stored in `data/grids/`.

## Spatial Accuracy Assessment

| Criteria                    | Status | Notes                                      |
|-----------------------------|--------|--------------------------------------------|
| CRS consistency             | ✅     | EPSG:4326 used everywhere                  |
| Grid cell count             | ✅     | 25 cells for 0.02°×0.02° at 500m          |
| Degree-to-meter conversion  | ⚠️     | Approximate (111000.0); not latitude-corrected |
| Projected CRS for area      | ❌     | No UTM or other projected CRS used         |
| Road network loading        | ❌     | 584MB file causes endpoint failure         |
| Demo suitability            | ✅     | Acceptable for demonstration purposes      |

## Recommendation

For production use, implement a projected CRS (e.g., UTM zone 36N for Cairo) for area calculations. Replace the constant `111000.0` with a latitude-aware Haversine-based conversion or reproject the grid to a local UTM CRS before computing cell sizes.

## Evidence Matrix

| Evidence File                                  | Content                                      |
|------------------------------------------------|----------------------------------------------|
| `app/domain/spatial_service.py:16-23`          | `generate_grid()` with 111000.0 conversion   |
| `data/grids/grid_*.geojson`                    | Generated grid GeoJSON files (25 cells typical) |
| `data/raw/roads.graphml`                       | 584MB road network for Cairo region          |
| `app/config.py`                                | Config with bounding box                     |
