# Architecture Documentation | Date: 2025-05-07 | MLLM-Geo-AI Project

---

## 5.1 What This System Does (Plain English)

Imagine you're a city planner. You want to know what type of area each part of Cairo is - is it mostly homes, shops, or factories?

Here's what this system does:

1. **You draw a box** on a map (like selecting a rectangle on Google Maps)
2. **The system gathers data** for that box:
   - **Place names** (POIs): "school", "hospital", "mosque" - like a list of what's in each area
   - **Satellite photos**: Pictures taken from space showing what the ground looks like
   - **Road network**: The streets, highways, and how they connect
3. **The system cuts your box** into 500m × 500m squares (like a chessboard)
4. **For each square**, the AI decides: is this Residential, Commercial, or Industrial?
5. **You get a colored map** you can export - green for homes, blue for shops, red for factories

**Why is this useful?**
- Urban planners can see how a city is organized
- Real estate developers can find commercial zones
- Traffic engineers can understand road connectivity
- Emergency responders can plan routes based on area types

---

## 5.2 Folder Structure & Why

```
MLLM_Geo_Ai/
├── app/                          # Main application code
│   ├── main.py                   # Entry point - starts FastAPI server
│   ├── config.py                 # Settings (POI_DIM=384, IMG_DIM=256, etc.)
│   ├── application/              # "The Manager" - orchestrates work
│   │   ├── fusion_service.py    # Runs the classification pipeline
│   │   ├── use_cases.py         # Business use cases
│   │   └── export_service.py     # Converts results to different formats
│   ├── domain/                   # "The Brain" - business rules
│   │   ├── spatial_service.py   # Grid generation, coordinate math
│   │   └── mlp_model.py          # Neural network classifier
│   ├── infrastructure/           # "The Hands" - talks to outside world
│   │   ├── ai_model.py          # Loads sentence-transformers
│   │   ├── image_encoder.py     # Loads ResNet-18
│   │   ├── road_network.py      # Loads OSMnx graphs
│   │   ├── satellite_loader.py  # Downloads from Google Earth Engine
│   │   ├── data_loader.py       # Reads CSV files
│   │   ├── db.py                # SQLite database connection
│   │   ├── job_store.py         # Manages job tracking
│   │   └── redis_store.py       # Redis for fast job status
│   └── interfaces/              # HTTP endpoints
│       └── api.py              # FastAPI routes
├── tasks/                        # Celery background tasks
│   ├── load_area.py            # Downloads POI, roads, satellite
│   └── classify.py             # Runs classification
├── models/                      # Saved AI models
│   ├── urban_mlp.pt            # Trained MLP classifier
│   └── sentence_transformer/  # MiniLM model files
├── data/                        # Data files
│   ├── raw/project.csv         # POI training data
│   ├── results/                # Classification results (GeoJSON)
│   └── sat_images/             # Downloaded satellite patches
├── tests/                       # Test files
├── reports/                     # Generated reports
├── scripts/                     # Utility scripts
├── celery_app.py              # Celery configuration
├── requirements.txt            # Python dependencies
└── .env                        # Environment variables
```

