# Test Artifacts

**Date:** 2026-06-17  

---

## Generated Test Files

| File | Purpose | Status |
|------|---------|--------|
| `data/temp/ground_truth.geojson` | Evaluation test (GeoJSON) | Created |
| `data/temp/ground_truth_correct.geojson` | Evaluation test (corrected) | Created |
| `data/temp/invalid_gt.geojson` | Evaluation test (invalid) | Created |
| `data/temp/ground_truth.csv` | Evaluation test (CSV) | Created |
| `data/temp/invalid_gt.csv` | Evaluation test (invalid CSV) | Created |

---

## API Responses

### Health Check
```json
{"status":"ok","app":"MLLM-Geo-AI-App","redis":"ok","job_store_mode":"redis"}
```

### Area Load Response
```json
{"job_id":"228c5e8b-0ae5-4f85-8e79-23582e22acc0","status_url":"/api/v1/area-status/...","websocket_url":"ws://localhost:8000/api/v1/ws/progress/..."}
```

### Area Status (Completed)
```json
{"job_id":"228c5e8b-...","status":"completed","step":"done","progress":1.0,"error":null,"grid_id":"grid_228c5e8b","num_cells":0,"geojson_preview_url":"/api/v1/grid/grid_228c5e8b/preview"}
```

### Grid Details
```json
{"grid_id":"grid_228c5e8b","bbox":[31.2,30.0,31.22,30.02],"cell_count":25,"road_density":12050.046625976562,"poi_count":0,"graph_stats":{"nodes":2070,"edges":0}}
```

### Classification Response (All Modalities - Sample Cell)
```json
{
  "cell_id": 0,
  "dominant_class": "Industrial",
  "confidence": 1.0,
  "confidences": {"residential": 0.0, "commercial": 0.0, "industrial": 1.0},
  "road_density": 802693272762.2891,
  "node_count": 84,
  "degree_centrality": 0.0,
  "clustering_coeff": 0.0,
  "total_road_length_m": 16287.0966796875,
  "poi_top_categories": [],
  "text_embedding_norm": 0.0,
  "graph_embedding_norm": 16287.3134765625,
  "geometry": {"type": "Polygon", "coordinates": [[[31.2045, 30.0], [31.2045, 30.0045], [31.2, 30.0045], [31.2, 30.0], [31.2045, 30.0]]]},
  "centroid": [30.00225, 31.20225],
  "satellite_thumbnail_url": "/api/v1/thumbnails/grid_228c5e8b/0.jpg"
}
```

### Grid Preview
- **Features:** 25
- **Format:** GeoJSON FeatureCollection
- **Properties:** geometry only (cell_id added during classification)

### Training Status (Failed - Missing Dataset)
```json
{"job_id":"7c2f880d-...","status":"failed","step":"failed","progress":0.05,"error":"Dataset not found: data/nonexistent.csv"}
```

### Evaluation Response (Broken)
```json
{"detail":"Could not detect prediction label column. Tried: ['predicted_label', 'prediction', 'pred_label', 'class', 'label', 'land_use', 'landuse', 'category']"}
```

---

## Celery Tasks Registered

| Task Name | Queue | Module |
|-----------|-------|--------|
| `tasks.load_area.load_area_task` | cpu | `tasks/load_area.py` |
| `tasks.classify.classify_task` | gpu | `tasks/classify.py` |
| `tasks.train_mllm.train_mllm_task` | gpu | `tasks/train_mllm.py` |

---

## Database Contents

### SQLite (`mllm_geo_ai.db`)

**Table: grids** (24 rows)
- `id` (TEXT) - Grid UUID
- `bbox` (TEXT) - JSON array of bbox
- `grid_size_m` (INTEGER) - Always 500
- `num_cells` (INTEGER) - 25 or 36
- `created_at` (TEXT) - Timestamp
- `status` (TEXT) - "completed"

**Table: jobs** (0 rows)
- Empty - jobs stored in Redis only

### Redis (441 keys)
- Patterns: `job:{uuid}:{field}`
- 17 keys per job (status, progress, step, type, error, grid_id, celery_task_id, num_cells, result_url, result_data, etc.)
- ~25 completed jobs in history
