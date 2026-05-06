# MLLM-Geo-AI — Comprehensive Build Plan for Missing Deliverables

**Generated:** 2026-04-26  
**Verification baseline:** 10 / 34 checks passed  
**Target after completion:** 32+ / 34 checks passed  
**Estimated effort:** 6 working days across 4 sprints

---

## Overview

The verification agent identified that the core ML pipeline is solid (encoders wired, MLP correct, inference valid, tests passing), but the **operational layers were never built beyond an in-memory prototype**. This plan fixes all 24 missing items across persistence, API contracts, scalability infrastructure, and scientific output.

> **Critical dependency:** Sprint 1 must be completed before any other sprint. The in-memory `job_store.py` dict is the root cause behind 12 of the 24 failures. Redis and SQLite must be wired first.

---

## Summary

| Sprint | Focus | Days | Checks Fixed | Severity |
|--------|-------|------|-------------|----------|
| Sprint 1 | Persistence layer | 1–2 | 3.1 → 3.6 (0/6 → 6/6) | Critical |
| Sprint 2 | API contracts + payload | 3–4 | 1.4, 2.3, 2.6–2.10 (4/10 → 10/10) | Critical |
| Sprint 3 | Scalability infrastructure | 5 | 4.1 → 4.7 (0/7 → 7/7) | Important |
| Sprint 4 | Scientific output + docs | 6 | 5.1–5.4 (2/6 → 6/6) | Final |
| **Sprint 5** | **Model Training Pipeline** | **7-8** | **Train RF + MLP models** | **Required** |
| **Sprint 6** | **Full Evaluation + Docs** | **9** | **Run evals, document results** | **Required** |
| **Sprint 7** | **Production Integration** | **10** | **Celery workers, full test** | **Final** |

---

## Sprint 1 — Persistence Layer
**Days 1–2 · Fixes checks 3.1 – 3.6 · Critical**

The entire job management system currently runs in a Python dict that evaporates on every server restart. This sprint replaces it with Redis (job tracking) and SQLite/SQLAlchemy (grid and job metadata).

---

### Task 1.1 — Install Redis and wire job store
**Effort:** 4 h  
**Fixes:** Check 3.1  
**Files:** `job_store.py`, `main.py`

Replace the in-memory dict in `job_store.py` with `redis-py` calls. All job state reads and writes must go through Redis.

**Redis key schema:**
```
job:{job_id}:status    → string  (pending | running | completed | failed)
job:{job_id}:progress  → float   (0.0 – 1.0)
job:{job_id}:step      → string  (human-readable current step)
```

**Implementation:**
```python
# infrastructure/redis_store.py
import redis
import json

class RedisJobStore:
    def __init__(self, url: str = "redis://localhost:6379"):
        self.r = redis.from_url(url, decode_responses=True)

    def set_status(self, job_id: str, status: str):
        self.r.set(f"job:{job_id}:status", status)

    def set_progress(self, job_id: str, progress: float, step: str):
        self.r.set(f"job:{job_id}:progress", str(round(progress, 4)))
        self.r.set(f"job:{job_id}:step", step)

    def get_job(self, job_id: str) -> dict | None:
        status = self.r.get(f"job:{job_id}:status")
        if not status:
            return None
        return {
            "job_id": job_id,
            "status": status,
            "progress": float(self.r.get(f"job:{job_id}:progress") or 0),
            "step": self.r.get(f"job:{job_id}:step") or "",
        }
```

Add to `requirements.txt`:
```
redis>=5.0.0
```

---

### Task 1.2 — Create SQLite models — grids table
**Effort:** 3 h  
**Fixes:** Check 3.2  
**Files:** `infrastructure/db.py`, `models/grid.py`

Create a SQLAlchemy model for the `grids` table and run the Alembic migration.

**Schema:**
| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | Unique grid identifier |
| bbox | JSON | [min_lon, min_lat, max_lon, max_lat] |
| grid_size_m | INT | 200, 500, or 1000 |
| num_cells | INT | Total cells in grid |
| created_at | TIMESTAMP | Creation time |
| status | TEXT | loading \| ready \| error |

**Implementation:**
```python
# models/grid.py
from sqlalchemy import Column, String, Integer, JSON, DateTime
from sqlalchemy.dialects.sqlite import BLOB
from infrastructure.db import Base
import uuid, datetime

class Grid(Base):
    __tablename__ = "grids"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    bbox = Column(JSON, nullable=False)
    grid_size_m = Column(Integer, nullable=False)
    num_cells = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String, default="loading")
```

---

### Task 1.3 — Create SQLite models — jobs table
**Effort:** 2 h  
**Fixes:** Check 3.3  
**Files:** `models/job.py`

