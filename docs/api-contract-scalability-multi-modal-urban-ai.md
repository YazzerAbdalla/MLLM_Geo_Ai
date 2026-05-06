# API Contract & Scalability Plan for Upgraded Multi‑Modal Urban AI System

This document defines the **fixed API contract** (OpenAPI 3.0) between the frontend UI and the FastAPI backend, evaluates the need for a **database**, and outlines **scalability strategies** for the entire application.

---

## 1. API Contract (OpenAPI 3.0)

Base URL: `http://localhost:8000/api/v1` (development)  
All endpoints return JSON unless specified otherwise.

### 1.1 Data Loading

#### `POST /load-area`
Start loading POI, road network, and satellite imagery for a given area.

**Request Body:**
```json
{
  "bbox": [31.10, 29.90, 31.30, 30.10],   // [min_lon, min_lat, max_lon, max_lat]
  "place_name": "Cairo, Egypt",            // optional, if provided bbox is derived
  "grid_size": 500,                        // cell size in meters (200, 500, 1000)
  "modalities": ["poi", "image", "graph"]  // which data types to load
}
```

**Response (202 Accepted):**
```json
{
  "job_id": "abc12345-...",
  "status_url": "/api/v1/area-status/abc12345",
  "websocket_url": "ws://localhost:8000/api/v1/ws/progress/abc12345"
}
```

**Errors:**
- `400` – Invalid bbox or unsupported grid size.
- `413` – Area too large (exceeds max cells, e.g., > 500).
- `503` – External service (OSM, Sentinel Hub) unavailable.

---

#### `GET /area-status/{job_id}`
Polling endpoint for loading progress.

**Response:**
```json
{
  "job_id": "abc12345",
  "status": "running",   // pending, running, completed, failed
  "step": "downloading_satellite",
  "progress": 0.65,      // 0..1
  "error": null
}
```

When `status = "completed"`, additional field:
```json
{
  "grid_id": "grid_abc123",
  "num_cells": 156,
  "geojson_preview_url": "/api/v1/grid/abc123/preview"
}
```

---

#### `GET /grid/{grid_id}/preview`
Returns GeoJSON of the grid cells (without classification) for preview.

**Response:** `application/geo+json`

---

### 1.2 Classification

#### `POST /classify`
Run multi‑modal classification on a loaded grid.

**Request Body:**
```json
{
  "grid_id": "grid_abc123",
  "modalities": ["poi", "image", "graph"],   // subset of loaded modalities
  "fusion_method": "concat",                 // concat, weighted, attention (default concat)
  "model_version": "v1.0"                   // optional
}
```

**Response (202 Accepted):**
```json
{
  "job_id": "class_job_xyz789",
  "status_url": "/api/v1/classify-status/xyz789",
  "websocket_url": "ws://localhost:8000/api/v1/ws/progress/xyz789"
}
```

---

#### `GET /classify-status/{job_id}`
Polling endpoint for classification progress.

**Response:**
```json
{
  "job_id": "xyz789",
  "status": "running",
  "step": "encoding_images",
  "progress": 0.3
}
```

When completed:
```json
{
  "result_url": "/api/v1/classification-result/xyz789"
}
```

---

#### `GET /classification-result/{job_id}`
Retrieve the full classification result as GeoJSON.

**Response:** `application/geo+json`  
Each feature (grid cell) has properties:
```json
{
  "cell_id": 42,
  "dominant_class": "Residential",
  "confidences": {
    "Residential": 0.85,
    "Commercial": 0.10,
    "Industrial": 0.05
  },
  "poi_top_categories": ["cafe", "school", "bank"],
  "road_density_km_per_km2": 4.2,
  "node_count": 18,
  "satellite_thumbnail_url": "/api/v1/thumbnails/grid_abc123/cell_42.jpg"
}
```

---

### 1.3 Export

#### `GET /export/{job_id}`
Download classification result in selected format.

**Query Parameters:**
- `format` – `geojson` | `shapefile` | `csv` (default `geojson`)

**Response:** File download (Content-Disposition).

---

### 1.4 Thumbnails

#### `GET /thumbnails/{grid_id}/{cell_id}.jpg`
Returns the satellite image patch for a specific cell.

**Response:** `image/jpeg`

---

### 1.5 Natural Language Query (future, but contract defined)

#### `POST /query`
Interpret a natural language question and return matching cell IDs.

**Request:**
```json
{
  "question": "Show me residential areas with high road density",
  "grid_id": "grid_abc123"
}
```

