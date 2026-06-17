# Urban AI Dashboard — Full System Audit Report

**Date:** 2026-06-17  
**Auditor:** Automated QA Pipeline  
**System:** MLLM-Geo-AI — Multi-Modal Land Use Classification  
**Environment:** Windows 11, Python 3.13, Redis 7, Celery 5.3

---

## Executive Summary

| Component | Score | Status |
|-----------|-------|--------|
| Infrastructure | 65/100 | Functional with gaps |
| Backend API | 70/100 | Most endpoints work, some performance issues |
| AI Pipeline | 45/100 | Classification runs but has silent failures |
| Data Layer | 60/100 | Grid data persists, results have inconsistencies |
| Frontend | Not tested | Requires browser-based validation |

**Overall Health Score: 60/100**

### Critical Issues Found
1. **Classification pipeline swallows errors** — Exceptions caught internally, status set to "failed", then overwritten to "completed"
2. **Job `num_cells` always shows 0** — `area-status` returns `num_cells: 0` despite grid having 25 cells
3. **All results show `node_count: 0`** — Road network graph features not being loaded properly
4. **High endpoint latency** — All endpoints take ~2s; graph-topology takes 45s
5. **`jobs` table empty** — Jobs stored only in Redis/in-memory; no SQLite persistence
6. **Orphan grid file** — `grid_78d2bf6b.geojson` exists on disk with no DB record
7. **Server crash on grid/preview** — Grid preview endpoint causes connection reset under load

---

## Infrastructure Report

### Docker
| Container | Status | Ports | Notes |
|-----------|--------|-------|-------|
| `mllm-geo-redis` | Up (healthy) | 6379 | Redis 7-alpine |
| `urban-redis` | Created (not running) | - | Duplicate container |

### Redis
| Metric | Value |
|--------|-------|
| Version | 7.4.9 |
| Status | Healthy (`PING → True`) |
| Connected clients | 26 |
| Memory used | 1.82 MB |
| Uptime | ~1 hour |

### Celery
| Metric | Value |
|--------|-------|
| Broker | `redis://localhost:6379/0` |
| Registered tasks | `load_area_task`, `classify_task`, `train_mllm_task` |
| Concurrency | solo (12 threads) |
| Queues | `celery`, `cpu`, `gpu` |
| Status | Worker connected successfully |

### Databases
| Database | Records | Notes |
|----------|---------|-------|
| SQLite (mllm_geo_ai.db) | 18 grids, 0 jobs | Jobs table exists but empty |
| Redis | Jobs stored in-memory | Used as primary job store |

### Models
| Model | Path | Size |
|-------|------|------|
| `random_forest.pkl` | `models/` | 47 KB |
| `urban_mlp.pt` | `models/` | 334 KB |
| `paraphrase-multilingual-MiniLM-L12-v2` | `models/sentence_transformer/` | Present |

### Caches
| Cache | Path | Status |
|-------|------|--------|
| Grid GeoJSON files | `data/grids/` | 19 files present |
| Satellite images | `data/sat_images/` | Empty |
| Road network | `data/raw/roads.graphml` | Not checked |
| Raw POI data | `data/raw/` | Empty |
| Classification results | `data/results/` | 11 GeoJSON files |

---

## Endpoint Audit Table

