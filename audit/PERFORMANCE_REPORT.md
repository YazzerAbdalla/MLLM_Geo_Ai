# Performance Report

## Endpoint Latency (Before vs After)

| Endpoint | Before (s) | After (s) | Change | Notes |
|----------|-----------|-----------|--------|-------|
| `GET /health` | 2.04 | 2.01 | ↔ No change | Baseline; needs async optimization |
| `POST /load-area` | <1 (async) | <1 | ↔ No change | Async task dispatch |
| `GET /area-status` | 2.01 | 2.01 | ↔ No change | Reads from Redis |
| `GET /grid/details` | 2.69 | 2.70 | ↔ No change | Geopandas file load |
| `GET /grid/preview` | 2.01 | 2.01 | ↔ No change | Geopandas to_json |
| `GET /grid/pois` | 2.01 | 2.01 | ↔ No change | File check + read |
| `GET /classify-status` | 2.01 | 2.01 | ↔ No change | Redis read |
| `GET /classification-result` | 2.01 | 2.01 | ↔ No change | File read |
| `GET /export` | 2.01 | 2.01 | ↔ No change | File read |
| `DELETE /jobs` | 2.30 | 2.30 | ↔ No change | Redis + Celery revoke |
| `GET /graph-topology` | 44.96 | 44.96 | ↔ No change | OSMnx is the bottleneck |

## Identified Bottlenecks

1. **GeoPandas `gpd.read_file()`** — Takes ~0.8s per call, called on every grid endpoint
2. **OSMnx graph operations** — Graph topology takes 45s due to loading 584MB `roads.graphml`
3. **No in-memory caching** — Grid data loaded from disk on every request
4. **Event loop blocking** — All async handlers call synchronous I/O without `run_in_executor`

## Optimization Opportunities (Safe)

| Optimization | Est. Improvement | Risk | Priority |
|-------------|-----------------|------|----------|
| In-memory grid cache (LRU, TTL=60s) | 80% reduction on grid endpoints | Low | High |
| Health endpoint: skip Redis ping on every call | 90% reduction | Low | High |
| Use `run_in_executor` for geopandas reads | 50% reduction on concurrent requests | Low | Medium |

Performance optimization was explicitly deprioritized per audit rules. These improvements are safe and non-breaking but were left for a future sprint.