**Response:**
```json
{
  "cell_ids": [12, 45, 78, 102],
  "explanation": "Areas classified as Residential with road density > 3.5 km/km²"
}
```

---

### 1.6 Training (future, optional)

#### `POST /train`
Start a training job with user‑provided labels.

**Request (multipart/form-data):**
- `labels` – GeoJSON or CSV file with per‑cell ground truth.
- `config` – JSON string with hyperparameters (learning rate, epochs, fusion method).

**Response:**
```json
{
  "job_id": "train_123",
  "status_url": "/api/v1/train-status/123"
}
```

---

## 2. Do We Need a Database?

### 2.1 Current Architecture (No DB)
The existing system is **stateless**:
- Input: `project.csv` (static)
- Grid cells are generated in memory.
- POI embeddings computed on‑the‑fly.
- No persistent storage of jobs or results.

**For the upgraded UI with async jobs, we need to track:**
- Job metadata (status, progress, result location)
- Grid definitions (cells geometry, satellite patch paths)
- Classification results (temporary until exported)
- User sessions (if authentication added later)

### 2.2 Recommended: Lightweight Database

| Use Case | Need DB? | Recommended Solution |
|----------|----------|----------------------|
| Job queue & status | **Yes** | Redis (ephemeral, fast) |
| Grid geometry & metadata | **Yes** | PostgreSQL + PostGIS (spatial queries) or SQLite (development) |
| Classification results (temporary) | **No** – store as GeoJSON files on disk, reference by job ID | File system + Redis mapping |
| User accounts / sessions | **Yes** (if added) | PostgreSQL + JWT |
| Model registry (versions, metrics) | **Yes** (advanced) | PostgreSQL or simple YAML files |

**Minimum viable DB setup for MVP:**
- **Redis** for job queues, progress tracking, and short‑lived result pointers.
- **SQLite** (or PostgreSQL) for storing grid metadata (bbox, cell size, creation time) – avoids recomputing grid on every request.

### 2.3 Data Persistence Plan

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│   FastAPI   │────▶│    Redis    │ (jobs, progress)
└─────────────┘     └─────────────┘     └─────────────┘
                           │                    │
                           ▼                    ▼
                    ┌─────────────┐     ┌─────────────┐
                    │ PostgreSQL  │     │   File      │
                    │ / SQLite    │     │   System    │
                    │ (grids,     │     │ (thumbnails,│
                    │  metadata)  │     │  results)   │
                    └─────────────┘     └─────────────┘