| # | Method | Endpoint | Status | Response Time | Notes |
|---|--------|----------|--------|--------------|-------|
| 1 | GET | `/health` | ✅ PASS | 2.04s | Slow for a health check |
| 2 | POST | `/api/v1/load-area` | ✅ PASS | <1s (async) | Returns 202 with job_id |
| 3 | GET | `/api/v1/area-status/{job_id}` | ✅ PASS | 2.01s | Returns correct status; `num_cells: 0` bug |
| 4 | GET | `/api/v1/grid/{grid_id}/details` | ✅ PASS | 2.69s | Returns correct grid metadata |
| 5 | GET | `/api/v1/grid/{grid_id}/preview` | ⚠️ WARN | Variable | Works for small grids; crashes on repeated calls |
| 6 | GET | `/api/v1/grid/{grid_id}/pois` | ✅ PASS | 2.01s | Returns empty list when no modalities |
| 7 | POST | `/api/v1/classify` | ✅ PASS | 2.01s | Returns 202 with job_id |
| 8 | GET | `/api/v1/classify-status/{job_id}` | ⚠️ WARN | 2.01s | Returns "completed" even with errors |
| 9 | GET | `/api/v1/classification-result/{job_id}` | ✅ PASS | 2.01s | Returns GeoJSON with features |
| 10 | GET | `/api/v1/export/{job_id}?format=geojson` | ❌ FAIL | 2.01s | Returns 404 when result file missing |
| 11 | GET | `/api/v1/export/{job_id}?format=csv` | ❌ FAIL | - | Returns 404 |
| 12 | GET | `/api/v1/export/{job_id}?format=shapefile` | ❌ FAIL | - | Not tested (requires 404 or error) |
| 13 | DELETE | `/api/v1/jobs/{job_id}` | ✅ PASS | 2.30s | Returns 200 with "cancelled" status |
| 14 | GET | `/api/v1/grid/{grid_id}/graph-topology` | ✅ PASS | 44.96s | Very slow for small grid (25 cells) |
| 15 | POST | `/api/v1/evaluate` | ⚠️ WARN | - | Needs further testing with proper payload |
| 16 | GET | `/api/v1/evaluate/{job_id}/export` | ⚠️ WARN | - | Needs testing with completed eval |
| 17 | POST | `/api/v1/mllm/train` | ⚠️ WARN | - | Async; not fully tested |
| 18 | GET | `/api/v1/mllm/train-status/{job_id}` | ✅ PASS | - | Returns job status |
| 19 | POST | `/api/v1/query` | ⚠️ WARN | - | Returns stub answer; grid lookup fails if not cached |
| 20 | WS | `/api/v1/ws/progress/{job_id}` | ⚠️ WARN | - | WebSocket exists; not functionally tested |

### Negative Test Results
| Test | Path | Status | Expected | Result |
|------|------|--------|----------|--------|
| Invalid bbox | `POST /load-area` | 422 | 422 | ✅ Correct validation |
| Non-existent job | `GET /area-status/invalid` | 404 | 404 | ✅ Correct |
| Non-existent grid | `GET /grid/invalid/details` | 404 | 404 | ✅ Correct |
| Wrong method | `GET /jobs/invalid` | 405 | 405 | ✅ Correct (should be DELETE) |
| Empty classify | `POST /classify {}` | 422 | 422 | ✅ Correct |
| Non-existent status | `GET /classify-status/invalid` | 404 | 404 | ✅ Correct |

---

## Detailed Findings

### 1. 🔴 CRITICAL: Classification Pipeline Error Swallowing

**Location:** `app/application/fusion_service.py:447-456`  
**Description:** The `execute()` method catches all exceptions and sets job status to "failed" but does NOT re-raise. The calling code in `tasks/classify.py:27` then overwrites status to "completed".

**Evidence:**
```json
GET /api/v1/classify-status/{job_id} → {
  "status": "completed",
  "step": "done",
  "progress": 1.0,
  "error": "all input arrays must have the same shape"
}
```

**Impact:** Failed classifications are reported as successful. Error message is silently stored but the user sees "completed".

**Recommended Fix:** Add `raise` after `update_job` in the except block of `execute()`, or check return value.

### 2. 🔴 HIGH: All Features Show Zero Values

**Evidence from 11 result files:**
- `road_density_km_per_km2: 0.0`
- `node_count: 0`
- `poi_top_categories: []`
- `text_embedding_norm: 0.0`
- `graph_embedding_norm: 0.0`

**Root Cause:** When modalities are `[]` (empty), no POI, image, or graph data is loaded. The classification runs on zero-filled features, producing random predictions (~0.33 confidence each).

**Impact:** Predictions are meaningless when modalities are empty. The system should validate and reject empty modalities for classification.

### 3. 🔴 HIGH: `num_cells` Field Returns Zero

**Location:** `app/interfaces/api.py:136` and `app/infrastructure/job_store.py`

