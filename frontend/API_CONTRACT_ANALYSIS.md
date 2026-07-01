# API Integration Contract Analysis

## Executive Summary
This document provides a comprehensive analysis of the expected backend API contracts for the Urban AI Dashboard. The frontend currently operates using a mock API client (`src/lib/api/mockClient.ts`), but expects a robust, asynchronous backend to handle heavy geographical data processing, Machine Learning model inference, and real-time WebSocket progress updates. 

## Frontend Architecture
The application is a React SPA built with Vite, TypeScript, and MapLibre GL for rendering geographical layers.
- **State Management**: Handled via Zustand (`src/store/dashboardStore.ts`), which stores the application configuration (grid size, modalities, ML model type) and current classification state.
- **Mock Client**: All backend calls are currently intercepted by `mockClient.ts` which simulates network latency, async processing, and event emission.
- **Layers**: Includes classification, POI, roads, OSMnx graph, and satellite layers.

## Page Analysis

### `Index.tsx`
- **User Actions**:
  - Load area (triggers POI/graph loading simulation)
  - Start classification (with modalities, model, and fusion preferences)
  - Cancel classification
- **Expected APIs**:
  - `POST /api/v1/classify`
  - WebSocket / SSE for progress (`Job Event Stream`)
- **State Requirements**: Loading steps, job progress, and streaming cell updates.

### `GridDetails.tsx`
- **User Actions**:
  - View specific cell details
  - Toggle road visibility
- **Expected APIs**:
  - `GET /api/v1/grid/{grid_id}/details`
- **State Requirements**: Fetches comprehensive statistics, graph metrics, and POI details for a specific cell.

### `TrainingLab.tsx` (Stub/Planned)
- **User Actions**: Upload labelled datasets, view live training curves.
- **Expected APIs**:
  - `POST /api/v1/train`
  - WebSocket for loss/metrics streaming.

### `DigitalTwin.tsx` (Stub/Planned)
- **User Actions**: Natural language querying.
- **Expected APIs**:
  - `POST /api/v1/query` (NL to Spatial Query).

## Component Analysis

### `Sidebar.tsx`
- **User Actions**: Configure classification settings, draw custom areas.
- **Expected APIs**: Relies heavily on the classification settings passed to the job API.
- **Calculations**: Frontend handles cell estimation (`estimateCells`), but might require a backend limit check in the future.

### `MapView.tsx`
- **User Actions**: View layers, click/double-click cells, draw bounding boxes.
- **Expected APIs**: 
  - `GET /api/v1/graph-topology`
- **State Requirements**: Requires GeoJSON geometries attached to cells, graph topology data (nodes/edges).

### `EvaluationPanel.tsx`
- **User Actions**: Upload ground truth files for evaluation.
- **Expected APIs**:
  - `POST /api/v1/evaluate`
- **State Requirements**: Needs evaluation metrics (accuracy, F1, confusion matrix).

### `CellDetailPanel.tsx`
- **User Actions**: Pin cells, view high-level stats on the map overlay.
- **Expected APIs**: Relies on data fetched during classification or grid details API.

## REST API Contracts

### 1. Classify Urban Area
- **Endpoint**: `POST /api/v1/classify`
- **Purpose**: Starts an asynchronous urban classification job.
- **Request DTO**:
  ```ts
  interface ClassifyRequest {
    grid_id: string;
    modalities: string[]; // "poi" | "image" | "graph" | "text"
    model_type: string; // "mlp" | "gnn"
    fusion_method: string; // "concat" | "weighted" | "attention"
    area_geometry?: { 
      type: "Polygon"; 
      coordinates: number[][][];
    } | null;
  }
  ```
- **Response DTO**:
  ```ts
  interface ClassifyResponse {
    job_id: string;
    status: string; // e.g., "pending" or "running"
    websocket_url?: string;
  }
  ```
- **Errors**: `400 Bad Request`, `422 Unprocessable Entity`, `500 Internal Server Error`
- **Called From**: `Index.tsx` -> `mockClient.ts (classify)`
- **Status**: Mocked.

### 2. Get Graph Topology
- **Endpoint**: `GET /api/v1/graph-topology` (or potentially scoped by grid ID `GET /api/v1/grid/{id}/graph-topology`)
- **Purpose**: Retrieves the OSMnx road network graph for rendering.
- **Response DTO**:
  ```ts
  interface GraphTopologyResponse {
    nodes: { id: string; lng: number; lat: number }[];
    edges: { from: string; to: string; coords: [number, number][] }[];
  }
  ```
- **Called From**: `MapView.tsx` -> `mockClient.ts (getGraphTopology)`
- **Status**: Mocked.

### 3. Get Cell Details
- **Endpoint**: `GET /api/v1/grid/{grid_id}/details`
- **Purpose**: Retrieves deep metrics and POIs for a specific cell.
- **Response DTO**:
  ```ts
  interface CellDetailsResponse {
    cell: CellDatum;
    pois: PoiPin[];
  }
  ```
