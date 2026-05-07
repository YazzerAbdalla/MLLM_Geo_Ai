# Upgrade Plan: From POI-Only MLLM to Multi-Modal Geo-AI (Roads + Satellite + POI) – Google Earth Engine Edition

## Overview

Your current project uses **grid-based POI + text embeddings** to classify urban zones. The new requirements add:

- **Road network** (OSMnx) → Graph structure (nodes, edges) + graph features
- **Satellite imagery** (Google Earth Engine – free, no credit card) → Image patches per cell
- **Multi‑modal fusion** (POI + Image + Graph + optional Text)
- **GNN or small MLLM** instead of Random Forest

This plan **preserves your working code** while extending it step by step, using **Google Earth Engine (GEE)** as the free satellite source.

---

## Manual Prerequisites (One‑Time, Human Must Do)

Before any code runs, complete these steps:

1. **Register for Google Earth Engine** – [earthengine.google.com/signup](https://earthengine.google.com/signup) (free, no credit card)
2. **Create a Cloud Project** (e.g., `my-gee-project`)
3. **Enable Earth Engine API** in that project
4. **Register the project** at `https://code.earthengine.google.com/register?project=YOUR_PROJECT_ID`
   - Select non‑commercial, academic research, Community tier
5. **Authenticate locally**:
   ```bash
   pip install earthengine-api
   python -c "import ee; ee.Authenticate()"
   ```
6. **Test**:
   ```bash
   python -c "import ee; ee.Initialize(project='YOUR_PROJECT_ID'); print('GEE ready')"
   ```
7. **Store project ID** in `.env`:
   ```
   EARTH_ENGINE_PROJECT=your-project-id
   ```

---

## Phase 0: Understand the New Data Model

| Old (current) | New (target) |
|---------------|---------------|
| Grid cells (500m × 500m) | Grid cells (keep for simplicity) |
| POI counts + concatenated text | POI embeddings + image patch + graph features |
| Sentence‑Transformer → embedding | CNN for image + MLP/GNN for fusion |
| Random Forest classifier | MLP or GNN classifier |

For each grid cell, extract:
- POI embedding (existing)
- Satellite image patch (new, from GEE)
- Graph features from the road network inside the cell (new)

---

## Phase 1: Add Road Network Collection (OSMnx)

### 1.1 New dependency
```bash
pip install osmnx networkx
```

### 1.2 Create `infrastructure/road_network.py`

```python
import osmnx as ox
import geopandas as gpd
import numpy as np

class RoadNetworkLoader:
    def __init__(self, bbox=None, place_name=None):
        self.bbox = bbox  # (north, south, east, west)
        self.place_name = place_name
        self.G = None
        self.nodes_gdf = None
        self.edges_gdf = None

    def load(self):
        if self.bbox:
            north, south, east, west = self.bbox
            self.G = ox.graph_from_bbox(north, south, east, west, network_type='drive')
        else:
            self.G = ox.graph_from_place(self.place_name, network_type='drive')
        self.nodes_gdf, self.edges_gdf = ox.graph_to_gdfs(self.G)
        return self.G

    def save_graphml(self, path: str):
        ox.save_graphml(self.G, path)

    def get_graph_features_for_grid(self, grid_gdf: gpd.GeoDataFrame) -> np.ndarray:
        features = []
        for idx, cell in grid_gdf.iterrows():
            cell_edges = self.edges_gdf.clip(cell.geometry)
            cell_nodes = self.nodes_gdf.clip(cell.geometry)
            node_count = len(cell_nodes)
            total_length = cell_edges['length'].sum() if not cell_edges.empty else 0
            avg_degree = cell_nodes['street_count'].mean() if not cell_nodes.empty else 0
            features.append([node_count, total_length, avg_degree])
        return np.array(features)
```

---

## Phase 2: Satellite Imagery Collection with Google Earth Engine

### 2.1 New dependencies
```bash
pip install earthengine-api geemap requests python-dotenv
```

### 2.2 Create `infrastructure/satellite_loader.py`

```python
import ee
import requests
import io
import os
from PIL import Image
import geopandas as gpd
from dotenv import load_dotenv

load_dotenv()

class SatelliteImageLoader:
    def __init__(self, bbox=None, place_name=None):
        # Initialize GEE with project from environment
        project_id = os.getenv('EARTH_ENGINE_PROJECT')
        if not project_id:
            raise ValueError("EARTH_ENGINE_PROJECT not set in .env")
        ee.Initialize(project=project_id)
        self.bbox = bbox  # (min_lon, min_lat, max_lon, max_lat)
        self.place_name = place_name

    def download_for_grid(self, grid_gdf: gpd.GeoDataFrame, output_dir: str, radius_m=250):
        """Download one 256x256 satellite image per grid cell using GEE getThumbURL."""
        os.makedirs(output_dir, exist_ok=True)
        for idx, cell in grid_gdf.iterrows():
            lon, lat = cell.geometry.centroid.x, cell.geometry.centroid.y
            region = ee.Geometry.Point([lon, lat]).buffer(radius_m).bounds()
            # Get median Sentinel-2 image (cloud filtered)
            image = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
                .filterBounds(region) \
                .filterDate('2023-01-01', '2023-12-31') \
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
                .median() \
                .clip(region)
            url = image.getThumbURL({
                'region': region,
                'dimensions': [256, 256],
                'format': 'png',
                'bands': ['B4', 'B3', 'B2'],  # RGB
                'min': 0,
                'max': 3000
            })
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                img = Image.open(io.BytesIO(response.content))
                img.save(f"{output_dir}/cell_{idx}.png")
            else:
                print(f"Failed cell {idx}: HTTP {response.status_code}")
```

---

## Phase 3: Image Feature Extraction (CNN)

### 3.1 Create `infrastructure/image_encoder.py`

```python
import torch
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
import numpy as np

class ImageEncoder:
    def __init__(self, embedding_dim=256):
        self.model = models.resnet18(weights='DEFAULT')
        self.model.fc = torch.nn.Linear(512, embedding_dim)
        self.model.eval()
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225])
        ])

    def encode(self, image_path: str) -> np.ndarray:
        img = Image.open(image_path).convert('RGB')
        img_t = self.transform(img).unsqueeze(0)
        with torch.no_grad():
            emb = self.model(img_t).squeeze().numpy()
        return emb
```

---

## Phase 4: Multi‑Modal Fusion (per grid cell)

### 4.1 Modify `domain/spatial_service.py` – add fusion method

```python
# Inside SpatialService class
def create_multimodal_feature(self, poi_embedding: np.ndarray,
                               image_embedding: np.ndarray,
                               graph_features: np.ndarray) -> np.ndarray:
    return np.concatenate([poi_embedding, image_embedding, graph_features])
```

### 4.2 Update `application/use_cases.py`

```python
class MultiModalClassificationUseCase:
    def __init__(self, poi_encoder, image_encoder, road_network, classifier):
        self.poi_encoder = poi_encoder
        self.image_encoder = image_encoder
        self.road_network = road_network
        self.classifier = classifier

    def execute(self, grid_cells):
        features = []
        for cell in grid_cells:
            poi_emb = self.poi_encoder.encode(cell.text_des)
            img_emb = self.image_encoder.encode(f"data/sat_images/cell_{cell.id}.png")
            graph_feat = self.road_network.get_graph_features_for_grid(cell.geometry)
            fused = np.concatenate([poi_emb, img_emb, graph_feat])
            features.append(fused)
        return self.classifier.predict(np.array(features))
```

---

## Phase 5: Model Upgrade – MLP (Simpler than GNN for MVP)

Start with a simple MLP. GNN can be added later.

### 5.1 Create `infrastructure/mlp_model.py`

```python
import torch.nn as nn
import torch.nn.functional as F

class UrbanMLP(nn.Module):
    def __init__(self, input_dim, hidden_dim=128, output_dim=3):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, output_dim),
            nn.Softmax(dim=1)
        )

    def forward(self, x):
        return self.net(x)
```

Training script will be added in Phase 6.

---

## Phase 6: Integrate into Existing API

### 6.1 Update `interfaces/api.py` with new endpoints

```python
from fastapi import BackgroundTasks
from app.application.use_cases import MultiModalClassificationUseCase

@router.post("/api/v1/load-area")
async def load_area(bbox: list, grid_size: int = 500):
    job_id = create_job()
    background_tasks.add_task(load_area_task, job_id, bbox, grid_size)
    return {"job_id": job_id}

@router.post("/api/v1/classify")
async def classify(job_id: str):
    result = classification_use_case.execute(job_id)
    return {"job_id": job_id, "status": "completed"}

@router.get("/api/v1/classification-result/{job_id}")
async def get_result(job_id: str):
    return geojson_result

@router.get("/api/v1/export/{job_id}")
async def export_result(job_id: str, format: str = "geojson"):
    return file_response
```

### 6.2 Keep old endpoint for backward compatibility

---

## Phase 7: Project Structure

```
MLLM_Geo_Ai/
├── app/
│   ├── main.py
│   ├── application/
│   │   ├── use_cases.py           # modified
│   │   └── fusion_service.py      # new
│   ├── domain/
│   │   ├── spatial_service.py     # modified
│   │   └── mlp_model.py           # new (instead of GNN for MVP)
│   ├── infrastructure/
│   │   ├── ai_model.py            # unchanged
│   │   ├── data_loader.py         # unchanged
│   │   ├── road_network.py        # new
│   │   ├── satellite_loader.py    # new (GEE version)
│   │   └── image_encoder.py       # new
│   └── interfaces/
│       └── api.py                 # modified
├── data/
│   ├── raw/
│   │   ├── project.csv
│   │   └── roads.graphml
│   └── sat_images/
├── models/
│   ├── sentence_transformer/
│   └── urban_mlp.pt
├── requirements.txt
├── .env                           # EARTH_ENGINE_PROJECT=...
└── README.md
```

---

## Phase 8: Testing & Validation

### 8.1 Unit tests
- `tests/test_road_network.py`
- `tests/test_satellite_loader.py` (mock GEE)
- `tests/test_image_encoder.py`
- `tests/test_fusion.py`

### 8.2 Integration test
- Small bounding box (2×2 km) → download roads + satellite → fuse → train MLP → evaluate.

### 8.3 Compare old vs new
- Old: POI + text → Random Forest
- New: POI + Image + Graph → MLP
- Measure accuracy improvement.

---

## Implementation Order (Recommended)

| Week | Task | Dependencies |
|------|------|--------------|
| 1 | OSMnx road network + per‑cell features | – |
| 2 | GEE satellite download per cell | Week 1 grid |
| 3 | Image encoder (ResNet) | Week 2 |
| 4 | Graph features, fusion, MLP training | Weeks 1,3 |
| 5 | FastAPI endpoints + job management | Week 4 |
| 6 | Streamlit UI (or React) | Week 5 |
| 7 | Testing, comparison, demo | All |

---

## Required `requirements.txt`

```txt
# Existing
pandas
geopandas
sentence-transformers
scikit-learn
fastapi
uvicorn

# New for multi‑modal
osmnx==1.9.1
networkx==3.2.1
earthengine-api>=0.1.400
geemap>=0.30.0
torch==2.1.0
torchvision==0.16.0
pillow==10.1.0
requests==2.31.0
streamlit==1.28.0
folium==0.14.0
streamlit-folium==0.15.0
python-dotenv>=1.0.0
```
