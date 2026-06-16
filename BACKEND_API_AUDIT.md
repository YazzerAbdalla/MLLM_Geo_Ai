# BACKEND API AUDIT

## Executive Summary
This document provides a comprehensive contract and implementation audit of the MLLM-Geo-AI backend. It includes details on all API endpoints, request/response DTOs, background jobs, websockets, domain models, storage mechanisms, and missing features.

## Architecture Overview
The application follows a Domain-Driven Design (DDD) structure.
- **Entry point:** `app/main.py`
- **Routing:** `app/interfaces/api.py`
- **Application Services:** `app/application/` (FusionService, ExportService, EvaluationService)
- **Infrastructure:** `app/infrastructure/` (RedisJobStore, SatelliteLoader, RoadNetwork, AI Model Wrappers)
- **Domain:** `app/domain/` (Grid generation, spatial logic)
- **Background Jobs:** Celery is used to process long-running tasks asynchronously via Redis.

## Endpoint Catalog

### POST /api/v1/load-area
* **File:** `app/interfaces/api.py`
* **Function:** `load_area()`
* **Purpose:** Triggers asynchronous generation of a spatial grid from a bounding box and initializes area loading.
* **Request DTO:**
```ts
interface LoadAreaRequest {
  bbox?: number[];
  place_name?: string;
  grid_size: number; // 200, 500, or 1000
  modalities: string[]; // default: ["poi", "image", "graph"]
}
```
* **Response:** Returns `job_id`, `status_url`, `websocket_url`.
* **Status Codes:** 202 (Accepted), 413 (Payload Too Large), 501 (Not Implemented - if async not available).
* **Status:** 🟡 Partially Implemented (Async tasks guarded by `TASKS_AVAILABLE`).

### GET /api/v1/area-status/{job_id}
* **File:** `app/interfaces/api.py`
* **Function:** `get_area_status()`
* **Purpose:** Poll status of a load-area job.
* **Status:** ✅ Fully Implemented.

### GET /api/v1/grid/{grid_id}/preview
* **File:** `app/interfaces/api.py`
* **Function:** `get_grid_preview()`
* **Purpose:** Returns a GeoJSON preview of the generated grid.
* **Status:** ✅ Fully Implemented.

### POST /api/v1/classify
* **File:** `app/interfaces/api.py`
* **Function:** `classify_grid()`
* **Purpose:** Starts the multi-modal classification background task.
* **Request DTO:**
```ts
interface ClassifyRequest {
  grid_id: string;
  modalities: string[];
  fusion_method: string;
  model_version?: string;
}
```
* **Status:** 🟡 Partially Implemented (Requires async).

### GET /api/v1/classify-status/{job_id}
* **File:** `app/interfaces/api.py`
* **Function:** `get_classify_status()`
* **Purpose:** Poll status of a classify job.
* **Status:** ✅ Fully Implemented.

### GET /api/v1/classification-result/{job_id}
* **File:** `app/interfaces/api.py`
* **Function:** `get_classification_result()`
* **Purpose:** Retrieve the classification results as GeoJSON.
* **Status:** ✅ Fully Implemented.

### GET /api/v1/export/{job_id}
* **File:** `app/interfaces/api.py`
* **Function:** `export_results()`
* **Purpose:** Export results as geojson, csv, or shapefile.
* **Status:** ✅ Fully Implemented.

### GET /api/v1/thumbnails/{grid_id}/{cell_id}.jpg
* **File:** `app/interfaces/api.py`
* **Function:** `get_thumbnail()`
* **Purpose:** Fetch satellite image patch for a cell.
* **Status:** ✅ Fully Implemented.

### DELETE /api/v1/jobs/{job_id}
* **File:** `app/interfaces/api.py`
* **Function:** `cancel_job()`
* **Purpose:** Terminate a running Celery job.
* **Status:** ✅ Fully Implemented.

### GET /api/v1/grid/{grid_id}/graph-topology
* **File:** `app/interfaces/api.py`
* **Function:** `get_graph_topology()`
* **Purpose:** Extracts graph topology for a grid.
* **Status:** ✅ Fully Implemented.

### POST /api/v1/evaluate
* **File:** `app/interfaces/api.py`
* **Function:** `evaluate()`
* **Purpose:** Evaluate job against ground truth.
* **Status:** ✅ Fully Implemented.

### GET /api/v1/evaluate/{job_id}/export
* **File:** `app/interfaces/api.py`
* **Function:** `export_evaluation()`
* **Purpose:** Export evaluation as CSV.
* **Status:** ✅ Fully Implemented.

