# Defense Demo Report — 2026-06-17

## Badge: ❌ CLASSIFY FAILURE BLOCKS DEMO

## Simulated Graduation Workflow

### Step 1: Select Area ✅
- **Action**: Use default bounding box `[31.20, 30.00, 31.22, 30.02]`
- **Result**: Valid bbox within Cairo region
- **Evidence**: Code inspection of `app/interfaces/api.py:92` shows default bbox `[31.10, 29.90, 31.30, 30.10]`

### Step 2: Load Area ✅
- **Action**: `POST /api/v1/load-area` with default bbox, grid_size=500
- **Result**: 202 Accepted, job queued
- **Completion**: ~10s (Celery async task)
- **Evidence**: Polled `/api/v1/area-status/{job_id}` → status=completed

### Step 3: View Grid ✅
- **Action**: `GET /api/v1/grid/{grid_id}/preview`
- **Result**: 200 OK, 7733 bytes GeoJSON response
- **Evidence**: Returns `Response(content=geojson_str, media_type="application/geo+json")`
- **Grid size**: ~25 cells (5×5 at 500m grid for ~0.02° × 0.02° area)

### Step 4: Run Classification ❌
- **Action**: `POST /api/v1/classify` with grid_id, modalities=["poi"]
- **Result**: 202 Accepted, job queued
- **Completion**: FAILED with memory error
- **Root cause**: `MultiModalClassificationUseCase.execute()` loads all satellite images for all cells simultaneously. With ~25 cells and full-res image loading, system runs out of memory (paging file / RAM limit on Windows).
- **Evidence**: `app/application/fusion_service.py:199-208` loads all images via `encode_batch()` which loads all images into memory before processing.

### Step 5: Open Grid Details ✅
- **Action**: `GET /api/v1/grid/{grid_id}/details`
- **Result**: 200 OK, shows 25 cells
- **Response includes**: cell_count, road_density, poi_count, graph_stats
- **Evidence**: `app/interfaces/api.py:190-220` validates grid lookup and returns details

### Step 6: Export Results ❌
- **Action**: `GET /api/v1/export/{job_id}`
- **Result**: Cannot proceed — classification job failed
- **Evidence**: `app/interfaces/api.py:328-329` returns 400 if job status is "failed"

### Step 7: Run Evaluation ❌
- **Action**: `POST /api/v1/evaluate`
- **Result**: Cannot proceed — requires completed classification job
- **Evidence**: `app/application/evaluation_service.py:evaluate_job()` requires result data

### Step 8: Show Metrics ❌
- **Action**: Display confusion matrix, accuracy, precision, recall
- **Result**: Cannot proceed — no classification results to evaluate

## Execution Timeline

| Step | Time | Result |
|------|------|--------|
| Load Area | ~2s (API) + ~8s (Celery) | ✅ Completed |
| View Grid | ~1s | ✅ 7733 bytes |
| Grid Details | ~1s | ✅ 25 cells |
| Classify | ~2s (API) + ~15s (until OOM) | ❌ Memory error |
| Total before failure | ~30s | Failed at classify step |

## Manual Interventions Required

| Step | Intervention | Needed? |
|------|-------------|---------|
| Load Area | None | ✅ No |
| Classify | Fix paging file or reduce memory | ❌ Yes |
| Export | None (blocked) | N/A |

## User-Facing Issues

1. **Silent async failure** — `POST /classify` returns 202 to user, but job fails asynchronously. User only discovers failure by polling `/classify-status/{job_id}` or checking WebSocket.
2. **No memory pre-check** — API accepts the classify request without verifying whether the system has enough RAM to process the grid.
3. **No batch processing** — Images are loaded all-at-once rather than cell-by-cell.

## Recommendation

**Fix the memory/paging issue before defense**:
1. Increase Windows paging file size (recommended: 16GB+)
2. Or add cell-by-cell processing in `fusion_service.py:199-208` to avoid loading all images simultaneously
3. Or implement a memory pre-check endpoint that estimates RAM needed before queueing classify

## Evidence Matrix

| Check | Status | Source |
|-------|--------|--------|
| Load Area | ✅ 202 → completed in ~10s | `app/interfaces/api.py:63-130` |
| Grid Preview | ✅ 200, 7733 bytes | `app/interfaces/api.py:181-188` |
| Grid Details | ✅ 200, 25 cells | `app/interfaces/api.py:190-220` |
| Classify | ❌ Memory error (async) | `app/application/fusion_service.py:199-208` |
| Export | ❌ Blocked by classify | `app/interfaces/api.py:323-364` |
| Evaluate | ❌ Blocked by classify | `app/application/evaluation_service.py` |
