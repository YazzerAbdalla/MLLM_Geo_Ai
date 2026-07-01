# Product Requirements Document (PRD) – Urban AI Dashboard

## 1. Introduction

### 1.1 Purpose
This document defines the requirements for the **Urban AI Dashboard**, a web‑based graphical user interface for the upgraded Multi‑Modal Urban Classification system. The dashboard enables urban planners, researchers, and GIS analysts to interactively select an area, run a multi‑modal (POI + satellite + road network) classification, visualise results on a map, query the model, and export data.

### 1.2 Scope
The UI will complement the existing FastAPI backend and will be developed as a standalone React application. It will communicate with the backend via REST APIs and WebSockets. The first release (MVP) will focus on area selection, classification execution, result visualisation, and data export. Advanced features (natural language query, training interface, ablation comparison) are planned for subsequent releases.

### 1.3 Target Users
- **Urban planner** – needs to quickly classify zones, compare scenarios, export maps.
- **GIS analyst** – wants to overlay classification with POI / road layers, download GeoJSON.
- **Researcher / student** – may run ablation studies, fine‑tune the model.
- **Developer** – may monitor system status and debug.

---

## 2. User Personas

| Persona | Goals | Pain Points |
|---------|-------|--------------|
| **Leila, Urban Planner** | Identify under‑served residential areas; export maps for reports. | Slow manual digitisation; lack of multi‑source data integration. |
| **Omar, GIS Analyst** | Compare POI‑only vs. multi‑modal results; overlay road density. | Needs to download results in GIS‑ready formats. |
| **Dr. Nour, Researcher** | Test fusion methods; fine‑tune the model with local labels. | No visual interface for training experiments. |
| **Karim, Developer** | Monitor API calls, view logs, test new endpoints. | Lack of integrated testing UI. |

---

## 3. User Stories

| ID | As a … | I want to … | So that … |
|----|--------|--------------|------------|
| US‑01 | Urban planner | draw a bounding box on a map or search for a city name | define my study area without writing code |
| US‑02 | GIS analyst | choose grid cell size (200m, 500m, 1000m) | control classification granularity |
| US‑03 | Any user | click a “Classify” button and see progress | understand when results are ready |
| US‑04 | Any user | see the classification result as a colour‑coded grid overlay | quickly identify zone types |
| US‑05 | Any user | click on any cell | see detailed classification scores, POI summary, satellite thumbnail, and road density |
| US‑06 | GIS analyst | toggle layers (results, POI heatmap, road network, satellite base map) | analyse spatial relationships |
| US‑07 | Urban planner | download the result as GeoJSON or Shapefile | use it in external GIS software |
| US‑08 | Researcher | run classification using different modality combinations (POI only, image only, all) | compare model performance (ablation) |
| US‑09 | Researcher | upload a labelled grid file and start a training job | fine‑tune the model with local data |
| US‑10 | Any user | type a natural language question like *“show residential areas with high road density”* | get intelligent filtered results (MLLM feature) |
| US‑11 | Any user | see a status bar with loading steps | know what the system is doing (downloading satellite, extracting features, etc.) |

---

## 4. Functional Requirements

### 4.1 Area Selection & Data Loading
| FR‑01 | The UI shall provide an interactive map (MapLibre GL) where the user can draw a rectangle to define the bounding box. |
| FR‑02 | The UI shall provide a search box that geocodes a place name (e.g., “Cairo, Egypt”) and centres the map on that location. |
| FR‑03 | Upon area selection, the UI shall call the backend to load POI, road network, and satellite imagery for that area. |
| FR‑04 | During loading, the UI shall display a progress indicator (e.g., “Loading roads…”, “Downloading satellite patches…”). |

### 4.2 Grid / Graph Configuration
| FR‑05 | The user shall be able to select a grid cell size from predefined options: 200m, 500m, 1000m (default 500m). |
| FR‑06 | An optional toggle shall allow switching from grid‑based to graph‑based (road intersection nodes) – advanced feature. |
| FR‑07 | After changing cell size, the UI shall update the grid preview overlay on the map. |