**Schema:**
| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | Job identifier |
| type | TEXT | load \| classify \| train |
| grid_id | UUID (FK) | References grids.id |
| status | TEXT | pending \| running \| completed \| failed |
| progress | FLOAT | 0.0 – 1.0 |
| step | TEXT | Current step description |
| result_path | TEXT | File path or S3 URL of result |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | Auto-updated on write |

**Implementation:**
```python
# models/job.py
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from infrastructure.db import Base
import uuid, datetime

class Job(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    type = Column(String, nullable=False)
    grid_id = Column(String, ForeignKey("grids.id"), nullable=True)
    status = Column(String, default="pending")
    progress = Column(Float, default=0.0)
    step = Column(String, default="")
    result_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)
```

---

### Task 1.4 — Wire DB to FastAPI lifespan — restart resilience
**Effort:** 2 h  
**Fixes:** Check 3.4  
**Files:** `main.py`, `infrastructure/db.py`

Use FastAPI's `lifespan` context manager to open the DB connection on startup and close it on shutdown. All job reads/writes must go through SQLAlchemy sessions — no in-memory fallback path.

```python
# main.py
from contextlib import asynccontextmanager
from infrastructure.db import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)  # create tables on startup
    yield
    engine.dispose()

app = FastAPI(lifespan=lifespan)
```

**Verification:** Kill the server process, restart it, and confirm that jobs created before the restart are still queryable via `GET /api/v1/area-status/{job_id}`.

---

### Task 1.5 — Fix satellite patch save path
**Effort:** 1 h  
**Fixes:** Check 3.5  
**Files:** `infrastructure/satellite_loader.py`

The current code saves to `data/thumbnails/{grid_id}/cell_N.png` (UUID subdirectory, regenerated each run). Change to a stable, flat path and add an existence guard.

```python
# infrastructure/satellite_loader.py  — patched download loop
def download_for_grid(self, grid_gdf, output_dir="data/sat_images", radius_m=250):
    os.makedirs(output_dir, exist_ok=True)
    for idx, cell in grid_gdf.iterrows():
        save_path = f"{output_dir}/cell_{idx}.png"
        if os.path.exists(save_path):          # cache guard — skip if already downloaded
            continue
        lon, lat = cell.geometry.centroid.x, cell.geometry.centroid.y
        # ... GEE download logic unchanged ...
        img.save(save_path)
```

---

### Task 1.6 — Write classification result GeoJSON to disk
**Effort:** 2 h  
**Fixes:** Check 3.6  
**Files:** `application/fusion_service.py`

After inference, serialize the full result as a GeoJSON FeatureCollection to disk and store the path in the `jobs` table. Never hold results in memory.

```python
# application/fusion_service.py  — after inference loop
import json, os

def save_result(self, job_id: str, features: list[dict]) -> str:
    os.makedirs("data/results", exist_ok=True)
    path = f"data/results/{job_id}.geojson"
    feature_collection = {
        "type": "FeatureCollection",
        "features": features   # each feature must include geometry + properties
    }
    with open(path, "w") as f:
        json.dump(feature_collection, f)
    return path
```

Then update `jobs.result_path` in the DB with the returned path.

---

## Sprint 2 — API Contracts + Payload
**Days 3–4 · Fixes checks 1.4, 2.3, 2.6 – 2.10 · Critical**

Sprint 1 must be complete before starting this sprint. Most fixes here are small; the GeoJSON FeatureCollection endpoint is the substantial one.

---

### Task 2.1 — Propagate graph metrics to classification payload
**Effort:** 3 h  
**Fixes:** Check 1.4  
**Files:** `application/fusion_service.py`

After inference, each cell's result dict must include all required fields beyond the old `dominant_class` + `confidences`.

**Required fields to add:**
```python
{
    "cell_id": int,
    "dominant_class": str,
    "confidences": {"Residential": float, "Commercial": float, "Industrial": float},
    # --- NEW FIELDS BELOW ---
    "road_density_km_per_km2": float,      # total_length_m / (cell_area_m2 / 1e6)
    "node_count": int,
    "poi_top_categories": list[str],       # top-3 POI category names by frequency
    "satellite_thumbnail_url": str,        # "/api/v1/thumbnails/{grid_id}/{cell_id}.jpg"
}
```

**Calculation for road density:**
```python
cell_area_km2 = cell.geometry.area / 1e6   # geometry is in EPSG:32636 (metres)
road_density = graph_features[i][1] / 1000 / cell_area_km2  # length in km / area in km²
```

---

