# Urban AI Dashboard

A GIS-style research tool for multi-modal urban land-use classification. The dashboard lets analysts draw a bounding box over Cairo, load a street-graph-aware grid, select which data modalities to fuse (POI, satellite imagery, road graph, text), run a classification job, and inspect per-cell results — all without a live backend. Every API call is intercepted by a structured mock layer that mirrors the shape of a real FastAPI service, so the UI can be demonstrated and tested before any ML infrastructure exists.

Built as part of an academic pipeline (Step 2) covering OSMnx road-graph extraction, MLLM POI embeddings, Sentinel-2 imagery, multi-modal fusion, and GNN vs MLP model comparison.

---

## Status

| Phase | Description | State |
|---|---|---|
| 0 | Project scaffolding | ✅ Complete |
| 1 | Layout & map shell | ✅ Complete |
| 2 | Left sidebar controls | ✅ Complete |
| 3 | Classification engine | ✅ Complete |
| 4 | Evaluation panel | ✅ Complete |
| 5 | Layer controls & URL persistence | ✅ Complete |
| 6 | Step 2 alignment fixes | ✅ Complete |
| 7 | Polish & keyboard shortcuts | ✅ Complete |

---

## Features

### GIS Layout
- **Single-screen split** — left sidebar controls, MapLibre center map, right detail panel, bottom status bar + histogram
- **Amber MOCK MODE banner** — indicates mock backend is active
- **RTL support** — English/Arabic toggle with full RTL layout flip

### Area Selection & Grid
- **Bbox draw tool** — press `D` to activate or click draw button
- **Nominatim search** — type city name to auto-fill Step 2 bbox (Cairo pre-configured)
- **Cell-count estimate** — amber warning at >300 cells, red block at >500
- **Grid size options** — 200m / 500m (default) / 1km toggle
- **Projection label** — EPSG:32636 (metric) displayed in sidebar

### Modality & Model Selection
- **Modality checkboxes** — POI (64-dim), Image (64-dim), Graph (32-dim), Text (64-dim), independently toggleable
- **Ablation presets** — POI only, POI+Image, POI+Image+Graph, all four
- **Model selector** — MLP (default) / GNN (spatial)
- **GNN auto-locks Graph** — selecting GNN enables Graph modality and shows topology layer
- **Fusion method** — concat / weighted / attention in classify request payload