### POST /api/v1/mllm/train
* **File:** `app/interfaces/api.py`
* **Function:** `train_mllm()`
* **Purpose:** Trigger model training async.
* **Status:** 🟡 Partially Implemented (Async check).

### GET /api/v1/mllm/train-status/{job_id}
* **File:** `app/interfaces/api.py`
* **Function:** `get_train_status()`
* **Purpose:** Poll training job.
* **Status:** ✅ Fully Implemented.

### POST /api/v1/query
* **File:** `app/interfaces/api.py`
* **Function:** `natural_language_query()`
* **Purpose:** Digital Twin Natural Language Query.
* **Status:** 🔴 Stub (Returns 501).

## DTO Catalog
```ts
interface LoadAreaRequest {
  bbox?: number[];
  place_name?: string;
  grid_size: number;
  modalities: string[];
}

interface ClassifyRequest {
  grid_id: string;
  modalities: string[];
  fusion_method: string;
  model_version?: string;
}

interface QueryRequest {
  question: string;
  grid_id: string;
}

interface MLLMTrainRequest {
  model_name: string;
  dataset_path: string;
  epochs: number;
  batch_size: number;
  learning_rate: number;
}
```

## WebSocket Catalog

### Endpoint
`/api/v1/ws/progress/{job_id}`

### Status
❌ Missing.
The URLs are returned in `load_area` and `classify` endpoints (`ws://localhost:8000/api/v1/ws/progress/{job_id}`) but the actual WebSocket endpoint is NOT implemented in `api.py`.

## Background Jobs
- **Celery configuration:** `celery_app.py`
- **Tasks:**
  - `tasks.load_area.load_area_task` (queue: cpu)
  - `tasks.classify.classify_task` (queue: gpu)
  - `tasks.train_mllm.train_mllm_task` (queue: gpu)
- **Progress Tracking:** Stored in Redis (`RedisJobStore`) via `job_store.py`.
- **Cancellation:** Supports cancellation via `celery_app.control.revoke(task_id, terminate=True)`.

## Service Catalog
- **MultiModalClassificationUseCase:** Handles fusion of embeddings.
- **ExportService:** Handles conversion of GeoJSON to CSV and Shapefile using temp directories.
- **EvaluationService:** Evaluates predicted results against ground truth.

## Storage Catalog
- **Redis:** Used for job tracking, progress, and status mapping.
- **SQLite Database:** `app.infrastructure.db.py` - Stores `Grid` models.
- **File System:** 
  - `data/results/*.geojson`
  - `data/grids/*.geojson`
  - `data/sat_images/cell_*.png`

## Domain Models
- **Grid:** Represents the bounding box map split into cells. `id`, `bbox`, `num_cells`, `grid_size_m`.

## Frontend Compatibility Report
- Frontend expects WebSockets for job progress but they are missing on the backend.
- The `POST /api/v1/query` endpoint is a 501 stub.

## Security Audit
- No authentication/authorization currently implemented.
- CORS configuration is unknown (needs to be checked in `main.py` but currently omitted).

## Performance Audit
- File-based I/O for grids and results could cause bottlenecks.
- `tempfile` is used for shapefile exports, which is good.
- Missing caching for thumbnail retrieval.

## Missing Work
- **WebSocket Progress Updates:** Need `/api/v1/ws/progress/{job_id}` implementation.
- **Natural Language Query (v2):** `POST /api/v1/query` is a stub.
- **Docker deployment.**

## Complete API Matrix
| Endpoint          | Status     | Notes           |
| ----------------- | ---------- | --------------- |
| POST /load-area | 🟡 Partial | Async guard |
| GET /area-status/{id} | ✅ Implemented | |
| GET /grid/{id}/preview | ✅ Implemented | |
| POST /classify | 🟡 Partial | Async guard |
| GET /classify-status/{id} | ✅ Implemented | |
| GET /classification-result/{id} | ✅ Implemented | |
| GET /export/{id} | ✅ Implemented | |
| GET /thumbnails/{g}/{c} | ✅ Implemented | |
| DELETE /jobs/{id} | ✅ Implemented | |
| GET /grid/{id}/graph-topology | ✅ Implemented | |
| POST /evaluate | ✅ Implemented | |
| GET /evaluate/{id}/export | ✅ Implemented | |
| POST /mllm/train | 🟡 Partial | |
| GET /mllm/train-status/{id} | ✅ Implemented | |
| POST /query | 🔴 Stub | Returns 501 |