### Task 2.2 — Fix grid preview Content-Type
**Effort:** 0.5 h  
**Fixes:** Check 2.3  
**Files:** `interfaces/api.py`

One-line fix. Replace the default JSON response with an explicit `Response` object.

```python
# Before
@router.get("/api/v1/grid/{grid_id}/preview")
async def get_grid_preview(grid_id: str):
    return geojson_dict   # returns application/json — WRONG

# After
from fastapi import Response

@router.get("/api/v1/grid/{grid_id}/preview")
async def get_grid_preview(grid_id: str):
    geojson_str = json.dumps(geojson_dict)
    return Response(content=geojson_str, media_type="application/geo+json")
```

---

### Task 2.3 — Build compliant GeoJSON FeatureCollection result endpoint
**Effort:** 2 h  
**Fixes:** Check 2.6  
**Files:** `interfaces/api.py`

Read the saved `.geojson` file from disk (written in Task 1.6). Each feature must carry the cell polygon geometry plus all required properties from Task 2.1.

```python
@router.get("/api/v1/classification-result/{job_id}")
async def get_classification_result(job_id: str):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job or not job.result_path:
        raise HTTPException(404, "Result not ready or job not found")
    if not os.path.exists(job.result_path):
        raise HTTPException(404, "Result file missing")
    with open(job.result_path) as f:
        content = f.read()
    return Response(content=content, media_type="application/geo+json")
```

**Note:** The geometry (cell polygon in WGS84) must be embedded in each feature when `fusion_service.py` builds the FeatureCollection. Reproject cell centroids from EPSG:32636 back to WGS84 before serialising.

---

### Task 2.4 — Implement export endpoint — GeoJSON, CSV, Shapefile
**Effort:** 3 h  
**Fixes:** Check 2.7  
**Files:** `interfaces/api.py`, `application/export_service.py`

Replace the stub with real file-streaming logic for all three formats.

```python
# application/export_service.py
import geopandas as gpd, zipfile, io, tempfile

class ExportService:
    def to_geojson(self, result_path: str) -> bytes:
        with open(result_path, "rb") as f:
            return f.read()

    def to_csv(self, result_path: str) -> bytes:
        gdf = gpd.read_file(result_path)
        # drop geometry column for CSV, keep all properties
        df = gdf.drop(columns="geometry")
        return df.to_csv(index=False).encode()

    def to_shapefile(self, result_path: str) -> bytes:
        gdf = gpd.read_file(result_path)
        with tempfile.TemporaryDirectory() as tmpdir:
            shp_path = os.path.join(tmpdir, "result.shp")
            gdf.to_file(shp_path)
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w") as z:
                for f in os.listdir(tmpdir):
                    z.write(os.path.join(tmpdir, f), arcname=f)
            return buf.getvalue()
```

```python
# interfaces/api.py
from fastapi.responses import Response

@router.get("/api/v1/export/{job_id}")
async def export_result(job_id: str, format: str = "geojson"):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job or not job.result_path:
        raise HTTPException(404)

    svc = ExportService()
    if format == "geojson":
        data = svc.to_geojson(job.result_path)
        media_type, filename = "application/geo+json", f"{job_id}.geojson"
    elif format == "csv":
        data = svc.to_csv(job.result_path)
        media_type, filename = "text/csv", f"{job_id}.csv"
    elif format == "shapefile":
        data = svc.to_shapefile(job.result_path)
        media_type, filename = "application/zip", f"{job_id}_shapefile.zip"
    else:
        raise HTTPException(400, "format must be geojson | csv | shapefile")

    return Response(
        content=data,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
```

---

### Task 2.5 — Fix thumbnail endpoint — serve JPEG not PNG
**Effort:** 1 h  
**Fixes:** Check 2.8  
**Files:** `interfaces/api.py`

Satellite patches are saved as PNG (GEE format). Convert to JPEG on-the-fly using Pillow.

```python
from PIL import Image
import io

@router.get("/api/v1/thumbnails/{grid_id}/{cell_id}.jpg")
async def get_thumbnail(grid_id: str, cell_id: int):
    png_path = f"data/sat_images/cell_{cell_id}.png"
    if not os.path.exists(png_path):
        raise HTTPException(404, "Thumbnail not found")
    img = Image.open(png_path).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return Response(content=buf.getvalue(), media_type="image/jpeg")
```

---

### Task 2.6 — Add POST /query stub — 501 Not Implemented
**Effort:** 0.5 h  
**Fixes:** Check 2.9  
**Files:** `interfaces/api.py`

The contract requires a 501 response, not a 404. Add the endpoint with full schema validation.

