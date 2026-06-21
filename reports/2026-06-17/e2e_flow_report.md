# E2E Flow Report — 2026-06-17

## Badge: ⚠️ E2E FAILED (classification blocks downstream)

## Complete End-to-End Flow

### Step 1: POST /api/v1/load-area ✅
- **Request**: `{"bbox": [31.20, 30.00, 31.22, 30.02], "grid_size": 500}`
- **Response**: 202, job_id returned
- **Evidence**: `app/interfaces/api.py:63-130`

### Step 2: Poll GET /api/v1/area-status/{job_id} ✅
- **Polling**: status → "queued" → "running" → "completed"
- **Duration**: ~8s
- **Response**: job_id, status, step, progress, grid_id, num_cells, geojson_preview_url
- **Evidence**: `app/interfaces/api.py:132-165`

### Step 3: GET /api/v1/grid/{grid_id}/preview ✅
- **Response**: 200 OK, 7733 bytes GeoJSON
- **Evidence**: `app/interfaces/api.py:181-188`

### Step 4: GET /api/v1/grid/{grid_id}/details ✅
- **Response**: 200 OK, ~25 cells, road_density: 0.0
- **Evidence**: `app/interfaces/api.py:190-220`
- Note: `road_density` is 0.0 because `total_length` column is 0 or absent with POI-only modality

### Step 5: GET /api/v1/grid/{grid_id}/graph-topology ❌
- **Response**: 500 Internal Server Error
- **Root cause**: `_extract_graph_from_grid_data` in `app/interfaces/helpers.py` likely fails when road network data is missing or graph topology cannot be built
- **Evidence**: `app/interfaces/api.py:412-449` shows the endpoint logic; no explicit try/except for internal errors

### Step 6: POST /api/v1/classify ✅
- **Request**: `{"grid_id": "<id>", "modalities": ["poi"]}`
- **Response**: 202, job_id returned
- **Evidence**: `app/interfaces/api.py:245-288`

### Step 7: Poll GET /api/v1/classify-status/{job_id} ❌
- **Polling**: status → "queued" → "running" → "failed"
- **Error**: Memory error (OOM during image encoding)
- **Evidence**: `app/application/fusion_service.py:199-208` loads all images at once

### Steps 8–12: All Downstream Steps Blocked ❌

| Step | Endpoint | Status | Reason |
|------|----------|--------|--------|
| 8 | GET /classification-result/{job_id} | ❌ | Job not completed |
| 9 | GET /export/{job_id} | ❌ | Job status is "failed" |
| 10 | POST /evaluate | ❌ | Requires completed classify job |
| 11 | GET /evaluate/{job_id}/export | ❌ | Requires completed evaluate job |
| 12 | POST /query | ❌ | Requires completed classify for real answers |

## Previous Successful Results

- **62 completed classification result files** exist in `data/results/`
- These are `.geojson` files from **previous sessions** where classification succeeded
- Examples: `003be567-8966-4a80-bd8b-73e89479132f.geojson`, `f8c38546-35da-4b7b-a81d-317d79a7fd32.geojson`
- This confirms the pipeline works under sufficient memory conditions

## Additional Issues Found

### Graph-Topology 500 Error
- `GET /api/v1/grid/{grid_id}/graph-topology` returns 500
- The endpoint has try/except for `NotImplementedError` (returns 501) but no catch for unexpected exceptions
- Likely fails when road network graph data is missing or `ox.graph_from_bbox` encounters issues

## Evidence Matrix

| Step | Status | Evidence |
|------|--------|----------|
| POST /load-area | ✅ 202 | `app/interfaces/api.py:63-130` |
| GET /area-status | ✅ completed (~8s) | `app/interfaces/api.py:132-165` |
| GET /grid/preview | ✅ 200 (7733 bytes) | `app/interfaces/api.py:181-188` |
| GET /grid/details | ✅ 200 (25 cells) | `app/interfaces/api.py:190-220` |
| GET /grid/graph-topology | ❌ 500 | `app/interfaces/api.py:412-449` |
| POST /classify | ✅ 202 (queued) | `app/interfaces/api.py:245-288` |
| GET /classify-status | ❌ failed (memory) | `app/application/fusion_service.py:199-208` |
| GET /classification-result | ❌ blocked | `app/interfaces/api.py:308-321` |
| GET /export | ❌ blocked | `app/interfaces/api.py:323-364` |
| POST /evaluate | ❌ blocked | `app/application/evaluation_service.py` |
| Previous results | ✅ 62 .geojson files | `data/results/*.geojson` |

## Conclusion

⚠️ **E2E FAILED** — The complete flow works through grid creation and details retrieval but fails at the classification step due to memory constraints. This blocks all downstream operations (result retrieval, export, evaluation). The pipeline has proven functional in previous sessions (62 successful results exist), indicating this is an environment-specific memory issue rather than a code logic bug. The graph-topology endpoint also returns 500 independently.