**Evidence:**
```json
GET /api/v1/area-status/{job_id} → {"num_cells": 0, ...}
```
But grid details correctly shows: `{"cell_count": 25}`

**Root Cause:** `num_cells` is passed to `update_job()` during the "completed" call, but the Redis job store may not persist it correctly. The `create_job()` method doesn't initialize `num_cells`.

### 4. 🟡 MEDIUM: High Latency on All Endpoints

| Endpoint | Avg Response Time | Expected |
|----------|-------------------|----------|
| `/health` | 2.04s | < 200ms |
| `/area-status` | 2.01s | < 500ms |
| `/grid/details` | 2.69s | < 500ms |
| `/grid/preview` | 2.01s | < 1s |
| `/grid/pois` | 2.01s | < 500ms |
| `/classify-status` | 2.01s | < 500ms |
| `/graph-topology` | 44.96s | < 5s |

**Root Cause:** All endpoints use `async def` handlers but call synchronous I/O (geopandas, SQLAlchemy) without `run_in_executor`, blocking the event loop.

### 5. 🟡 MEDIUM: Orphan Grid File

**Evidence:** `grid_78d2bf6b.geojson` exists on disk (in `data/grids/`) but has no corresponding record in the SQLite `grids` table.

### 6. 🟡 MEDIUM: Jobs Not Persisted in SQLite

**Evidence:** The `jobs` table exists in SQLite but has 0 rows. All job data is stored in Redis and in-memory dictionary only.

**Impact:** Server restart loses all job state. No historical job tracking.

### 7. 🟢 LOW: GET on DELETE Endpoint Returns 405

**Path:** `GET /api/v1/jobs/{job_id}` returns 405 Method Not Allowed  
**Expected behavior:** Should return 405 or 404 — correct behavior. The audit script used wrong HTTP method.

### 8. 🟢 LOW: Export Returns 404

**Path:** `GET /api/v1/export/{job_id}?format=geojson`  
**Result:** 404 — "Job not found or not completed"  
**Cause:** The classification job completed with error status, so the result file `data/results/{job_id}.geojson` may not have been created, or the job lookup fails.

---

## Performance Report

### Latency Metrics
```
Health Check:          2.04s  (baseline)
Area Status:           2.01s
Grid Details:          2.69s
Grid Preview:          2.01s
Grid POIs:             2.01s
Classify Status:       2.01s
Cancel Job:            2.30s
Graph Topology:       44.96s  ★ BOTTLENECK
Invalid Payload:       2.26s
```

### Identified Bottlenecks
1. **GeoPandas file loading** — `gpd.read_file()` takes ~0.8s per call, called on every grid endpoint request
2. **OSMnx graph processing** — Graph topology endpoint takes 45s due to OSMnx graph operations
3. **No caching** — Grid data loaded from disk on every request; no in-memory cache
4. **Event loop blocking** — Synchronous I/O in async handlers blocks all concurrent requests

---

## Security Findings

| Severity | Finding | Status |
|----------|---------|--------|
| LOW | Invalid IDs return 404 (safe) | ✅ No information leak |
| LOW | SQL injection not tested | ⚠️ Requires dedicated test |
| LOW | No authentication on any endpoint | ⚠️ Intended for demo |
| LOW | Large payload not tested | ⚠️ Boundary test needed |
| LOW | Path traversal not tested | ⚠️ Requires dedicated test |

No critical security vulnerabilities found in basic testing.

---

## Database Audit

### Grids Table (18 rows)
| Column | Status |
|--------|--------|
| id | 18 unique IDs, no duplicates |
| bbox | All valid JSON arrays |
| grid_size_m | All 500m |
| num_cells | Ranges from 25 to 288 |
| status | All "completed" |
| created_at | Valid timestamps |

### File Storage Audit
| Location | Files | Missing DB Entries | Orphan Files |
|----------|-------|-------------------|--------------|
| `data/grids/` | 19 .geojson | 0 | `grid_78d2bf6b` (1 orphan) |
| `data/results/` | 11 .geojson | N/A | N/A |
| `data/sat_images/` | 0 | N/A | N/A |

