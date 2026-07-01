import { create } from "zustand";
import type { CellDatum, FusionMethod, LoadingStep, Modality, ModelType } from "@/lib/api/types";
import type { JobStatus, QueryResponse } from "@/api/types";

export type LayerKey = "classification" | "poi" | "roads" | "graph" | "satellite";

export type DrawnGeometry = {
  type: "Polygon";
  coordinates: number[][][];
} | null;

interface DashState {
  bbox: { north: number; south: number; east: number; west: number } | null;
  setBbox: (b: DashState["bbox"]) => void;
  gridSize: 200 | 500 | 1000;
  setGridSize: (n: DashState["gridSize"]) => void;

  /** Custom user-drawn geometry (rectangle/polygon). Filters classification grid when set. */
  drawnGeometry: DrawnGeometry;
  setDrawnGeometry: (g: DrawnGeometry) => void;
  /** Whether the map is currently in draw-area mode. */
  drawMode: boolean;
  setDrawMode: (v: boolean) => void;

  modalities: Record<Modality, boolean>;
  toggleModality: (m: Modality) => void;
  setModality: (m: Modality, v: boolean) => void;
  modelType: ModelType;
  setModelType: (m: ModelType) => void;
  fusion: FusionMethod;
  setFusion: (f: FusionMethod) => void;

  loaded: boolean;
  setLoaded: (v: boolean) => void;
  loadingStep: LoadingStep | null;
  setLoadingStep: (s: LoadingStep | null) => void;
  classifying: boolean;
  setClassifying: (v: boolean) => void;
  classifyProgress: number;
  setClassifyProgress: (n: number) => void;
  cells: CellDatum[];
  appendCells: (c: CellDatum[]) => void;
  resetCells: () => void;

  /** Active backend job ids (load + classify) */
  loadJobId: string | null;
  setLoadJobId: (id: string | null) => void;
  classifyJobId: string | null;
  setClassifyJobId: (id: string | null) => void;
  /** Set after /load-area completes — used as grid_id for downstream calls */
  gridId: string | null;
  setGridId: (id: string | null) => void;
  jobStatus: JobStatus | null;
  setJobStatus: (s: JobStatus | null) => void;
  /** Replace all cells at once (used when classification-result arrives) */
  setCells: (c: CellDatum[]) => void;

  selectedCellId: string | null;
  setSelectedCellId: (id: string | null) => void;
  pinned: string[];
  togglePin: (id: string) => void;

  layers: Record<LayerKey, boolean>;
  setLayer: (k: LayerKey, v: boolean) => void;

  activeTab: "detail" | "evaluation";
  setActiveTab: (t: DashState["activeTab"]) => void;

  /** Selected search location for centering/zooming and default area generation. */
  searchLocation: { lat: number; lng: number; label: string } | null;
  /** Sets the selected search location. */
  setSearchLocation: (loc: { lat: number; lng: number; label: string } | null) => void;

  poiHeatmapEmpty: boolean;
  setPoiHeatmapEmpty: (v: boolean) => void;

  queryResults: QueryResponse | null;
  setQueryResults: (r: QueryResponse | null) => void;
  queryHistory: string[];
  addQueryHistory: (q: string) => void;
  isQuerying: boolean;
  setIsQuerying: (v: boolean) => void;
  queryError: string | null;
  setQueryError: (e: string | null) => void;
  matchedCellIds: string[];
  setMatchedCellIds: (ids: string[]) => void;
  aiQueryOpen: boolean;
  setAiQueryOpen: (v: boolean) => void;
}

const STEP2_BBOX = { north: 30.10, south: 29.90, east: 31.30, west: 31.10 };

export const useDash = create<DashState>((set) => ({
  bbox: STEP2_BBOX,
  setBbox: (bbox) => set({ bbox }),
  gridSize: 500,
  setGridSize: (gridSize) => set({ gridSize }),

  drawnGeometry: null,
  setDrawnGeometry: (drawnGeometry) => set({ drawnGeometry }),
  drawMode: false,
  setDrawMode: (drawMode) => set({ drawMode }),

  modalities: { poi: true, image: true, graph: false, text: false },
  toggleModality: (m) =>
    set((s) => ({ modalities: { ...s.modalities, [m]: !s.modalities[m] } })),
  setModality: (m, v) =>
    set((s) => ({ modalities: { ...s.modalities, [m]: v } })),
  modelType: "mlp",
  setModelType: (modelType) =>
    set((s) =>
      modelType === "gnn"
        ? { modelType, modalities: { ...s.modalities, graph: true }, layers: { ...s.layers, graph: true } }
        : { modelType }
    ),
  fusion: "concat",
  setFusion: (fusion) => set({ fusion }),

  loaded: false,
  setLoaded: (loaded) => set({ loaded }),
  loadingStep: null,
  setLoadingStep: (loadingStep) => set({ loadingStep }),
  classifying: false,
  setClassifying: (classifying) => set({ classifying }),
  classifyProgress: 0,
  setClassifyProgress: (classifyProgress) => set({ classifyProgress }),
  cells: [],
  appendCells: (c) => set((s) => ({ cells: [...s.cells, ...c] })),
  resetCells: () => set({ cells: [], classifyProgress: 0 }),
  setCells: (cells) => set({ cells }),

  loadJobId: null,
  setLoadJobId: (loadJobId) => set({ loadJobId }),
  classifyJobId: null,
  setClassifyJobId: (classifyJobId) => set({ classifyJobId }),
  gridId: null,
  setGridId: (gridId) => set({ gridId }),
  jobStatus: null,
  setJobStatus: (jobStatus) => set({ jobStatus }),

  selectedCellId: null,
  setSelectedCellId: (selectedCellId) => set({ selectedCellId }),
  pinned: [],
  togglePin: (id) =>
    set((s) => {
      if (s.pinned.includes(id)) return { pinned: s.pinned.filter((x) => x !== id) };
      if (s.pinned.length >= 3) return s;
      return { pinned: [...s.pinned, id] };
    }),

  layers: {
    classification: true,
    poi: false,
    roads: false,
    graph: false,
    satellite: false,
  },
  setLayer: (k, v) => set((s) => ({ layers: { ...s.layers, [k]: v } })),

  activeTab: "detail",
  setActiveTab: (activeTab) => set({ activeTab }),

  searchLocation: null,
  setSearchLocation: (searchLocation) => set({ searchLocation }),

  poiHeatmapEmpty: false,
  setPoiHeatmapEmpty: (poiHeatmapEmpty) => set({ poiHeatmapEmpty }),

  queryResults: null,
  setQueryResults: (queryResults) => set({ queryResults }),
  queryHistory: [],
  addQueryHistory: (q) =>
    set((s) => {
      const filtered = s.queryHistory.filter((h) => h !== q);
      return { queryHistory: [q, ...filtered].slice(0, 5) };
    }),
  isQuerying: false,
  setIsQuerying: (isQuerying) => set({ isQuerying }),
  queryError: null,
  setQueryError: (queryError) => set({ queryError }),
  matchedCellIds: [],
  setMatchedCellIds: (matchedCellIds) => set({ matchedCellIds }),
  aiQueryOpen: false,
  setAiQueryOpen: (aiQueryOpen) => set({ aiQueryOpen }),
}));
