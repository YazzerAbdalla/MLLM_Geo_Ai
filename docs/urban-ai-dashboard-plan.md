## Urban AI Dashboard — Core MVP (v1)

Build the central classification workflow from PRD v3.0, wired to a mock API layer. Other PRD pages (MLLM Builder, Digital Twin, Training Lab, Ablation) ship as navigable stub pages so the IA is in place for v2.

### Scope (in)

**Main Dashboard (**`/`**)** — single-screen GIS-style layout:

- Left sidebar: Area selection, Grid size, Modality checkboxes, Model selector, Classify controls, Layer toggles
- Center: MapLibre GL map
- Right panel: Cell detail / Evaluation tabs (appears after classify)
- Top bar: Logo, language toggle (EN/AR + RTL), Mock Mode banner
- Bottom status bar: live class distribution histogram

**Area selection & loading** (FR-01–05)

- MapLibre GL with bbox draw tool (key `D`) and Nominatim geocoding search
- Cell-count estimate before submit; amber > 300, block red > 500
- Loading overlay with step labels (downloading_poi, …, building_graph)

**Grid & graph** (FR-06–08)

- Grid radio: 200 / 500 (default) / 1km
- Empty cell outlines render after load
- Graph topology toggle layer (nodes + edges)

**Modalities** (FR-09–12)

- 4 independent checkboxes: POI, Image, Graph, Text
- Ablation preset dropdown
- At least one required to enable Classify

**Model selector** (FR-13–16)

- MLP (default) / GNN
- Selecting GNN auto-enables and locks Graph modality + auto-shows graph topology layer

**Classify execution & results** (FR-17–25)

- Classify button → mock job with simulated WebSocket-style progressive batches
- Cells animate in, opacity = 0.35 + confidence × 0.60
- Colors: Residential `#FFD966`, Commercial `#E63946`, Industrial `#9B5DE5`
- Cancel button
- Cell click → detail panel: dominant class, 3 confidence bars, top-5 POI, satellite thumb, road density, node count
- Pin up to 3 cells for comparison
- Live distribution histogram in status bar

**Evaluation panel** (FR-26–31)

- Tab appears after classify
- Without GT: dominant-class distribution, avg confidence, confidence histogram
- Ground-truth CSV/GeoJSON upload → mock returns Accuracy, per-class F1, Macro/Weighted F1, Spatial Accuracy
- 3×3 color-coded confusion matrix

**Layer controls** (FR-32–33)

- Toggles: Classification, POI heatmap, Roads, Graph topology, Satellite basemap
- State synced to URL query string

**i18n** (Arabic + English, RTL)

- Language toggle flips `dir="rtl"` and `lang` on `<html>`
- All sidebar/panel strings translated; map labels English-only

**Mock Mode** (FR-64–66)

- Always-on for v1; amber "MOCK MODE" banner
- Cairo dataset, ~144 cells, realistic confidences (0.51–0.97)
- Mock API client structured so endpoints can later swap to a real FastAPI backend

**Keyboard shortcuts** (US-16): D draw, C classify, E evaluation tab, Esc cancel/close panel

**Stub pages** (nav links only, "Coming in v2" placeholder):

- `/mllm-builder`
- `/digital-twin`
- `/training-lab`
- `/ablation`

### Scope (out — deferred)

Real classification/ML, real WebSockets, real exports, MLLM training, Digital Twin NL query execution, ablation comparison runs, training lab fine-tune flow. UI shells stubbed.

### Design

- Dense GIS analyst tool: compact controls, monospace for IDs/metrics, neutral slate UI so the map dominates
- Class colors used only for data; UI uses a neutral palette with one accent
- All colors via design tokens in `index.css` + `tailwind.config.ts` (HSL)

### Technical notes

- **Map**: `maplibre-gl` + `@mapbox/mapbox-gl-draw` (works with MapLibre) for bbox; OSM raster tiles + Esri World Imagery for satellite layer (no token)
- **Mock API**: thin `src/lib/api/` module returning Promises with `setTimeout` + an `EventEmitter` for "ws" progress; same shape as PRD endpoints so MSW can be added later without changing callers
- **State**: TanStack Query for server state, Zustand for map/layer/selection UI state
- **Charts**: Recharts (histogram, confusion matrix coloring via SVG)
- **i18n**: lightweight in-house dictionary (`useI18n` hook), no extra dep
- **Routing**: React Router (already present); add the 4 stub routes
- **Geocoding**: direct fetch to Nominatim (`https://nominatim.openstreetmap.org/search`) with proper User-Agent header note
- Mock dataset stored as JSON in `src/mocks/cairo-grid.json`

### Acceptance (v1)

1. User draws bbox or searches "Cairo", picks 500m grid, sees cell estimate
2. Loading overlay cycles through 4 steps, then empty grid renders
3. User checks POI + Graph, picks GNN → Graph locks on, topology layer appears
4. Click Classify → cells progressively colorize with confidence-based opacity
5. Cell click opens detail panel with all required fields
6. Evaluation tab shows distribution; uploading mock GT CSV reveals metrics + confusion matrix
7. Language toggle switches whole UI to Arabic RTL
8. Layer toggles persist on reload via URL
9. Stub pages reachable from a nav menu