```python
from pydantic import BaseModel

class QueryRequest(BaseModel):
    question: str
    grid_id: str

@router.post("/api/v1/query")
async def natural_language_query(body: QueryRequest):
    raise HTTPException(
        status_code=501,
        detail="Natural language query is planned for v2 and not yet implemented."
    )
```

---

### Task 2.7 — Add input validation — 413 and 400 guards
**Effort:** 1 h  
**Fixes:** Check 2.10  
**Files:** `interfaces/api.py`, `schemas/load_area.py`

```python
# schemas/load_area.py
from pydantic import BaseModel, validator
from typing import Literal

class LoadAreaRequest(BaseModel):
    bbox: list[float]
    place_name: str | None = None
    grid_size: Literal[200, 500, 1000] = 500   # 400 if invalid value
    modalities: list[str] = ["poi", "image", "graph"]

    @validator("bbox")
    def bbox_must_be_valid(cls, v):
        if len(v) != 4:
            raise ValueError("bbox must have exactly 4 values: [min_lon, min_lat, max_lon, max_lat]")
        return v
```

```python
# interfaces/api.py — inside load_area handler, after grid generation
if num_cells > 500:
    raise HTTPException(
        status_code=413,
        detail=f"Area too large: {num_cells} cells exceed the 500-cell limit. Zoom in or increase grid_size."
    )
```

---

## Sprint 3 — Scalability Infrastructure
**Day 5 · Fixes checks 4.1 – 4.7 · Important**

Requires Sprint 1 to be complete (Redis must be running as Celery broker).

---

### Task 3.1 — Install and configure Celery with Redis broker
**Effort:** 4 h  
**Fixes:** Checks 4.1, 4.2  
**Files:** `celery_app.py`, `tasks/load_area.py`, `tasks/classify.py`

```python
# celery_app.py
from celery import Celery
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "mllm_geo_ai",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["tasks.load_area", "tasks.classify"]
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    task_routes={
        "tasks.classify.*": {"queue": "gpu"},
        "tasks.load_area.*": {"queue": "cpu"},
    }
)
```

```python
# tasks/load_area.py
from celery_app import celery_app
from infrastructure.redis_store import RedisJobStore

@celery_app.task(bind=True)
def load_area_task(self, job_id: str, bbox: list, grid_size: int, modalities: list):
    store = RedisJobStore()
    store.set_status(job_id, "running")
    store.set_progress(job_id, 0.1, "generating_grid")
    # ... pipeline logic ...
    store.set_status(job_id, "completed")
```

Add to `requirements.txt`:
```
celery[redis]>=5.3.0
```

---

### Task 3.2 — Replace BackgroundTasks with Celery enqueue
**Effort:** 1 h  
**Fixes:** Check 4.2  
**Files:** `interfaces/api.py`

```python
# Before
background_tasks.add_task(load_area_task, job_id, bbox, grid_size)

# After
from tasks.load_area import load_area_task as celery_load_area_task
celery_load_area_task.delay(job_id, bbox, grid_size, modalities)
```

FastAPI now returns 202 in under 10ms. The Celery worker handles the long-running work asynchronously.

---

### Task 3.3 — Batch image encoding — replace sequential loop
**Effort:** 2 h  
**Fixes:** Check 4.3  
**Files:** `infrastructure/image_encoder.py`, `application/fusion_service.py`

Add a `encode_batch` method to `ImageEncoder` that processes all cells in a single GPU forward pass.

```python
# infrastructure/image_encoder.py
def encode_batch(self, image_paths: list[str]) -> np.ndarray:
    """Encode N images in one forward pass. Returns (N, 256) array."""
    tensors = []
    for path in image_paths:
        img = Image.open(path).convert("RGB")
        tensors.append(self.transform(img))
    batch = torch.stack(tensors)          # shape: (N, 3, 224, 224)
    with torch.no_grad():
        embeddings = self.model(batch)    # shape: (N, 256)
    return embeddings.numpy()
```

```python
# application/fusion_service.py  — replace per-cell loop
image_paths = [f"data/sat_images/cell_{i}.png" for i in cell_indices]
image_embeddings = self.image_encoder.encode_batch(image_paths)  # single pass
```

---

### Task 3.4 — Cache POI embeddings in Redis per grid cell
**Effort:** 2 h  
**Fixes:** Check 4.5  
**Files:** `infrastructure/ai_model.py`

```python
# infrastructure/ai_model.py
import pickle

def encode_with_cache(self, text: str, grid_id: str, cell_idx: int) -> np.ndarray:
    cache_key = f"emb:poi:{grid_id}:{cell_idx}"
    cached = self.redis.get(cache_key)
    if cached:
        return pickle.loads(cached)
    embedding = self.model.encode(text)
    self.redis.set(cache_key, pickle.dumps(embedding))   # no TTL — persists until grid deleted
    return embedding
```