---

## PRD Compliance Matrix

| Requirement | Status | Notes |
|-------------|--------|-------|
| FR-01: Health endpoint | ✅ PASS | Returns status, Redis check |
| FR-02: Load area | ✅ PASS | Accepts bbox, returns job_id |
| FR-03: Area status | ✅ PASS | Polling works |
| FR-04: Grid details | ✅ PASS | Returns metadata |
| FR-05: Grid preview | ⚠️ PARTIAL | Works but may crash server |
| FR-06: Grid POIs | ✅ PASS | Returns POI list |
| FR-07: Classification | ⚠️ PARTIAL | Runs but errors are swallowed |
| FR-08: Classify status | ⚠️ PARTIAL | Reports "completed" despite errors |
| FR-09: Classification result | ✅ PASS | Returns GeoJSON |
| FR-10: Export | ❌ FAIL | Returns 404 for completed jobs |
| FR-11: Cancel job | ✅ PASS | Works correctly |
| FR-12: Graph topology | ✅ PASS | Works but very slow |
| FR-13: Evaluate | ⚠️ PARTIAL | Needs validation with proper ground truth |
| FR-14: Evaluate export | ⚠️ PARTIAL | Needs testing |
| FR-15: MLLM Train | ⚠️ PARTIAL | Async endpoint exists |
| FR-16: NL Query | ⚠️ PARTIAL | Returns stub answer only |
| FR-17: WebSocket progress | ⚠️ PARTIAL | Endpoint exists, not functionally verified |

---

## Defect Log

### DEF-001: Classification Error Swallowing
- **Severity:** Critical
- **Location:** `fusion_service.py:447-456` / `tasks/classify.py:17-28`
- **Steps:**
  1. POST /api/v1/classify with any grid_id
  2. Poll classify-status until "completed"
  3. Note: error field contains "all input arrays must have the same shape"
  4. But status is "completed", not "failed"
- **Expected:** Status should be "failed" when classification pipeline errors
- **Actual:** Status is "completed" despite an error message
- **Root Cause:** `execute()` catches exception, sets "failed", but does not re-raise. Calling code overwrites to "completed".
- **Fix:** Add `raise` after `job_store.update_job(status="failed")` in `execute()`.

### DEF-002: `num_cells` Returns Zero
- **Severity:** High
- **Location:** `app/infrastructure/job_store.py:28-42`
- **Steps:**
  1. POST /api/v1/load-area (valid)
  2. Poll area-status until completed
  3. Check `num_cells` field — shows 0
  4. But GET /grid/{id}/details shows correct cell_count
- **Expected:** `num_cells` should reflect actual cell count (25)
- **Actual:** Always 0
- **Root Cause:** `num_cells` not initialized in `create_job()`. Redis store may not persist `**kwargs` fields correctly.
- **Fix:** Initialize `num_cells: 0` in `create_job()` or read from grid data.

### DEF-003: All Graph Features Zero
- **Severity:** High
- **Location:** Multiple
- **Steps:**
  1. POST /api/v1/load-area with modalities ["poi","image","graph"]
  2. Run classification
  3. Check results — all `node_count: 0`, `road_density: 0.0`
- **Expected:** Non-zero graph features if road network data exists
- **Actual:** All zero — predictions are random
- **Root Cause:** The road network download may fail silently or grid cells don't contain roads. Need to investigate task execution.
- **Fix:** Validate feature extraction against expected ranges.

### DEF-004: High Endpoint Latency
- **Severity:** Medium
- **Location:** All API endpoints
- **Steps:** Time any endpoint — all take ~2s
- **Expected:** <500ms for read operations
- **Actual:** 2s+ for all endpoints; 45s for graph-topology
- **Root Cause:** Synchronous I/O (geopandas, SQLAlchemy) in async handlers without `run_in_executor`. Event loop blocked.
- **Fix:** Move synchronous calls to thread pool, add caching.