### 4.3 Classification Execution
| FR‑08 | A prominent **“Classify”** button shall trigger the multi‑modal classification pipeline on the backend. |
| FR‑09 | The UI shall show real‑time progress updates via WebSocket (e.g., “Extracting POI embeddings…”, “Encoding images…”, “Running GNN…”). |
| FR‑10 | The user shall be able to cancel a running classification job. |

### 4.4 Result Visualisation
| FR‑11 | The classification result shall be displayed as a coloured grid overlay: <br> – Residential: `#FFD966` (yellow/gold) <br> – Commercial: `#E63946` (red) <br> – Industrial: `#9B5DE5` (purple) |
| FR‑12 | A legend shall be shown on the map. |
| FR‑13 | When the user clicks on a grid cell, a side panel shall show: <br> – Dominant class and confidence (percentages for all three classes) <br> – Top 5 POI categories in that cell <br> – Thumbnail of the satellite patch (if available) <br> – Road density (km/km²) and node count |
| FR‑14 | The user shall be able to toggle the following layers on/off: <br> – Classification result <br> – POI heatmap (density of POIs) <br> – Road network (edges) <br> – Satellite base map (switch to satellite imagery as background) |

### 4.5 Export
| FR‑15 | The UI shall provide an **Export** button with format options: GeoJSON, Shapefile (zipped), CSV. |
| FR‑16 | The exported file shall contain for each cell: geometry, dominant class, confidence scores, cell ID, and optionally POI counts / road metrics. |
| FR‑17 | The user shall be able to export the current map view as PNG/PDF (via browser print or canvas capture). |

### 4.6 Natural Language Query (MLLM) – Future Release
| FR‑18 | A text input box shall allow users to ask questions like “show me residential areas near commercial zones”. |
| FR‑19 | The backend (with a small MLLM) shall interpret the query and return filtered cell IDs or a highlighted subset on the map. |

### 4.7 Training Interface – Advanced Release
| FR‑20 | A **“Training Lab”** page shall allow users to upload a labelled grid file (GeoJSON or CSV). |
| FR‑21 | Users shall be able to adjust hyperparameters (learning rate, fusion method, GNN layers) via form fields. |
| FR‑22 | The UI shall start an asynchronous training job and display loss/accuracy curves in real time. |
| FR‑23 | After training, the user can download the new model weights and apply them for classification. |

### 4.8 Ablation Comparison Mode
| FR‑24 | The user shall be able to select modality combinations: <br> – POI only <br> – Image only <br> – Graph only <br> – POI+Image <br> – All modalities |
| FR‑25 | The UI shall run classification for each selected combination and display side‑by‑side maps or a comparison table with accuracy metrics (if ground truth exists). |

### 4.9 System Status & Notifications
| FR‑26 | The UI shall show a persistent status bar (e.g., “Ready”, “Loading area…”, “Classifying…”, “Error: …”). |
| FR‑27 | Error messages shall be user‑friendly and suggest corrective actions (e.g., “Area too large – please select a smaller bounding box”). |

---

## 5. Non‑Functional Requirements

| NFR‑01 | **Performance** – Initial map load < 3 seconds. Classification result for a 10×10 grid (100 cells) shall be returned within 30 seconds on a typical laptop + GPU backend. |
| NFR‑02 | **Usability** – The interface shall be responsive on desktop screens (minimum 1280×720). Mobile support is not required for MVP. |
| NFR‑03 | **Reliability** – The UI shall handle backend failures gracefully (display error, allow retry). |
| NFR‑04 | **Scalability** – The frontend must be able to display up to 500 grid cells without major lag (use vector tiles or clustering for larger grids). |
| NFR‑05 | **Security** – All API calls shall be authenticated (API key or JWT) if deployed publicly. For local development, CORS shall be properly configured. |
| NFR‑06 | **Maintainability** – The code shall be modular (components, stores, API clients) and documented. |
| NFR‑07 | **Localisation** – UI text in English (Arabic optional for future). |