### Classification
- **Classify button** — press `C` or click button to run
- **Loading overlay** — cycles: downloading_poi → mapping_poi_to_nodes → building_graph → classifying
- **Progressive colorization** — cells appear in batches with confidence-based opacity (0.35 + confidence × 0.60)
- **Cell colors** — Residential (#FFD966), Commercial (#E63946), Industrial (#9B5DE5)
- **Cancel** — press Esc to abort classification
- **Live histogram** — confidence distribution in bottom status bar

### Cell Detail Panel
- **Tab switching** — Detail / Evaluation tabs
- **Cell ID** — monospace font
- **Class + color swatch**
- **Confidence bars** — all three classes
- **Cell Story** — "Cell Story (POI semantic vector)" section with 384-dim subtitle, top-5 POI list, tooltip explains mean-pooling
- **Graph metrics** — degree_centrality, clustering_coeff, total_road_length_m, node_count, road_density
- **Satellite thumbnail**
- **Embedding norms** — graph L2, text L2
- **Pin to compare** — pin up to 3 cells for comparison

### Evaluation Tab
- **Distribution chart** — per-class bar chart
- **Average confidence** — percentage
- **Confidence histogram** — 10 buckets
- **Ground truth upload** — CSV/GeoJSON/JSON
- **Metrics** — Accuracy, Macro F1, Weighted F1, Spatial Accuracy
- **Per-class F1** — Residential, Commercial, Industrial
- **Confusion matrix** — 3×3 grid

### Layer Controls
- **Toggle switches** — Classification, POI heatmap, Roads, Graph topology, Satellite
- **URL persistence** — layer state in query string, restores on reload

### Keyboard Shortcuts

| Key | Action |
|---|---|
| `D` | Activate bbox draw tool |
| `C` | Run classification |
| `E` | Switch to Evaluation tab |
| `Esc` | Cancel classification / close panel |

---

## Getting Started

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Run tests
npm run test
```

Requires Node.js ≥ 18. No API keys needed — the app runs entirely on mock data and public tile sources (OSM, Esri World Imagery).

---

## Architecture

### Folder Structure

```
src/
├── components/           # UI components
│   ├── dashboard/       # Main dashboard components
│   │   ├── TopBar.tsx
│   │   ├── Sidebar.tsx
│   │   ├── MapView.tsx
│   │   ├── RightPanel.tsx
│   │   ├── CellDetailPanel.tsx
│   │   ├── EvaluationPanel.tsx
│   │   ├── LoadingOverlay.tsx
│   │   └── StatusBar.tsx
│   └── ui/             # shadcn/ui components
├── hooks/
│   ├── useKeyboardShortcuts.ts
│   └── useUrlLayers.ts
├── lib/
│   ├── api/
│   │   ├── mockClient.ts    # Mock API (swap to FastAPI here)
│   │   └── types.ts
│   ├── colors.ts
│   ├── i18n.ts          # EN/AR dictionary + RTL toggle
│   └── utils.ts
├── mocks/
│   ├── cairo-grid.json  # 144-cell dataset
│   └── cairo-graph.json # Graph topology
├── pages/               # Route components
│   ├── Index.tsx        # Main dashboard
│   ├── MllmBuilder.tsx
│   ├── DigitalTwin.tsx
│   ├── TrainingLab.tsx
│   ├── Ablation.tsx
│   └── StubPage.tsx
├── store/
│   └── dashboardStore.ts # Zustand UI state
└── index.css            # HSL design tokens
```

### State Management

- **Zustand** — UI state (modalities, grid size, layers, selected cell, pinned cells, bbox, loading state)
- **TanStack Query** — available for server state (not used in mock mode)
- **React Router** — navigation between dashboard and stub pages
- **URL query string** — layer toggle persistence

### Mock API Layer

`src/lib/api/mockClient.ts` contains:
- `classify()` — returns ClassifyJob with EventEmitter for progressive batches
- `getGraphTopology()` — returns nodes/edges from cairo-graph.json
- `evaluate()` — returns synthetic metrics (mock GT)
- `estimateCells()` — bbox + gridSize → cell count estimate
- `cairoBbox` / `allCells` — direct export of 144-cell dataset
- **Startup assertion** — validates all cell centroids within Step 2 bbox

The module is structured to swap to a real fetch-based FastAPI client without changing callers.

### i18n

`src/lib/i18n.ts` provides:
- `useI18n()` hook — returns `t(key)`, `lang`, `setLang`
- Dictionary object with EN/AR key-value pairs for all UI strings
- Language toggle sets `dir="rtl"` and `lang="ar"` on `<html>`

---

## Mock Data

**File:** `src/mocks/cairo-grid.json`  
**Cells:** 144 (12×12 grid)  
**Grid:** 500m default (EPSG:32636 metric projection, displayed as WGS84 on map)

**Study area bbox (Step 2 specification):**

```
north=30.10  south=29.90  east=31.30  west=31.10
```

A startup assertion verifies that every cell centroid falls within this bbox.

**Per-cell fields:**

| Field | Description |
|---|---|
| id | Unique cell identifier, e.g. `CAI-0042` |
| class | `Residential` / `Commercial` / `Industrial` |
| confidence | Dominant class confidence, range 0.51–0.97 |
| confidences | Per-class scores (sum = 1) |
| top5_poi | Top 5 POI names in cell |
| road_density | Roads per km² |
| node_count | OSMnx graph nodes in cell |
| degree_centrality | Mean node degree centrality |
| clustering_coeff | Mean clustering coefficient |
| total_road_length_m | Total road length in metres |
| graph_embedding_norm | L2 norm of 32-dim graph feature |
| text_embedding_norm | L2 norm of 64-dim text feature |
| satellite_thumb | Thumbnail URL |
| geometry | GeoJSON polygon |

**Class colours:**

| Class | Hex |
|---|---|
| Residential | #FFD966 |
| Commercial | #E63946 |
| Industrial | #9B5DE5 |

---

## Step 2 Academic Alignment

This dashboard is the UI layer for the Step 2 multi-modal urban classification pipeline.

| Pipeline concept | Where in UI |
|---|---|
| OSMnx road graph | Graph modality; topology layer; Graph metrics panel |
| Nearest-node POI mapping | `mapping_poi_to_nodes` loading step |
| Cell Story (384-dim) | Cell detail panel section |
| EPSG:32636 metric | Sidebar projection label |
| GraphML source | JSDoc comment on mockClient |
| Ablation strategy | Ablation preset dropdown |
| Fusion methods | fusion_method in classify payload |

---

## Roadmap

### v2 — Real Backend Integration

- Real ML classification via FastAPI endpoint
- WebSocket streaming for classify progress
- Full ablation comparison view (`/ablation`)
- MLLM training flow (`/mllm-builder`)
- Digital Twin natural-language query (`/digital-twin`)
- Training lab fine-tune flow (`/training-lab`)
- Data export (CSV, GeoJSON, PNG)
- Full 224-dim feature vector breakdown in cell detail

---

## Contributing

### Swapping Mock to Real Backend

1. Replace the function bodies in `src/lib/api/mockClient.ts` with `fetch()` calls to your FastAPI service.
2. No caller components need to change — they already use the same Promise/EventEmitter interface.
3. The MOCK MODE banner will automatically hide once real endpoints return non-mock data.

### Adding Translations

Add key-value pairs to both `en` and `ar` objects in `src/lib/i18n.ts`. Wrap any new UI string in `t("your_key")`.

### Data Updates

Replace `src/mocks/cairo-grid.json` with updated cell data. All centroids must remain within the Step 2 study area bbox or the startup assertion will throw.

---

## License

MIT