When a grid is deleted, flush its embedding keys: `redis.delete(*redis.keys(f"emb:poi:{grid_id}:*"))`.

---

### Task 3.5 — Confirm satellite patch cache guard is active
**Effort:** 0.5 h  
**Fixes:** Check 4.6  
**Files:** `infrastructure/satellite_loader.py`

This was implemented in Task 1.5. Verify the `if os.path.exists(save_path): continue` guard is present and the path is stable (not UUID-based). No code change needed if Task 1.5 is done.

---

### Task 3.6 — Add nginx config and Celery worker definitions
**Effort:** 2 h  
**Fixes:** Check 4.7  
**Files:** `nginx.conf`, `docker-compose.yml`

```nginx
# nginx.conf
upstream fastapi {
    server fastapi:8000;
}
server {
    listen 80;
    location / {
        proxy_pass http://fastapi;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    location /ws/ {
        proxy_pass http://fastapi;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

```yaml
# docker-compose.yml
version: "3.9"
services:
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  fastapi:
    build: .
    ports: ["8000:8000"]
    depends_on: [redis]
    environment:
      - REDIS_URL=redis://redis:6379/0

  celery-cpu-worker:
    build: .
    command: celery -A celery_app worker -Q cpu -c 4 --loglevel=info
    depends_on: [redis]
    environment:
      - REDIS_URL=redis://redis:6379/0

  celery-gpu-worker:
    build: .
    command: celery -A celery_app worker -Q gpu -c 1 --loglevel=info
    depends_on: [redis]
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    environment:
      - REDIS_URL=redis://redis:6379/0
```

---

## Sprint 4 — Scientific Output + Documentation
**Day 6 · Fixes checks 5.1 – 5.4 · Final**

---

### Task 4.1 — Write baseline evaluation script — POI + Random Forest
**Effort:** 2 h  
**Fixes:** Check 5.1  
**Files:** `evals/eval_baseline.py`

```python
# evals/eval_baseline.py
"""Evaluates the legacy POI-only + Random Forest pipeline on a held-out test split."""
import pandas as pd
import numpy as np
import json
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
from sklearn.model_selection import train_test_split
from app.infrastructure.ai_model import SentenceTransformerModel
from app.infrastructure.data_loader import DataLoader

LABEL_MAP = {"Residential": 0, "Commercial": 1, "Industrial": 2}

def main():
    df = pd.read_csv("data/raw/project.csv")
    _, test_df = train_test_split(df, test_size=0.2, random_state=42)

    model = SentenceTransformerModel()
    embeddings = model.encode_batch(test_df["text_description"].tolist())
    y_true = test_df["label"].map(LABEL_MAP).values

    # Load saved Random Forest (or retrain if not saved)
    import joblib
    clf = joblib.load("models/random_forest.pkl")
    y_pred = clf.predict(embeddings)

    results = {
        "accuracy": round(accuracy_score(y_true, y_pred), 4),
        "f1_macro": round(f1_score(y_true, y_pred, average="macro"), 4),
        "f1_per_class": f1_score(y_true, y_pred, average=None).round(4).tolist(),
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
    }
    with open("evals/baseline_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Baseline accuracy:", results["accuracy"])

if __name__ == "__main__":
    main()
```

---

### Task 4.2 — Write multi-modal evaluation script — MLP
**Effort:** 2 h  
**Fixes:** Check 5.2  
**Files:** `evals/eval_multimodal.py`

```python
# evals/eval_multimodal.py
"""Evaluates the new multi-modal POI + Image + Graph → MLP pipeline."""
import torch, json
import numpy as np
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
from sklearn.model_selection import train_test_split
import pandas as pd

LABEL_MAP = {"Residential": 0, "Commercial": 1, "Industrial": 2}

