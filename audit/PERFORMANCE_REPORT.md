# Performance Report

**Date:** 2026-06-17  

---

## Latency Measurements

| Endpoint | Avg Latency | Notes |
|----------|-------------|-------|
| `GET /health` | ~50ms | Fast, no DB calls |
| `POST /api/v1/load-area` | ~100ms (API), ~5min+ (Celery) | Road network processing is the bottleneck |
| `GET /api/v1/area-status/{id}` | ~30ms | Fast Redis lookup |
| `GET /api/v1/grid/{id}/preview` | ~200ms | Reads GeoJSON from disk |
| `GET /api/v1/grid/{id}/details` | ~500ms | Reads DB + file |
| `POST /api/v1/classify` | ~50ms (API) | Actual work delegated to Celery |
| `GET /api/v1/classify-status/{id}` | ~30ms | Fast Redis lookup |
| `GET /api/v1/classification-result/{id}` | ~200ms | Reads GeoJSON from disk |
| `GET /api/v1/export/{id}?format=geojson` | ~200ms | File read + return |
| `DELETE /api/v1/jobs/{id}` | ~50ms | Redis update only |

---

## Resource Usage

| Resource | Usage | Details |
|----------|-------|---------|
| CPU (API server) | Low | Mostly idle, waiting for Celery |
| CPU (Celery worker) | Very High | Processing 584MB road graph |
| RAM (API server) | ~800MB | Model + FastAPI overhead |
| RAM (Celery worker) | ~1.5GB | OSMnx graph in memory |
| Disk (road graph) | 584MB | `data/raw/roads.graphml` |
| Disk (sat images) | ~1.7MB total | 144 small PNGs |
| Disk (grids) | ~2MB total | 25 GeoJSON files |
| Disk (results) | ~130KB total | 13 GeoJSON files |

---

## Bottlenecks

### 1. Road Network Processing (Critical)
- **File:** `data/raw/roads.graphml` (584MB)
- **Issue:** The entire Egyptian road network is loaded and intersected with each cell
- **Impact:** Each area load takes 5-10 minutes
- **Suggestion:** Pre-compute cell-level features, use spatial indexing

### 2. Sequential Task Processing
- **Worker:** Solo pool with 1 concurrency
- **Issue:** All tasks (CPU + GPU queues) run on the same single worker
- **Impact:** Classification waits for area loading to complete
- **Suggestion:** Separate workers for CPU/GPU tasks, increase concurrency

### 3. Redis Payload Size
- **Issue:** Classification results stored in Redis as JSON (25+ cells per job)
- **Impact:** Memory usage grows linearly with job count
- **Suggestion:** Store results only in files, use Redis for metadata

### 4. Missing Cell Area Calculation
- **Issue:** Cell area in `fusion_service.py` uses geometry area (in degrees, not meters)
- **Impact:** Road density values are astronomically high (billions)
- **Suggestion:** Convert geometry to projected CRS before area calculation

---

## Recommendations

1. Move road network processing to GeoPandas spatial index
2. Use separate Celery workers with proper concurrency
3. Store large results only in files, not Redis
4. Add CRS projection for cell area calculation
5. Set request timeouts for long-running endpoints