**Why this structure?**
- **app/** is the main code following Domain-Driven Design (DDD)
- **tasks/** is for background jobs (separate from web server)
- **models/** holds trained AI weights (separate from code)
- **data/** holds user data (separate from code)
- **tests/** holds tests (separate from code)
- **scripts/** holds utility scripts (not part of web app)

If you delete any folder:
- Delete `models/` → classification won't work
- Delete `data/` → no data to classify
- Delete `app/domain/` → no business logic
- Delete `app/infrastructure/` → can't load data or run AI

---

## 5.3 Domain-Driven Design: The Three Layers

### The Analogy

Think of a restaurant:
- **Domain** = The Chef - knows what makes a good meal, but doesn't cook
- **Application** = The Manager - tells the chef what to cook and when
- **Infrastructure** = The Kitchen - has the oven, pots, and knows how to use them

### The Three Layers

| Layer | Name | What It Does | What It Doesn't Know |
|-------|------|--------------|----------------------|
| Domain | The Brain | Business rules: what is a residential area? how to generate a grid? | Databases, AI models, the internet |
| Application | The Manager | Orchestration: load data → encode → classify → save result | How to talk to Redis or load models |
| Infrastructure | The Hands | External systems: load CSV, run AI model, save to disk | Business rules |

### ASCII Diagram - How a Request Flows

```
USER → FASTAPI (Interfaces) → Application (Manager)
                              ↓
                    Domain (Brain) - "Is this residential?"
                              ↓
                    Infrastructure (Hands) - Load AI model, run inference
                              ↓
                    USER gets result
```

**Key Rule**: Domain NEVER imports from Infrastructure.
- ✅ `domain/spatial_service.py` can import from `domain/mlp_model.py`
- ✅ `infrastructure/ai_model.py` can import from `domain/mlp_model.py`
- ❌ `domain/spatial_service.py` cannot import from `infrastructure/db.py`

---

## 5.4 The Data Flow: Step by Step

When a user calls `POST /api/v1/classify`, here's exactly what happens:

```
Step 1:  HTTP Request arrives at FastAPI (app/interfaces/api.py)
Step 2:  FastAPI validates the request using Pydantic (checks: grid_id, modalities)
Step 3:  FastAPI creates a job record in Redis: job:{uuid}:status = "pending"
Step 4:  FastAPI enqueues a Celery task: classify_task.delay(job_id, grid_id, modalities)
Step 5:  FastAPI immediately returns 202 + job_id (doesn't wait!)
Step 6:  Celery worker picks up the task from the queue
Step 7:  Worker loads grid from storage (SQLite or Redis cache)
Step 8:  Worker runs POI embedding via sentence-transformer (384-dim)
Step 9:  Worker loads satellite image patch for each cell (from disk)
Step 10: Worker encodes image via ResNet-18 (256-dim)
Step 11: Worker computes road graph features: node_count, total_length, avg_degree (3-dim)
Step 12: Worker fuses: concat([poi_emb, img_emb, graph_feat]) = 643-dim vector
Step 13: Worker runs MLP classifier → outputs [p_res, p_com, p_ind] probabilities
Step 14: Worker serializes result as GeoJSON
Step 15: Worker saves GeoJSON to data/results/{job_id}.geojson
Step 16: Worker updates Redis: job:{job_id}:status = "completed", progress = 1.0
Step 17: Frontend polls GET /classify-status/{job_id} → sees "completed"
Step 18: Frontend fetches GET /classification-result/{job_id} → shows colored map
```

**Total time**: 30-60 seconds for 100 cells (async, user doesn't wait)

---

## 5.5 Redis: What It Stores and Why

### Why Redis?

Think of Redis as a **super-fast bulletin board** in your kitchen.

- **Database is like a filing cabinet** - great for long-term storage, but slow to check
- **Redis is like a whiteboard** - you can write and read instantly

We use Redis for job status because:
1. **It updates many times per second** (loading → encoding → classifying → done)
2. **The data is temporary** - once job is done, we read from file
3. **It supports pub/sub** - can notify frontend when job completes

### Redis Key Schema

| Key Pattern | Type | Example | Purpose |
|-------------|------|---------|---------|
| job:{job_id}:status | String | "pending" \| "running" \| "completed" \| "failed" | Current state |
| job:{job_id}:progress | Float | "0.0" → "0.5" → "1.0" | 0-100% complete |
| job:{job_id}:step | String | "encoding_images" | What it's doing now |
| job:{job_id}:type | String | "load" \| "classify" | What kind of job |
| job:{job_id}:grid_id | String | "grid_abc123" | Result grid ID |
| job:{job_id}:error | String | "GEE download failed" | Error message |
| grid:{grid_id}:cells | String (GeoJSON) | "{"type":"FeatureCollection"..." | Cached grid (optional) |

### Example Session

```python
# User starts classification
redis.set("job:abc123:status", "pending")
redis.set("job:abc123:progress", "0.0")

# Worker starts
redis.set("job:abc123:status", "running")
redis.set("job:abc123:step", "loading_grid")
redis.set("job:abc123:progress", "0.1")

# Worker encoding
redis.set("job:abc123:step", "encoding_poi")
redis.set("job:abc123:progress", "0.3")

# Worker done
redis.set("job:abc123:status", "completed")
redis.set("job:abc123:progress", "1.0")
```

---

## 5.6 Celery: Why We Use a Task Queue

### The Problem

If classifying 144 grid cells takes 30 seconds, and a web request must respond in <5 seconds, what do we do?

### The Restaurant Analogy

```
WITHOUT Celery (bad):
─────────────────────
You: "I'd like the special" → Waiter cooks for 30 minutes → You wait → Finally eat
→ You leave angry (timeout!)

WITH Celery (good):
────────────────────
You: "I'd like the special" → Waiter gives you ticket #42 → You sit and read
→ Waiter checks ticket #42 periodically → "Your order is ready!"
→ You eat and leave happy
```

### Celery Terms

| Term | What It Is | In Our App |
|------|------------|------------|
| Broker | The message queue | Redis |
| Worker | The background process | celery worker command |
| Task | A job to do | load_area_task, classify_task |
| Queue | Where tasks wait | "cpu" queue, "gpu" queue |

### Our Two Queues

```python
task_routes = {
    "tasks.classify.*": {"queue": "gpu"},      # Heavy ML work
    "tasks.load_area.*": {"queue": "cpu"},     # Data downloads
}
```

- **CPU queue**: For grid generation, downloading data (light work)
- **GPU queue**: For image encoding, running neural networks (heavy work)

### Starting Celery

```bash
# Start CPU worker
celery -A celery_app worker -Q cpu --loglevel=info

# Start GPU worker
celery -A celery_app worker -Q gpu --loglevel=info
```

---

## 5.7 Database: What We Store and Why

### Where Data Goes

| What | Where | Why |
|------|-------|-----|
| Grid geometry (bbox, cell polygons) | SQLite (mllm_geo_ai.db) | Needs spatial queries, persists forever |
| Job status & progress | Redis | Temporary, needs ultra-fast updates |
| Classification results | Filesystem (data/results/*.geojson) | Too large for DB, referenced by job_id |
| Satellite image patches | Filesystem (data/sat_images/*.png) | Binary, served as static files |
| Model weights | Filesystem (models/*.pt) | Binary, versioned |

### Database Schema (SQLite)

```python
# Tables created in app/infrastructure/db.py

class Grid(Base):
    id = Column(String, primary_key=True)  # UUID
    bbox = Column(JSON)  # [min_lon, min_lat, max_lon, max_lat]
    grid_size_m = Column(Integer)  # 200|500|1000
    num_cells = Column(Integer)
    created_at = Column(DateTime)
    status = Column(String)  # "loading"|"ready"|"error"

class Job(Base):
    id = Column(String, primary_key=True)  # UUID
    type = Column(String)  # "load"|"classify"|"train"
    grid_id = Column(String, ForeignKey("grids.id"))
    status = Column(String)  # "pending"|"running"|"completed"|"failed"
    progress = Column(Float)  # 0..1
    step = Column(String)  # Current step description
    result_path = Column(String)  # File path
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
```

### Current Status

**Note**: Grid storage is not fully implemented. Currently:
- Jobs stored in Redis (but not SQLite)
- Grid data stored in memory/Redis
- Need to implement SQLite storage for production

---

## 5.8 The AI Pipeline in Plain English

### The Four AI Components

#### 1. Sentence Transformer (MiniLM-L12-v2)
**What it does**: Takes text like "school, pharmacy, mosque" and turns it into 384 numbers.

**How to think about it**: Two neighborhoods with similar places will have similar numbers.
- "school, hospital" → [0.1, -0.3, 0.5, ...384 numbers...]
- "university, clinic" → [0.12, -0.29, 0.52, ...similar!...]
- "factory, warehouse" → [0.9, 0.8, -0.2, ...different!...]

#### 2. ResNet-18 CNN
**What it does**: Takes a 256×256 satellite photo and produces 256 numbers describing the image.

**How to think about it**: It learns what different land looks like from above.
- Green parks → certain pattern of numbers
- Gray buildings → different pattern
- Roads grid → another pattern

#### 3. Graph Features (OSMnx)
**What it does**: Counts roads, intersections, and measures connectivity.

**Simple 3 numbers**:
- `node_count`: How many intersections?
- `total_length`: How many km of road?
- `avg_degree`: How connected is each intersection?

#### 4. Fusion (Concatenation)
**What it does**: Stacks all numbers side by side.

```
[384 POI numbers] + [256 Image numbers] + [3 Graph numbers] = 643 numbers
```

#### 5. MLP Classifier
**What it does**: Takes the 643 numbers and outputs 3 probabilities.

```
643 numbers → [p_residential, p_commercial, p_industrial]
            → e.g., [0.85, 0.10, 0.05] = "Residential!"
```

**Training**: The MLP learns which patterns of numbers correspond to which land use.

---

## 5.9 Spatial Coordinate System: Why EPSG:32636?

### The Problem

Maps use degrees (latitude/longitude), but you can't measure meters in degrees.

**Why?**
- 1 degree of latitude ≈ 111 km (always)
- 1 degree of longitude ≈ 111 km × cos(latitude) (varies!)

At Cairo (30°N):
- 1° latitude ≈ 111 km
- 1° longitude ≈ 96 km

If you say "500m grid", in degrees that's:
- 500m / 111km = 0.0045° (north-south)
- 500m / 96km = 0.0052° (east-west)

### The Solution: UTM Zone 36N (EPSG:32636)

UTM projects Earth's surface onto a flat grid measured in meters.

**EPSG:32636** covers Egypt (including Cairo).

### The Conversion

```python
# WGS84 (degrees) → UTM (meters)
grid_gdf = grid_gdf.to_crs("EPSG:32636")

# Now we can:
width_m = max_x - min_y  # Actual meters!
cells = ceil(width_m / 500)  # Exactly 500m cells

# UTM (meters) → WGS84 (degrees) for display
grid_gdf = grid_gdf.to_crs("EPSG:4326")  # Return to degrees for GeoJSON
```

### Always Remember

1. **Input**: User gives degrees (WGS84)
2. **Convert**: degrees → meters (EPSG:32636)
3. **Process**: Generate grid in meters
4. **Output**: Convert meters → degrees (EPSG:4326) for GeoJSON

---

*Documentation created: 2025-05-07*
*Project: MLLM-Geo-AI Urban Classification System*
*For: Junior developers learning the codebase*