---

## 6. Technology Stack

| Layer | Technology | Justification |
|-------|------------|----------------|
| **Frontend Framework** | React 18 + Vite | Fast build, component‑based, large ecosystem. |
| **Mapping** | MapLibre GL (open source Mapbox fork) | Free, custom styling, supports GeoJSON layers, vector tiles. |
| **UI Components** | Mantine | Rich components, dark mode, accessible, hooks‑based. |
| **State Management** | Zustand | Minimal boilerplate, works well with React. |
| **Data Fetching / Caching** | TanStack Query (React Query) | Manages async state, caching, background refetch. |
| **HTTP Client** | Axios | Simple, interceptors for error handling. |
| **WebSocket** | native WebSocket API (or Socket.IO if needed) | Real‑time progress updates. |
| **Charting** (training curves) | Recharts | Lightweight, declarative. |
| **Code Editor** (training config) | Monaco Editor (optional) | For advanced users to edit hyperparameters in JSON. |
| **Styling** | CSS Modules + Mantine’s emotion | Scoped styles, maintainable. |
| **Build tool** | Vite | Fast HMR, easy proxy configuration for backend. |

### Backend (existing) additions
| Component | Technology | Purpose |
|-----------|------------|---------|
| Async tasks | Celery + Redis | Handle long classification / training jobs. |
| WebSocket endpoint | FastAPI WebSocket | Push progress updates to frontend. |
| File storage | Local filesystem (or S3) | Store satellite patches, exported files. |

---

## 7. Data Flow (Sequence)

1. **User selects area** → Frontend sends `POST /api/v1/load-area` with bbox.
2. Backend starts async task → returns `job_id`.
3. Frontend polls `GET /api/v1/area-status/{job_id}` or listens via WebSocket.
4. When loading completes, backend returns grid GeoJSON + metadata.
5. **User clicks “Classify”** → `POST /api/v1/classify` with grid ID, cell size, modality flags.
6. Backend runs feature extraction, fusion, GNN inference.
7. Progress messages sent via WebSocket (e.g., `{"step": "encoding_images", "progress": 0.4}`).
8. Result returned as GeoJSON with per‑cell classification.
9. Frontend overlays result on map.
10. **User clicks cell** → frontend shows detailed data from the result object.
11. **User exports** → `GET /api/v1/export/{job_id}?format=geojson` → download file.

---

## 8. API Endpoints (Frontend Expectations)

| Endpoint | Method | Request | Response | Used for |
|----------|--------|---------|----------|----------|
| `/api/v1/load-area` | POST | `{ "bbox": [lon_min, lat_min, lon_max, lat_max], "place_name": "optional" }` | `{ "job_id": "abc123" }` | Start data loading. |
| `/api/v1/area-status/{job_id}` | GET | – | `{ "status": "loading", "step": "downloading_satellite", "progress": 0.6 }` | Polling (fallback). |
| `/api/v1/ws/progress/{job_id}` | WebSocket | – | Streams progress JSON | Real‑time updates. |
| `/api/v1/classify` | POST | `{ "grid_id": "abc123", "cell_size": 500, "modalities": ["poi","image","graph"] }` | `{ "job_id": "xyz789" }` | Start classification. |
| `/api/v1/classification-result/{job_id}` | GET | – | GeoJSON FeatureCollection with `properties.class`, `properties.confidences` | Retrieve result. |
| `/api/v1/export/{job_id}` | GET | `?format=geojson` | File download | Export. |
| `/api/v1/query` (future) | POST | `{ "question": "show residential areas near industrial zones" }` | `{ "cell_ids": [ ... ] }` | Natural language query. |

---

## 9. UI Components (High‑Level)