def main():
    df = pd.read_csv("data/raw/project.csv")
    _, test_df = train_test_split(df, test_size=0.2, random_state=42)

    from app.infrastructure.ai_model import SentenceTransformerModel
    from app.infrastructure.image_encoder import ImageEncoder
    from app.infrastructure.road_network import RoadNetworkLoader
    from app.domain.mlp_model import UrbanMLP

    poi_enc = SentenceTransformerModel()
    img_enc = ImageEncoder(embedding_dim=256)
    road_net = RoadNetworkLoader()    # assumes roads.graphml already loaded

    features, y_true = [], []
    for idx, row in test_df.iterrows():
        poi_emb = poi_enc.encode(row["text_description"])           # 384-dim
        img_emb = img_enc.encode(f"data/sat_images/cell_{idx}.png") # 256-dim
        graph_f = road_net.get_graph_features_for_grid(row["geometry"])  # 3-dim
        features.append(np.concatenate([poi_emb, img_emb, graph_f]))
        y_true.append(LABEL_MAP[row["label"]])

    X = torch.tensor(np.array(features), dtype=torch.float32)
    mlp = UrbanMLP(input_dim=643)
    mlp.load_state_dict(torch.load("models/urban_mlp.pt"))
    mlp.eval()
    with torch.no_grad():
        probs = mlp(X).numpy()
    y_pred = probs.argmax(axis=1)

    results = {
        "accuracy": round(accuracy_score(y_true, y_pred), 4),
        "f1_macro": round(f1_score(y_true, y_pred, average="macro"), 4),
        "f1_per_class": f1_score(y_true, y_pred, average=None).round(4).tolist(),
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
    }
    with open("evals/multimodal_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Multi-modal accuracy:", results["accuracy"])

if __name__ == "__main__":
    main()
```

---

### Task 4.3 — Run comparison and verify accuracy improvement
**Effort:** 2 h  
**Fixes:** Check 5.3  
**Files:** `evals/README.md`

Run both scripts and document results:

```bash
python evals/eval_baseline.py
python evals/eval_multimodal.py
```

If the multi-modal accuracy is equal to or lower than baseline:
1. Increase MLP training epochs (try 100 → 200).
2. Add label smoothing (`nn.CrossEntropyLoss(label_smoothing=0.1)`).
3. Try weighted loss if class imbalance is present.

Document final numbers in `evals/README.md`:

```markdown
# Evaluation Results

| Metric | Baseline (RF) | Multi-modal (MLP) | Delta |
|--------|-------------|-------------------|-------|
| Accuracy | X.XX | X.XX | +X.XX |
| F1 macro | X.XX | X.XX | +X.XX |
```

---

### Task 4.4 — Update Scientific_Analysis.md — 643-dim methodology
**Effort:** 1 h  
**Fixes:** Check 5.4  
**Files:** `docs/Scientific_Analysis.md`, `README.md`

Add a new subsection **3.3 — Multi-Modal Feature Vector** to `Scientific_Analysis.md`:

```markdown
### 3.3 Multi-Modal Feature Vector

The final input to the UrbanMLP classifier is a 643-dimensional concatenated vector
constructed from three independent encoders:

| Component | Encoder | Output dim |
|-----------|---------|-----------|
| POI semantic text | paraphrase-multilingual-MiniLM-L12-v2 | 384 |
| Satellite image patch | ResNet-18 (replaced FC layer) | 256 |
| Road graph features | OSMnx (node_count, road_length_m, avg_degree) | 3 |
| **Total input to UrbanMLP** | | **643** |

Each dimension is L2-normalized before concatenation to ensure equal contribution
across modalities regardless of scale differences.
```

Also update the model summary table in `README.md`.

---

### Task 4.5 — Fix test_road_network — align method name
**Effort:** 0.5 h  
**Fixes:** Warning 5.5  
**Files:** `infrastructure/road_network.py`, `tests/test_road_network.py`

The test calls `get_graph_features_for_geometry` but the verification spec expects `get_graph_features_for_grid`. Add an alias in `road_network.py` to satisfy both:

```python
# infrastructure/road_network.py
def get_graph_features_for_grid(self, grid_gdf):
    """Primary public method — used by fusion pipeline and tests."""
    return self._compute_features(grid_gdf)

# Alias for backward compatibility
get_graph_features_for_geometry = get_graph_features_for_grid
```

Update `tests/test_road_network.py` to call `get_graph_features_for_grid` directly.

---

### Task 4.6 — Final agent re-run and sign-off
**Effort:** 1 h  
**Fixes:** All domains  
**Files:** `VERIFICATION_REPORT_v2.md`

Re-run the full verification agent prompt against the patched codebase.

```bash
# Start services
docker-compose up -d redis
celery -A celery_app worker -Q cpu,gpu --loglevel=info &
uvicorn app.main:app --reload

# Run agent
# Paste agent prompt into your AI agent tool
# Save output to VERIFICATION_REPORT_v2.md
```

**Target score:** 32+ / 34 checks passed.  
Any remaining SKIPs should be filed as GitHub issues for v2.

---

## Sprint 5 — Model Training Pipeline
**Days 7-8 · Required for evaluation scripts to run**

The evaluation scripts require trained models. This sprint creates the training pipeline.

---

### Task 5.1 — Random Forest training script
**Effort:** 2 h  
**Files:** `scripts/train_baseline.py`

Create `scripts/train_baseline.py` that:
1. Loads `data/raw/project.csv`
2. Encodes text descriptions with SentenceTransformer
3. Trains RandomForestClassifier (n_estimators=100)
4. Saves to `models/random_forest.pkl`

```python
# scripts/train_baseline.py
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from app.infrastructure.ai_model import Embedder

