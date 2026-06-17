# Endpoint Inventory

**Source:** OpenAPI schema + FastAPI routers  
**Server:** http://localhost:8001  
**Date:** 2026-06-17  

---

## REST Endpoints

| # | Method | Endpoint | Purpose | Request Schema | Response Schema | Status Codes |
|---|--------|----------|---------|---------------|----------------|--------------|
| 1 | POST | `/api/v1/load-area` | Create grid from bbox | `{bbox, place_name, area_geometry, grid_size, modalities}` | `{job_id, status_url, websocket_url}` | 202, 413, 422, 501 |
| 2 | GET | `/api/v1/area-status/{job_id}` | Poll area load job | path: `job_id` | `{job_id, status, step, progress, error}` + grid info when completed | 200, 404 |
| 3 | GET | `/api/v1/grid/{grid_id}/preview` | Get grid GeoJSON | path: `grid_id` | GeoJSON FeatureCollection | 200, 404 |
| 4 | GET | `/api/v1/grid/{grid_id}/details` | Get grid statistics | path: `grid_id` | `{grid_id, bbox, cell_count, road_density, poi_count, graph_stats}` | 200, 404 |
| 5 | GET | `/api/v1/grid/{grid_id}/pois` | Get POI data | path: `grid_id` | `[{id, name, category, lat, lng}]` | 200, 404 |
| 6 | POST | `/api/v1/classify` | Start classification | `{grid_id, modalities, fusion_method, model_version}` | `{job_id, status_url, websocket_url}` | 202, 400, 422, 501 |
| 7 | GET | `/api/v1/classify-status/{job_id}` | Poll classification job | path: `job_id` | `{job_id, status, step, progress, error}` + result_url when completed | 200, 404 |
| 8 | GET | `/api/v1/classification-result/{job_id}` | Get classification results | path: `job_id` | GeoJSON FeatureCollection | 200, 404 |
| 9 | GET | `/api/v1/export/{job_id}` | Export results | path: `job_id`, query: `format` | File (GeoJSON/CSV/Shapefile) | 200, 400, 404 |
| 10 | GET | `/api/v1/thumbnails/{grid_id}/{cell_id}.jpg` | Get satellite thumbnail | path: `grid_id`, `cell_id` | JPEG image | 200, 404 |
| 11 | DELETE | `/api/v1/jobs/{job_id}` | Cancel a job | path: `job_id` | `{job_id, status, message}` | 200, 404 |
| 12 | GET | `/api/v1/grid/{grid_id}/graph-topology` | Get road network graph | path: `grid_id`, query: `max_nodes`, `simplify` | GeoJSON (MultiLineString) | 200, 404, 501 |
| 13 | POST | `/api/v1/evaluate` | Evaluate predictions | form: `job_id`, `ground_truth_file` | `{job_id, num_samples, labels, overall_accuracy, macro_f1, weighted_f1, per_class_f1, confusion_matrix}` | 200, 400, 404, 500 |
| 14 | GET | `/api/v1/evaluate/{job_id}/export` | Export evaluation CSV | path: `job_id` | CSV file | 200, 400, 404 |
| 15 | POST | `/api/v1/mllm/train` | Start MLLM training | `{model_name, dataset_path, epochs, batch_size, learning_rate}` | `{job_id, status_url, websocket_url}` | 202, 400, 501 |
| 16 | GET | `/api/v1/mllm/train-status/{job_id}` | Poll training job | path: `job_id` | `{job_id, status, step, progress, error}` | 200, 404 |
| 17 | POST | `/api/v1/query` | NL query (stub) | `{question, grid_id}` | `{answer, query_type, confidence}` | 200, 400, 404 |
| 18 | GET | `/health` | Health check | none | `{status, app, redis, job_store_mode}` | 200 |

---

## WebSocket Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| WS | `/api/v1/ws/progress/{job_id}` | Real-time job progress |

---

## Router Paths

- **Prefix:** `/api/v1`
- **Router module:** `app/interfaces/api.py`
- **Total routes:** 18 (17 REST + 1 WebSocket)