| Component | Description |
|-----------|-------------|
| **MapView** | Wrapper for MapLibre map, handles bounding box drawing, grid overlay, layer toggling. |
| **ControlPanel** | Sidebar with area selection, grid size slider, Classify button, modality checkboxes, Export button. |
| **LayerToggle** | Buttons to show/hide POI heat, roads, satellite base map. |
| **ProgressBar** | Shows current step and percentage. |
| **CellDetailsPanel** | Slide‑in panel that appears when a cell is clicked; displays all details. |
| **QueryInput** (future) | Text input with suggestions, submit button. |
| **TrainingLabPage** (future) | File upload, hyperparameter form, live charts. |
| **ComparisonView** (future) | Two maps side‑by‑side for ablation. |
| **NotificationToast** | For success/error messages. |

---

## 10. Mockup Descriptions (Text)

### Main Dashboard
- **Top bar**: Title “Urban AI Dashboard”, dark/light mode toggle, user avatar (if auth).
- **Left sidebar (collapsible)**: ControlPanel. Contains:
  - “Area” section: search box, “Draw on map” button, current bbox coordinates.
  - “Grid” section: radio buttons (200m / 500m / 1000m).
  - “Modalities” section: checkboxes (POI, Image, Graph).
  - “Actions” section: [Classify] button (primary), [Export] dropdown.
  - “Layers” section: toggles for Results, POI heat, Roads.
- **Main area**: Full‑width map. Initially shows satellite base map. After classification, coloured grid appears.
- **Bottom status bar**: Text like “Ready – 512 cells loaded”.
- **Right side (hidden until cell click)**: CellDetailsPanel.

### After classification
- Grid cells are semi‑transparent coloured polygons.
- Clicking a cell opens right panel with:
  - **Class**: Residential (85%), Commercial (10%), Industrial (5%)
  - **Top POIs**: Café (12), School (3), Bank (2)
  - **Road density**: 4.2 km/km²
  - **Satellite thumbnail**: 128×128 pixel image
- Legend shows colour mapping.

### Training Lab (future)
- Left side: upload zone (drag & drop file), hyperparameter fields (learning rate, fusion type dropdown).
- Right side: live chart of loss vs. epoch.
- Bottom: [Start Training] button, logs output.

---

## 11. Acceptance Criteria (MVP)

- [ ] User can draw a bounding box and see the grid preview.
- [ ] User can start classification and see progress updates.
- [ ] After classification, coloured grid is displayed on the map.
- [ ] Clicking a cell shows correct detailed data (class, confidences, top POIs, road density).
- [ ] User can toggle results layer on/off.
- [ ] User can export results as GeoJSON and download the file.
- [ ] Error messages are shown when backend fails (e.g., invalid bbox).
- [ ] The UI is responsive on a 1920×1080 screen (no horizontal scroll).

---

## 12. Future Enhancements (Post‑MVP)

- Natural language query with small MLLM.
- Ablation comparison mode (side‑by‑side maps).
- Training interface with live metrics.
- User authentication and saving of analysis sessions.
- Mobile‑friendly layout.
- Integration with external data sources (population density, land use).

---

## 13. Risks & Mitigations

| Risk | Mitigation |
|------|-------------|
| Large area causes timeout (too many grid cells) | Limit bbox size on frontend; show warning if > 500 cells; implement paginated loading. |
| Satellite download fails (no images) | Fallback to blank patch; inform user. |
| WebSocket disconnects | Auto‑reconnect with exponential backoff; polling fallback. |
| MapLibre GL learning curve | Provide clear documentation and reusable component. |

---

## 14. Glossary

- **MLLM** – Multi‑Modal Large Language Model (small version used for queries).
- **GNN** – Graph Neural Network (used for spatial reasoning).
- **POI** – Point of Interest.
- **Grid cell** – Square polygon used as classification unit.
- **Ablation** – Running model with one or more modalities removed to measure contribution.

---

**Document version:** 1.0  
**Last updated:** 2026‑04‑17  
**Authors:** AI Engineering Team  
**Approvals:** Pending