def main():
    df = pd.read_csv("data/raw/project.csv")
    df = df.dropna(subset=["label", "text_description"])

    train_df, _ = train_test_split(df, test_size=0.2, random_state=42)

    embedder = Embedder()
    X = embedder.embed_texts(train_df["text_description"].tolist())
    y = train_df["label"].map({"Residential": 0, "Commercial": 1, "Industrial": 2})

    clf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    clf.fit(X, y)

    import os
    os.makedirs("models", exist_ok=True)
    joblib.dump(clf, "models/random_forest.pkl")
    print("Saved: models/random_forest.pkl")

if __name__ == "__main__":
    main()
```

---

### Task 5.2 — UrbanMLP training script
**Effort:** 3 h  
**Files:** `scripts/train_multimodal.py`

Create `scripts/train_multimodal.py` that:
1. Loads data and encodes all 3 modalities (POI + Image + Graph)
2. Trains UrbanMLP with early stopping
3. Saves to `models/urban_mlp.pt`

```python
# scripts/train_multimodal.py
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split
from app.infrastructure.ai_model import Embedder
from app.infrastructure.image_encoder import ImageEncoder
from app.domain.mlp_model import UrbanMLP

LABEL_MAP = {"Residential": 0, "Commercial": 1, "Industrial": 2}

def main():
    df = pd.read_csv("data/raw/project.csv")
    df = df.dropna(subset=["label", "text_description"])
    train_df, _ = train_test_split(df, test_size=0.2, random_state=42)

    poi_enc = Embedder()
    img_enc = ImageEncoder()

    features, labels = [], []
    for idx, row in train_df.iterrows():
        poi = poi_enc.embed_texts([row["text_description"]])[0]
        img = img_enc.encode(f"data/sat_images/cell_{idx}.png")
        graph = [0, 0, 0]  # placeholder
        features.append(torch.cat([torch.from_numpy(poi), torch.from_numpy(img), torch.tensor(graph)]))
        labels.append(LABEL_MAP[row["label"]])

    X = torch.stack(features).float()
    y = torch.tensor(labels)

    dataset = TensorDataset(X, y)
    loader = DataLoader(dataset, batch_size=32, shuffle=True)

    model = UrbanMLP(input_dim=643)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.CrossEntropyLoss()

    for epoch in range(100):
        model.train()
        for batch_x, batch_y in loader:
            optimizer.zero_grad()
            loss = criterion(model(batch_x), batch_y)
            loss.backward()
            optimizer.step()

    torch.save(model.state_dict(), "models/urban_mlp.pt")
    print("Saved: models/urban_mlp.pt")

if __name__ == "__main__":
    main()
```

---

### Task 5.3 — Unified training script
**Effort:** 1 h  
**Files:** `scripts/train.py`

Create a unified entry point:

```python
# scripts/train.py
"""Unified training script for all models."""
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=["baseline", "multimodal", "all"], default="all")
    args = parser.parse_args()

    if args.model in ["baseline", "all"]:
        print("Training baseline (RF)...")
        from scripts.train_baseline import main as train_rf
        train_rf()

    if args.model in ["multimodal", "all"]:
        print("Training multimodal (MLP)...")
        from scripts.train_multimodal import main as train_mlp
        train_mlp()

if __name__ == "__main__":
    main()
```

---

### Task 5.4 — Verify models saved
**Effort:** 0.5 h  
**Verification:**
```bash
ls -la models/
# Must show: random_forest.pkl, urban_mlp.pt
```

---

## Sprint 6 — Full Evaluation + Documentation
**Day 9 · Required to complete scientific output**

---

### Task 6.1 — Run baseline evaluation
**Effort:** 1 h  
**Files:** `evals/baseline_results.json`

```bash
python evals/eval_baseline.py
# Expected output: Baseline accuracy: X.XXXX
```

---

### Task 6.2 — Run multimodal evaluation
**Effort:** 1 h  
**Files:** `evals/multimodal_results.json`

```bash
python evals/eval_multimodal.py
# Expected output: Multi-modal accuracy: X.XXXX
```

---

### Task 6.3 — Create evals README with results table
**Effort:** 1 h  
**Files:** `evals/README.md`

```markdown
# Evaluation Results

