# Remaining Issues Root Cause Analysis

## DEF-007 — Large Area Validation Not Triggering

| Field | Value |
|-------|-------|
| **Affected files** | `app/interfaces/api.py` (load_area endpoint) |
| **Root cause** | Grid is generated via `generate_grid()` BEFORE cell count is checked. For very large bboxes, grid generation creates thousands of cells, consuming memory/time before the 413 rejection. |
| **Impact** | Large requests timeout instead of returning HTTP 413 immediately |
| **Current behavior** | `generate_grid()` is called on line 95, THEN `num_cells > 500` is checked on line 99. Timeout occurs during grid generation. |
| **Expected behavior** | Estimate cell count BEFORE calling `generate_grid()`. Reject with 413 if > 500 cells. |
| **Proposed fix** | Calculate `ceil((max_x-min_x)/cell_size) * ceil((max_y-min_y)/cell_size)` before grid generation. Early exit if > 500. |

## DEF-008 — Invalid Grid ID Accepted

| Field | Value |
|-------|-------|
| **Affected files** | `app/interfaces/api.py` (classify endpoint at line 220) |
| **Root cause** | `classify_grid()` creates a job and queues it without verifying the grid_id exists. |
| **Impact** | Invalid grid IDs (`"fake_grid"`) return 202 Accepted, then fail silently in Celery worker |
| **Current behavior** | No `get_grid()` check before `create_job()` + `apply_async()` |
| **Expected behavior** | Check `job_store.get_grid(grid_id)` and return 404 if not found |
| **Proposed fix** | Add `job_store.get_grid(request.grid_id)` check at the start of `classify_grid()`. |

## DEF-009 — Empty Modalities Validation Missing

| Field | Value |
|-------|-------|
| **Affected files** | `app/interfaces/api.py` (load_area endpoint) |
| **Root cause** | `load_area()` accepts `modalities: []` without validation. Only `classify_grid()` validates. |
| **Impact** | Empty modalities list passes through to Celery task, causing unnecessary work |
| **Current behavior** | No check for empty modalities in `load_area()` |
| **Expected behavior** | Reject `{"modalities": []}` with HTTP 400 |
| **Proposed fix** | Add `if not request.modalities:` check in `load_area()`. |

## DEF-010 — DELETE Job Endpoint Inconsistent

| Field | Value |
|-------|-------|
| **Affected files** | `app/interfaces/api.py` (lines 347-376) |
| **Root cause** | The endpoint exists at `DELETE /api/v1/jobs/{job_id}` and returns 404/200 correctly, but test coverage is missing. Path conflicts or deployment mismatch may cause 405. |
| **Impact** | Some test runs return 405 Method Not Allowed |
| **Current behavior** | Delete exists; returns 404 for missing job, 200 for deleted job |
| **Expected behavior** | Always available, proper status codes |
| **Proposed fix** | Add regression tests to verify endpoint availability and behavior. |

## DEF-011 — MLLM Training Validation Not Active

| Field | Value |
|-------|-------|
| **Affected files** | `app/interfaces/api.py` (train_mllm endpoint, lines 491-546), `app/application/mllm_use_case.py` |
| **Root cause** | Validation exists in API layer but missing from use case layer |
| **Impact** | Invalid datasets (nonexistent.csv, dataset.graphml) create Celery jobs |
| **Current behavior** | API validates path exists, extension, epochs/batch_size range. Use Case layer does NOT validate. |
| **Expected behavior** | Both API and service layers validate before queueing |
| **Proposed fix** | Add validation to `mllm_use_case.py` and strengthen API validation. |

## DEF-012 — Evaluation Endpoint Broken

| Field | Value |
|-------|-------|
| **Affected files** | `app/application/evaluation_service.py` (line 21) |
| **Root cause** | `PRED_LABEL_CANDIDATES` list is missing `"dominant_class"`, which is the actual prediction column name output by the classification pipeline. |
| **Impact** | Evaluation fails with "Could not detect prediction label column" |
| **Current behavior** | The evaluator looks for `predicted_label`, `prediction`, `pred_label`, `class`, `label`, `land_use`, `landuse`, `category`. But the classification result uses `dominant_class`. |
| **Expected behavior** | Evaluator should find `dominant_class` in classification results |
| **Proposed fix** | Add `"dominant_class"` to `PRED_LABEL_CANDIDATES`. |

## DEF-013 — num_cells Data Integrity Issue

| Field | Value |
|-------|-------|
| **Affected files** | `app/interfaces/api.py` (area-status endpoint), `app/infrastructure/job_store.py` |
| **Root cause** | num_cells is stored in Redis/memory but can be 0 when Redis returns stale data or memory fallback has initial value. The Grid SQLite table has the correct num_cells but `get_area_status()` doesn't query it. |
| **Impact** | Area status returns `num_cells: 0` while grid actually has 25+ cells |
| **Current behavior** | `get_area_status()` returns `job.get("num_cells", 0)` from job store |
| **Expected behavior** | Return actual cell count from Grid SQLite table for completed jobs |
| **Proposed fix** | When status is "completed", query Grid SQLite table for num_cells as authoritative source. |

## DEF-014 — Road Density Calculation Invalid

| Field | Value |
|-------|-------|
| **Affected files** | `app/application/fusion_service.py` (lines 328-343) |
| **Root cause** | `cell_info["geometry"].area` on EPSG:4326 geometries returns area in square degrees, NOT square meters. Values like 802693272762 appear when dividing road length (meters) by degrees^2. |
| **Impact** | Road density values are astronomically incorrect |
| **Current behavior** | Area calculated from unprojected WGS84 geometry |
| **Expected behavior** | Convert geometry to projected CRS (EPSG:3857 or UTM) before area calculation |
| **Proposed fix** | Project geometry to EPSG:3857 (Web Mercator) before calling `.area`. Use `geometry.to_crs("EPSG:3857").area` for correct square meters. |