```

**Why not a full RDBMS from start?**  
MVP can use SQLite (file‑based) for simplicity. Redis is still recommended for job queues because Celery/RQ expects it. If you prefer to avoid Redis, you can use `BackgroundTasks` in FastAPI for short jobs (<1 min), but classification may take >30s – a task queue is better.

---

## 3. Scalability Strategies

The system will face different loads:
- **Number of concurrent users** (planners, analysts)
- **Size of study area** (grid cells, satellite patches)
- **Model inference time** (GNN + image encoding)

### 3.1 Horizontal Scaling (Stateless Backend)

| Component | Stateless? | Scaling Strategy |
|-----------|------------|------------------|
| FastAPI (REST + WebSocket) | Yes | Run multiple replicas behind a load balancer (e.g., Nginx, Traefik). Use `sticky sessions` for WebSocket if needed. |
| Celery workers | Yes | Scale workers horizontally; use Redis as broker. |
| Redis | No (stateful) | Use Redis Sentinel or Redis Cluster for high availability. |
| PostgreSQL | No (stateful) | Read replicas for query scaling; connection pooling (PgBouncer). |
| File storage (thumbnails, results) | Yes | Use object storage (S3, MinIO) instead of local disk. |

### 3.2 Vertical Scaling (Resource Optimisation)

- **GPU for inference**: Attach GPU to one or more Celery workers for model inference. Queue classification jobs to GPU workers.
- **CPU‑intensive tasks** (grid generation, POI embedding) can run on CPU workers.
- **Memory** – Satellite patches: store as files, not in RAM.

### 3.3 Optimising Long‑Running Jobs

| Problem | Solution |
|---------|----------|
| Large area (e.g., 1000 cells) | Process cells in batches; stream progress after each batch. Limit max cells (e.g., 500) with frontend warning. |
| Satellite download per cell | Parallel downloads with `asyncio` (but respect API rate limits). Cache downloaded patches per bbox. |
| Image encoding (CNN) | Batch encode many images on GPU; pre‑compute embeddings when area is loaded (not during classification). |
| GNN inference | For < 500 nodes, inference is fast (<1s). For larger graphs, use graph partitioning or mini‑batch sampling (e.g., NeighborLoader). |

### 3.4 Caching Strategy

| Cache Level | Technology | TTL | What to cache |
|-------------|------------|-----|----------------|
| POI embeddings per grid cell | Redis | indefinite (until grid changes) | Already computed embeddings |
| Satellite patches | Filesystem / S3 | permanent | Raw images |
| Road network features per cell | Redis | permanent | Node count, road length |
| Classification results | Redis (or file) | 24 hours | GeoJSON result of a job |

### 3.5 Asynchronous Job Flow (Production Ready)

```
User request → FastAPI → Creates job record in Redis → Enqueues task in Celery → Returns job_id
Celery worker → Processes task → Updates Redis progress → Stores final result in S3 → Marks job complete
Frontend polls or WebSocket → Reads progress from Redis → When complete, fetches result URL from S3
```

### 3.6 Resource Estimation (Example)

| Workload | Cells | Satellite images | Inference time (GPU) | Memory |
|----------|-------|------------------|----------------------|--------|
| Small neighbourhood | 25 | 25 | ~5 sec | 2 GB |
| Medium district | 100 | 100 | ~15 sec | 4 GB |
| Large zone | 500 | 500 | ~60 sec | 16 GB (parallel batch) |

**Recommendation:** Set max cells = 500; if exceeded, return error with suggestion to zoom in.

---

## 4. Database Schema (MVP)

### SQLite / PostgreSQL Tables

#### `grids`
| Column | Type | Description |
|--------|------|-------------|
| id (PK) | UUID | Unique grid identifier |
| bbox | JSON | [min_lon, min_lat, max_lon, max_lat] |
| grid_size_m | INT | 200, 500, 1000 |
| num_cells | INT | Total cells |
| created_at | TIMESTAMP | |
| status | TEXT | loading, ready, error |

#### `jobs`
| Column | Type | Description |
|--------|------|-------------|
| id (PK) | UUID | Job ID |
| type | TEXT | load, classify, train |
| grid_id (FK) | UUID | References grids.id |
| status | TEXT | pending, running, completed, failed |
| progress | FLOAT | 0..1 |
| step | TEXT | Current step description |
| result_path | TEXT | File path (or S3 URL) of result |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

#### `thumbnails` (optional, can be derived from file naming)
| Column | Type |
|--------|------|
| grid_id | UUID |
| cell_index | INT |
| file_path | TEXT |

**Redis keys:**
- `job:{job_id}:status` → JSON
- `job:{job_id}:progress` → float
- `job:{job_id}:step` → string
- `grid:{grid_id}:cells` → GeoJSON (optional, for quick access)

---

## 5. Implementation Roadmap for Scalability

| Phase | Focus | DB | Scaling actions |
|-------|-------|----|------------------|
| **MVP (Week 1‑2)** | Single‑user, local | SQLite + Redis (or in‑memory dict for jobs) | No scaling, but design for later |
| **Alpha (Week 3‑4)** | Multiple concurrent requests | PostgreSQL + Redis (on same machine) | Celery workers (1 GPU, 2 CPU) |
| **Beta (Week 5‑6)** | Production‑like load | Managed PostgreSQL (RDS), Redis Cluster | Load‑balanced FastAPI (2‑3 replicas), S3 for files |
| **Public release** | 50+ concurrent users | Cloud‑native (AWS/GCP) | Auto‑scaling workers, CDN for thumbnails |

---

## 6. Summary of Decisions

| Question | Answer |
|----------|--------|
| Need a database? | **Yes** – at least Redis for job tracking, plus SQLite/PostgreSQL for grid metadata. |
| Can we start without a DB? | **Yes, but with limitations** – you can store jobs in memory, but they will be lost on restart. For demo/MVP, acceptable. |
| Recommended DB for MVP | **SQLite (grids) + Redis (jobs)** – both easy to set up. |
| How to scale classification? | Use Celery workers with GPU; batch image encoding; limit grid size. |
| How to handle many users? | Stateless FastAPI behind load balancer; use Redis for session affinity if needed for WebSocket. |

---

This API contract and scaling plan ensures that your upgraded multi‑modal urban AI system is **production‑ready, extensible, and maintainable**. The next step is to implement the endpoints in FastAPI and connect them to the frontend according to the PRD.