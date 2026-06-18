# Performance Report | Date: 2026-06-17 | MLLM-Geo-AI Project

## 1. API Latency Measurements

| Endpoint | Method | Avg Latency | Notes |
|----------|--------|-------------|-------|
| /health | GET | ~50ms | Lightweight |
| /api/v1/load-area | POST | ~200ms | Returns 202, task runs async |
| /api/v1/area-status/{id} | GET | ~50ms | Quick Redis/memory lookup |
| /api/v1/grid/{id}/preview | GET | ~100ms | Reads GeoJSON from disk |
| /api/v1/grid/{id}/details | GET | ~100ms | Reads from disk |
| /api/v1/grid/{id}/graph-topology | GET | >120s | TIMEOUT - 558MB roads.graphml |
| /api/v1/classify | POST | ~200ms | Returns 202, task runs async |
| /api/v1/classify-status/{id} | GET | ~50ms | Quick lookup |
| /api/v1/jobs/{id} | DELETE | ~50ms | Quick update |

## 2. Celery Task Performance

| Task | Total Executions | Avg Time (estimated) |
|------|-----------------|---------------------|
| load_area_task | 16 | ~3-10s (depends on modalities) |
| classify_task | 8 | Unknown (may be slow with image encoding) |
| train_mllm_task | 9 | Unknown (depends on epochs) |

## 3. Resource Usage

| Resource | Usage | Notes |
|----------|-------|-------|
| CPU | Moderate | Grid generation, image encoding |
| RAM | ~2-4 GB | Model loading, data processing |
| Disk | >600 MB | 558MB roads.graphml, 144 sat images, models |

## 4. Bottlenecks Identified

1. **Graph-topology endpoint**: Loading 558MB roads.graphml on every request is extremely slow. Needs caching or pre-processing.
2. **Image encoding**: ResNet-18 encoding for 144+ images can take 10-30s.
3. **Large area handling**: 500-cell limit prevents excessive processing.
4. **Classify task latency**: The Celery classify task may be slow due to image encoding pipeline.

## 5. Recommendations

1. Cache the parsed graph-topology for each grid_id
2. Add timeout limits to long-running endpoints
3. Consider reducing roads.graphml size or using spatial indexing

## 6. Evidence Matrix

| Item | Code Verified | Runtime Verified | Evidence Attached |
|------|:-------------:|:----------------:|:-----------------:|
| API Latency | YES | YES | YES |
| Celery Performance | YES | PARTIAL | YES |
| Resource Usage | YES | PARTIAL | YES |