- **Called From**: `GridDetails.tsx` -> `mockClient.ts (getCellDetails)`
- **Status**: Mocked.

## WebSocket Contracts

### Job Progress Stream
Currently implemented as an `EventEmitter` (`ClassifyJob`) on the frontend, which must be replaced by WebSocket or SSE.
- **Connection**: `ws://<domain>/ws/progress/{job_id}`
- **Client Events Sent**: (Optional, standard connection)
- **Server Events Expected**:
  ```json
  {
    "type": "step" | "batch" | "done" | "cancelled",
    "step": "downloading_poi" | "mapping_poi_to_nodes" | "building_graph" | "classifying", // optional
    "progress": 0.45, // optional (0.0 to 1.0)
    "cells": [ ...CellDatum ] // optional, sent during "batch" type
  }
  ```

## DTO Definitions

### `CellDatum`
```ts
interface CellDatum {
  id: string;
  row: number;
  col: number;
  class: string; // "Residential" | "Commercial" | "Industrial"
  confidence: number;
  confidences: Record<string, number>;
  top5_poi: string[];
  road_density: number;
  node_count: number;
  degree_centrality: number;
  clustering_coeff: number;
  total_road_length_m: number;
  graph_embedding_norm: number;
  text_embedding_norm: number;
  satellite_thumb: string; // URL
  geometry: { type: "Polygon"; coordinates: number[][][] };
  centroid: [number, number]; // [lng, lat]
}
```

### `PoiPin`
```ts
interface PoiPin {
  id: string;
  name: string;
  category: string;
  lat: number;
  lng: number;
  class: string; // "Residential" | "Commercial" | "Industrial"
}
```

## File Upload Contracts

### Evaluation Ground Truth Upload
- **Endpoint**: `POST /api/v1/evaluate`
- **Supported Formats**: `.csv`, `.geojson`, `.json`
- **Request**: Multipart Form Data (`file: File`)
- **Response DTO**:
  ```ts
  interface EvaluateResponse {
    accuracy: number;
    macro_f1: number;
    weighted_f1: number;
    spatial_accuracy: number;
    per_class_f1: Record<string, number>; // e.g. { "Residential": 0.85 }
    confusion_matrix: number[][]; // e.g. [[82, 8, 2], [5, 44, 6], ...]
    class_labels: string[]; // ["Residential", "Commercial", "Industrial"]
  }
  ```
- **Called From**: `EvaluationPanel.tsx` -> `mockClient.ts (evaluate)`

## Export Contracts
*No explicit export functionalities (CSV, PDF) are currently mapped in the MVP components.*

## Background Jobs
- **Classification**: Heavy task requiring async/batch streaming. Requires job creation, websocket progress, and cancellation endpoint (e.g., `DELETE /api/v1/jobs/{job_id}`).

## Missing APIs
| Endpoint | Used By | Status |
|---|---|---|
| `DELETE /api/v1/jobs/{job_id}` | `Index.tsx` (Cancel Job) | Missing |
| `POST /api/v1/train` | `TrainingLab.tsx` | Planned |
| `POST /api/v1/query` | `DigitalTwin.tsx` | Planned |

## Integration Risks
1. **WebSocket Stability**: The frontend expects a progressive stream of cells (`type: "batch"`). If the backend sends too large of a batch, it could freeze the MapLibre GL instance.
2. **Graph Size**: `getGraphTopology` currently returns nodes and edges synchronously. A large urban area graph could result in a massive JSON payload causing high latency. This needs to be paginated or streamed.
3. **Cancellation Mechanism**: The frontend allows cancelling a running classification. The backend must robustly terminate ML inference processes to prevent resource exhaustion.

## Backend Implementation Priority
1. **P0**: `POST /api/v1/classify` & WebSocket streaming.
2. **P1**: `GET /api/v1/grid/{grid_id}/details` (Needed for cell deep dives).
3. **P1**: `GET /api/v1/graph-topology`.
4. **P2**: `POST /api/v1/evaluate` (Ground truth evaluation).
5. **P3**: Job Cancellation API.

## Open Questions
- What are the file size limits for the `POST /api/v1/evaluate` upload?
- Does the backend require authentication or API keys for these endpoints? (Frontend currently does not inject any headers).
- How long are completed Job IDs retained on the backend?

## Complete Endpoint Matrix

| Method | Path | Component Source | Notes |
|---|---|---|---|
| POST | `/api/v1/classify` | `Index.tsx`, `Sidebar.tsx` | Initializes batch job |
| WS | `/ws/progress/{id}` | `Index.tsx` | Streams `ProgressEvent` |
| GET | `/api/v1/grid/{id}/details` | `GridDetails.tsx` | Fetch stats and POIs |
| GET | `/api/v1/graph-topology` | `MapView.tsx` | Fetches OSMnx nodes/edges |
| POST | `/api/v1/evaluate` | `EvaluationPanel.tsx` | Uploads ground truth |
| DELETE | `/api/v1/jobs/{id}` | `Index.tsx` | Cancels running job |