### DEF-005: Orphan Grid File
- **Severity:** Low
- **Location:** `data/grids/grid_78d2bf6b.geojson`
- **Steps:** List grid files and compare to DB records
- **Expected:** Every file has a DB record
- **Actual:** One file (`grid_78d2bf6b`) has no DB record
- **Fix:** Clean up orphan file or add DB migration.

### DEF-006: Export Returns 404
- **Severity:** Medium
- **Location:** `app/interfaces/api.py:284-314`
- **Steps:**
  1. Run classification
  2. Wait for "completed"
  3. GET /api/v1/export/{job_id}?format=geojson
- **Expected:** Returns GeoJSON file
- **Actual:** 404 Not Found
- **Root Cause:** Result file may not exist if classification had error (see DEF-001). The endpoint checks job status but not actual file existence in some cases.
- **Fix:** Ensure result file is written before setting status to "completed".

---

## Final Verdict

# NOT READY

The system has fundamental issues that prevent production or academic defense use:

1. **Classification results are unreliable** — Errors are silently swallowed, features are all zeros, predictions are random
2. **Export is broken** — Returns 404 for jobs reported as "completed"
3. **Performance is poor** — All endpoints take 2s+; graph-topology takes 45s
4. **Data persistence gaps** — Jobs not persisted in SQLite, orphan files, missing fields

### Recommendation
Address all Critical and High severity defects before the next audit. Priority order:
1. Fix DEF-001: Classification error propagation
2. Fix DEF-002: num_cells field
3. Fix DEF-003: Feature extraction validation
4. Fix DEF-004: Performance optimization (caching + async)
5. Fix DEF-006: Export endpoint
6. Add input validation for empty modalities to prevent meaningless classifications

---

## Appendix A: Test Commands Used

```bash
# Health check
curl -s http://localhost:8000/health

# Load area
curl -s -X POST http://localhost:8000/api/v1/load-area \
  -H "Content-Type: application/json" \
  -d '{"bbox":[31.20,30.00,31.22,30.02],"grid_size":500,"modalities":[]}'

# Poll area status
curl -s http://localhost:8000/api/v1/area-status/{job_id}

# Grid details
curl -s http://localhost:8000/api/v1/grid/{grid_id}/details

# Grid preview
curl -s http://localhost:8000/api/v1/grid/{grid_id}/preview

# Grid POIs
curl -s http://localhost:8000/api/v1/grid/{grid_id}/pois

# Classify
curl -s -X POST http://localhost:8000/api/v1/classify \
  -H "Content-Type: application/json" \
  -d '{"grid_id":"{grid_id}","modalities":[]}'

# Classify status
curl -s http://localhost:8000/api/v1/classify-status/{job_id}

# Classification result
curl -s http://localhost:8000/api/v1/classification-result/{job_id}

# Export
curl -s http://localhost:8000/api/v1/export/{job_id}?format=geojson

# Cancel job
curl -s -X DELETE http://localhost:8000/api/v1/jobs/{job_id}

# Graph topology
curl -s "http://localhost:8000/api/v1/grid/{grid_id}/graph-topology?max_nodes=500&simplify=true"

# Evaluate
curl -s -X POST http://localhost:8000/api/v1/evaluate \
  -F "job_id={job_id}" \
  -F "ground_truth_file=@truth.csv"

# NL Query
curl -s -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the land use?","grid_id":"{grid_id}"}'

# Invalid tests
curl -s -X POST http://localhost:8000/api/v1/load-area \
  -H "Content-Type: application/json" \
  -d '{"bbox":"invalid"}'
curl -s http://localhost:8000/api/v1/jobs/invalid_job_id
```

## Appendix B: Environment Details

| Component | Value |
|-----------|-------|
| OS | Windows 11, Version 10.0.26200 |
| Python | 3.13.3 |
| FastAPI | 0.135.2 |
| Uvicorn | 0.42.0 |
| Celery | 5.3.6 |
| Redis | 7.4.9 (Docker) |
| SQLite | 3.x (via SQLAlchemy) |
| GeoPandas | Latest |
| OSMnx | Latest |

---

*Report generated automatically by the Urban AI Dashboard Audit Pipeline.*
*For questions, contact the development team.*
