# Workflow Validation Report

**Date:** 2026-06-17  

---

## Phase 1: Environment Verification

| Component | Status | Details |
|-----------|--------|---------|
| FastAPI Server | ✅ Running | Port 8000/8001 |
| Redis | ✅ Connected | redis://localhost:6379 |
| Celery Worker | ✅ Running | 3 tasks registered |
| SQLite | ✅ Connected | 2 tables (grids, jobs) |
| Model File | ✅ Present | paraphrase-multilingual-MiniLM-L12-v2 (470MB) |
| OSM Cache | ✅ Present | roads.graphml (584MB) |
| Satellite Images | ✅ Present | 144 PNG images |

---

## Phase 2: Endpoint Discovery

- **Total endpoints discovered:** 18
- **REST endpoints:** 17
- **WebSocket endpoints:** 1
- **OpenAPI schema:** Available at `/openapi.json`

---

## Phase 3: Area Loading Workflow

### Step 1: Create Area
```
POST /api/v1/load-area
Request: {"bbox": [31.20, 30.00, 31.22, 30.02], "grid_size": 500, "modalities": ["poi", "image", "graph"]}
Response: {"job_id": "228c5e8b-...", "status_url": "/api/v1/area-status/228c5e8b-..."}
Status: 202 Accepted ✅
```

### Step 2: Status Transitions
```
Poll 1: status="queued", step="initialized", progress=0.0
Poll 2: status="running", step="downloading_road_network", progress=0.6
Poll 3: status="completed", step="done", progress=1.0
```
Transitions observed: queued → running → completed ✅

### Step 3: Verify Cell Count
```
num_cells: 25 ✅
```

### Step 4: Artifacts
| Artifact | Path | Status |
|----------|------|--------|
| Grid file | `data/grids/grid_228c5e8b.geojson` | ✅ 25 features |
| DB record | SQLite `grids` table | ✅ 24 total grids |
| Redis job | Redis `job:228c5e8b:*` | ✅ Status: completed |
| Road features | grid_gdf with node_count, total_length, avg_degree | ✅ |

---

## Phase 4: Classification Workflow

### Test A: POI Only
```
POST /api/v1/classify
Request: {"grid_id": "grid_228c5e8b", "modalities": ["poi"]}
Status: completed ✅
Result: 25 cells classified (all Industrial)
```
**Issue:** Modality filtering ignored - all 3 modalities still processed

### Test B: Graph Only
```
Request: {"grid_id": "grid_228c5e8b", "modalities": ["graph"]}
Status: completed (with error) ❌
Error: "all input arrays must have the same shape"
```

### Test C: Image Only
```
Request: {"grid_id": "grid_228c5e8b", "modalities": ["image"]}
Status: completed (with error) ❌
Error: "all input arrays must have the same shape"
```

### Test D: All Modalities
```
Request: {"grid_id": "grid_228c5e8b", "modalities": ["poi", "image", "graph"]}
Status: completed
Result: 25 cells classified ✅
```

---

## Phase 5: Classification Validation

10 cells inspected from all-modalities result:

| Cell | Class | Confidence | Road Density | Nodes | Text Norm | Graph Norm |
|------|-------|------------|-------------|-------|-----------|------------|
| 0 | Industrial | 1.0 | 8.03e11 | 84 | 0.0 | 16287.3 |
| 1 | Industrial | 1.0 | 8.41e11 | 42 | 0.0 | 17066.8 |
| 2 | Industrial | 1.0 | 9.06e11 | 70 | 0.0 | 18385.2 |
| 3 | Industrial | 1.0 | 1.23e12 | 122 | 0.0 | 25002.2 |
| 4 | Industrial | 1.0 | 1.10e12 | 147 | 0.0 | 22312.8 |
| 5 | Industrial | 1.0 | 5.84e11 | 70 | 0.0 | 11859.5 |
| 6 | Industrial | 1.0 | 8.81e11 | 110 | 0.0 | 17866.8 |
| 7 | Industrial | 1.0 | 4.87e11 | 54 | 0.0 | 9888.9 |
| 8 | Industrial | 1.0 | 2.98e11 | 14 | 0.0 | 6042.4 |
| 9 | Commercial | 0.3556 | 0.0 | 0 | 0.0 | 0.0 |

**Findings:**
- 9/10 cells classified as Industrial (suspicious uniformity)
- Confidence = 1.0 for most cells (overconfidence)
- Road density values are unrealistic (billions)
- Text embedding norm = 0.0 for all cells (no POI data)
- Cell 9 has road_density=0, nodes=0 → probably outside road network
- No null or NaN values detected ✅
- Minor class variation: cells 9, 20, 24 show lower confidence

---

## Phase 6: Job Management

| Operation | Status | Notes |
|-----------|--------|-------|
| GET area-status/{id} | ✅ | Correct transitions |
| GET classify-status/{id} | ✅ | Status polling works |
| DELETE /jobs/{id} | ❌ | 405 Method Not Allowed on new server |
| Cancel long-running job | ⚠️ | Not tested - DELETE endpoint unavailable |

---

## Phase 7: Export Validation

| Format | Status | Details |
|--------|--------|---------|
| GeoJSON | ✅ | 25 features, valid GeoJSON |
| CSV | ⚠️ | Returns only header (1 row) - data stored in Redis, not file |
| Shapefile | ⚠️ | Not tested - depends on working classification result file |

---

## Phase 8: Training Workflow

| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| Valid dataset (project.csv) | 202 + completed | 202 + queued | ⚠️ Job queued |
| Missing file | 400 | 202 (task later fails) | ❌ Validation bypassed |
| Wrong extension (.graphml) | 400 | 202 (task later fails) | ❌ Validation bypassed |
| Invalid epochs | 400 | 422 | ✅ |

---

## Phase 9: Evaluation Workflow

| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| Valid GeoJSON ground truth | Accuracy metrics | "Could not detect prediction label column" | ❌ |
| Invalid GeoJSON (missing columns) | 400 | "Could not detect ground truth label column" | ⚠️ Error format acceptable |
| Non-existent job | 404 | 404 | ✅ |

**Root cause:** `PRED_LABEL_CANDIDATES` missing `dominant_class`

---

## Phase 10: Database Audit

| Table | Rows | Issues |
|-------|------|--------|
| `grids` | 24 | Some grids may be orphans (no corresponding job) |
| `jobs` | 0 | All jobs in Redis, not SQLite |
| Redis | 441 keys | Large payloads stored as result_data |