| Metric | Baseline (RF) | Multi-modal (MLP) | Delta |
|--------|-------------|-------------------|-------|
| Accuracy | X.XX | X.XX | +X.XX |
| F1 macro | X.XX | X.XX | +X.XX |

## Notes
- Test split: 20% random_state=42
- Baseline: POI only (384-dim) + RandomForest
- Multi-modal: POI (384) + Image (256) + Graph (3) = 643-dim + MLP
```

---

### Task 6.4 — Verify multimodal > baseline
**Effort:** 1 h  

If multimodal accuracy <= baseline:
1. Retrain MLP with more epochs (200)
2. Add label smoothing
3. Re-run eval

---

## Sprint 7 — Production Integration
**Day 10 · Final production-ready validation**

---

### Task 7.1 — Start Celery CPU worker
**Effort:** 1 h  
```bash
celery -A celery_app worker -Q cpu -c 4 --loglevel=info &
```

---

### Task 7.2 — Start Celery GPU worker (optional)
**Effort:** 1 h  
```bash
celery -A celery_app worker -Q gpu -c 1 --loglevel=info &
```

---

### Task 7.3 — Full API integration test
**Effort:** 2 h  

```bash
# Start server
python -m app.main

# Run full test
curl -X POST http://localhost:8000/api/v1/load-area \
  -H "Content-Type: application/json" \
  -d '{"bbox":[31.1,29.9,31.3,30.1],"grid_size":500}'

# Poll until complete
curl http://localhost:8000/api/v1/area-status/{job_id}

# Run classification
curl -X POST http://localhost:8000/api/v1/classify \
  -H "Content-Type: application/json" \
  -d '{"grid_id":"{grid_id}"}'

# Get results
curl http://localhost:8000/api/v1/classification-result/{job_id}
```

---

### Task 7.4 — Create final verification report
**Effort:** 1 h  
**Files:** `VERIFICATION_REPORT_v2.md`

Document final state:
- Test results
- Verification score
- Any remaining issues

---

## Updated Requirements

Add these to `requirements.txt`:

```txt
# Sprint 1 — Persistence
redis>=5.0.0
sqlalchemy>=2.0.0
alembic>=1.13.0

# Sprint 3 — Scalability
celery[redis]>=5.3.0
```

---

## Updated Project Structure

```
MLLM_Geo_Ai/
├── app/
│   ├── main.py                          # lifespan DB wiring
│   ├── application/
│   │   ├── use_cases.py
│   │   ├── fusion_service.py            # + graph metrics + GeoJSON save
│   │   └── export_service.py            # NEW — GeoJSON/CSV/Shapefile
│   ├── domain/
│   │   ├── spatial_service.py
│   │   └── mlp_model.py
│   ├── infrastructure/
│   │   ├── ai_model.py                  # + Redis embedding cache
│   │   ├── data_loader.py
│   │   ├── db.py                        # NEW — SQLAlchemy engine + session
│   │   ├── redis_store.py               # NEW — Redis job store
│   │   ├── road_network.py              # + method alias fix
│   │   ├── satellite_loader.py          # + stable path + cache guard
│   │   └── image_encoder.py             # + encode_batch()
│   └── interfaces/
│       └── api.py                       # all contract fixes applied
├── models/
│   ├── grid.py                          # NEW — SQLAlchemy Grid model
│   └── job.py                           # NEW — SQLAlchemy Job model
├── schemas/
│   └── load_area.py                     # NEW — Pydantic validators
├── tasks/
│   ├── load_area.py                     # NEW — Celery task
│   └── classify.py                      # NEW — Celery task
├── evals/
│   ├── eval_baseline.py                 # NEW
│   ├── eval_multimodal.py               # NEW
│   └── README.md                        # NEW — results table
├── data/
│   ├── raw/project.csv
│   ├── sat_images/                      # stable path (was data/thumbnails/{uuid}/)
│   └── results/                         # NEW — {job_id}.geojson files
├── celery_app.py                        # NEW
├── nginx.conf                           # NEW
├── docker-compose.yml                   # NEW
├── requirements.txt                     # updated
├── .env
└── README.md                            # + 643-dim summary
```

---

## Verification Targets

After all 4 sprints are complete, re-run the agent. Expected outcome:

| Domain | Before | After |
|--------|--------|-------|
| Classification quality | 4/5 | 5/5 |
| API contracts | 4/10 | 10/10 |
| Data persistence | 0/6 | 6/6 |
| Scalability | 0/7 | 7/7 |
| Scientific output | 2/6 | 6/6 |
| **Overall** | **10/34** | **34/34** |

---

*End of build plan — generated 2026-04-26*