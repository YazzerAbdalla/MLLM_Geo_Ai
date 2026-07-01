import { useCallback, useEffect, useMemo } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Switch } from "@/components/ui/switch";
import { TopBar } from "@/components/dashboard/TopBar";
import { Sidebar } from "@/components/dashboard/Sidebar";
import { MapView } from "@/components/dashboard/MapView";
import { RightPanel } from "@/components/dashboard/RightPanel";
import { StatusBar } from "@/components/dashboard/StatusBar";
import { LoadingOverlay } from "@/components/dashboard/LoadingOverlay";
import { AiQueryPanel } from "@/components/dashboard/AiQueryPanel";
import { useDash } from "@/store/dashboardStore";
import { cairoBbox, estimateCells } from "@/lib/api/mockClient";
import { useLoadArea } from "@/hooks/api/useLoadArea";
import { useClassify } from "@/hooks/api/useClassify";
import { useCancelJob } from "@/hooks/api/useCancelJob";
import { useJobProgress } from "@/hooks/api/useJobProgress";
import { useClassificationResult } from "@/hooks/api/useClassificationResult";
import { useClassification } from "@/hooks/api/useClassification";
import { isSuccess, isTerminal, type LoadingStep } from "@/api/types";
import { featureToCell } from "@/lib/adapters";
import { useUrlLayers } from "@/hooks/useUrlLayers";
import { useKeyboardShortcuts } from "@/hooks/useKeyboardShortcuts";
import type { Modality } from "@/lib/api/types";
import { toast } from "@/hooks/use-toast";
import { useI18n } from "@/lib/i18n";
import { getBboxFromGeometry, createSmallDefaultArea } from "@/lib/geoUtils";

const Index = () => {
  useUrlLayers();

  const { jobId: routeJobId } = useParams();
  const navigate = useNavigate();
  const reviewMode = !!routeJobId;

  const {
    setLoaded, setLoadingStep, setClassifying, setClassifyProgress,
    resetCells, setCells, modelType, fusion, setActiveTab,
    bbox, loadJobId, setLoadJobId, classifyJobId, setClassifyJobId,
    setGridId, gridSize, setGridSize, drawnGeometry, setDrawnGeometry,
    searchLocation,
  } = useDash();

  const storeCells = useDash((s) => s.cells);
  const storeGridId = useDash((s) => s.gridId);
  const storeClassifyJobId = useDash((s) => s.classifyJobId);

  const loadAreaM = useLoadArea();
  const classifyM = useClassify();
  const cancelM = useCancelJob();
  const loadProgress = useJobProgress(loadJobId);
  const classifyProgress = useJobProgress(classifyJobId);
  const resultQ = useClassificationResult(
    reviewMode ? null : classifyJobId,
    !reviewMode && isSuccess(classifyProgress.status)
  );
  const reviewQ = useClassification(reviewMode ? routeJobId : null);

  // Resolve jobId / gridId / cells for MapView: prefer route params / API data, fall back to store
  const activeJobId = routeJobId || storeClassifyJobId;
  const activeGridId = reviewQ.data?.gridId ?? storeGridId;
  const activeCells = reviewMode ? (reviewQ.data?.cells ?? storeCells) : storeCells;

  /**
   * Triggers loading of urban data for the selected area of interest (AOI).
   * Implements validation and automatic grid size fallback.
   */
  const handleLoadArea = useCallback(() => {
    if (reviewMode) return;
    if (useDash.getState().loaded || loadAreaM.isPending) return;

    let areaToAnalyze = null;
    let isDefaultArea = false;

    // Area source selection logic:
    // 1. drawnGeometry takes absolute priority
    // 2. Fall back to creating a small default area centered on the searchLocation
    if (drawnGeometry) {
      areaToAnalyze = drawnGeometry;
    } else if (searchLocation) {
      areaToAnalyze = createSmallDefaultArea(searchLocation.lng, searchLocation.lat);
      isDefaultArea = true;
    }

    // Show error if no area or location is selected/drawn
    if (!areaToAnalyze) {
      toast({
        title: "Area Selection Required",
        description: "Please draw an area on the map or select a search location.",
        variant: "destructive",
      });
      return;
    }

    const b = getBboxFromGeometry(areaToAnalyze);
    if (!b) return;

    let currentGridSize = gridSize;
    let cellEstimate = estimateCells(b, currentGridSize);

    // Validate estimated cells before sending request
    if (cellEstimate > 500) {
      // Try to find a larger grid size that is under the 500-cell limit
      const sizes: (200 | 500 | 1000)[] = [200, 500, 1000];
      const nextSize = sizes.find((s) => s > currentGridSize && estimateCells(b, s) <= 500);
      if (nextSize) {
        currentGridSize = nextSize;
        setGridSize(nextSize);
        toast({
          title: "Grid Size Adjusted",
          description: `Grid size automatically increased to ${nextSize}m to stay within backend cell limits.`,
        });
        cellEstimate = estimateCells(b, nextSize);
      } else {
        toast({
          title: "Area Too Large",
          description: `Estimated ${cellEstimate} cells exceed the 500-cell backend limit. Please zoom in or draw a smaller area.`,
          variant: "destructive",
        });
        return;
      }
    }

    setLoadingStep("downloading_poi");
    loadAreaM.mutate(
      {
        bbox: [b.west, b.south, b.east, b.north],
        place_name: searchLocation?.label || "Custom Drawn Area",
      },
      {
        onSuccess: ({ job_id }) => {
          setLoadJobId(job_id);
          // Save the default area as drawn geometry so it renders on map after load completes
          if (isDefaultArea) {
            setDrawnGeometry(areaToAnalyze);
          }
        },
        onError: () => setLoadingStep(null),
      }
    );
  }, [
    reviewMode,
    drawnGeometry,
    searchLocation,
    gridSize,
    setGridSize,
    setDrawnGeometry,
    loadAreaM,
    setLoadJobId,
    setLoadingStep,
  ]);

  const handleClassify = useCallback(() => {
    if (reviewMode) return;
    const state = useDash.getState();
    if (!state.loaded || state.classifying || !state.gridId) return;
    const mods = (Object.keys(state.modalities) as Modality[]).filter((k) => state.modalities[k]);
    if (mods.length === 0) return;
    resetCells();
    setClassifying(true);
    setLoadingStep("classifying");
    classifyM.mutate(
      {
        grid_id: state.gridId,
        cell_size: state.gridSize,
        modalities: mods,
        model_type: modelType,
        fusion_method: fusion,
        area_geometry: state.drawnGeometry,
      },
      {
        onSuccess: ({ job_id }) => setClassifyJobId(job_id),
        onError: () => { setClassifying(false); setLoadingStep(null); },
      }
    );
  }, [reviewMode, classifyM, fusion, modelType, resetCells, setClassifying, setClassifyJobId, setLoadingStep]);

  const handleCancel = useCallback(() => {
    if (reviewMode) return;
    const jid = classifyJobId || loadJobId;
    if (!jid) return;
    cancelM.mutate(jid, {
      onSuccess: () => {
        setClassifying(false);
        setLoadingStep(null);
        if (classifyJobId) setClassifyJobId(null);
        else setLoadJobId(null);
      },
    });
  }, [reviewMode, cancelM, classifyJobId, loadJobId, setClassifying, setClassifyJobId, setLoadJobId, setLoadingStep]);

  // React to load-area job progress
  useEffect(() => {
    if (!loadJobId) return;
    if (loadProgress.step) setLoadingStep(loadProgress.step as LoadingStep);
    if (isSuccess(loadProgress.status)) {
      setLoaded(true);
      // Retrieve grid_id from job status progress response, fallback to loadJobId if not present
      setGridId(loadProgress.gridId || loadJobId);
      setLoadingStep(null);
    } else if (isTerminal(loadProgress.status)) {
      setLoadingStep(null);
    }
  }, [loadJobId, loadProgress.status, loadProgress.step, loadProgress.gridId, setGridId, setLoaded, setLoadingStep]);

  // React to classify job progress
  useEffect(() => {
    if (!classifyJobId) return;
    if (typeof classifyProgress.progress === "number") setClassifyProgress(classifyProgress.progress);
    if (classifyProgress.step) setLoadingStep(classifyProgress.step as LoadingStep);
    if (isSuccess(classifyProgress.status)) {
      setLoadingStep(null);
    } else if (isTerminal(classifyProgress.status)) {
      setClassifying(false);
      setLoadingStep(null);
    }
  }, [classifyJobId, classifyProgress.status, classifyProgress.step, classifyProgress.progress, setClassifying, setClassifyProgress, setLoadingStep]);

  // Populate cells when classification result arrives (workspace mode)
  useEffect(() => {
    if (!resultQ.data || reviewMode) return;
    if (import.meta.env.DEV) {
      console.log("[Index] classification result received — feature count:", resultQ.data.features?.length);
      resultQ.data.features?.forEach((f: Record<string, unknown>) => {
        console.log("  feature dominant_class:", f.dominant_class, "cell_id:", f.cell_id, "properties:", f.properties);
      });
    }
    const mapped = resultQ.data.features.map(featureToCell);
    if (import.meta.env.DEV) {
      console.log("[Index] mapped cells:", mapped.length);
      mapped.forEach((c) => console.log("  cell id:", c.id, "class:", c.class, "confidence:", c.confidence));
    }
    setCells(mapped);
    setClassifying(false);
    // Navigate to route-driven view after classification completes
    const state = useDash.getState();
    if (state.classifyJobId) {
      navigate(`/classification/${state.classifyJobId}`, { replace: true });
    }
  }, [resultQ.data, reviewMode, setCells, setClassifying, navigate]);

  // Populate cells in review mode when fetched via useClassification
  useEffect(() => {
    if (!reviewQ.data || !reviewMode) return;
    setCells(reviewQ.data.cells);
    setLoaded(true);
    setClassifying(false);
    setLoadingStep(null);
    setClassifyJobId(routeJobId ?? null);
    setGridId(reviewQ.data.gridId ?? null);
  }, [reviewQ.data, reviewMode, routeJobId, setCells, setLoaded, setClassifying, setLoadingStep, setClassifyJobId, setGridId]);

  useKeyboardShortcuts({
    onDraw: handleLoadArea,
    onClassify: handleClassify,
    onEvaluation: () => setActiveTab("evaluation"),
    onCancel: handleCancel,
  });

  return (
    <div className="h-screen flex flex-col bg-background text-foreground">
      <TopBar />
      <div className="flex-1 flex overflow-hidden">
        {reviewMode ? (
          <ReviewSidebar />
        ) : (
          <Sidebar onLoadArea={handleLoadArea} onClassify={handleClassify} onCancel={handleCancel} />
        )}
        <main className="flex-1 relative">
          <MapView jobId={activeJobId} gridId={activeGridId} cells={activeCells} />
          <LoadingOverlay />
          <MapLegend />
        </main>
        <RightPanel />
      </div>
      <StatusBar />
    </div>
  );
}

function ReviewSidebar() {
  const { t } = useI18n();
  const layers = useDash((s) => s.layers);
  const setLayer = useDash((s) => s.setLayer);
  const poiHeatmapEmpty = useDash((s) => s.poiHeatmapEmpty);
  return (
    <aside className="w-[320px] shrink-0 border-r border-border bg-card overflow-y-auto">
      <div className="p-4 space-y-5">
        <section className="space-y-2">
          <h3 className="text-[11px] uppercase tracking-wider text-muted-foreground font-semibold">{t("layers")}</h3>
          <LayerRow label={t("layer_classification")} value={layers.classification} onChange={(v) => setLayer("classification", v)} />
          <LayerRow label={t("layer_poi")} value={layers.poi} onChange={(v) => setLayer("poi", v)} />
          {poiHeatmapEmpty && (
            <p className="text-[11px] text-muted-foreground pl-6">No POIs available for the selected area.</p>
          )}
          <LayerRow label={t("layer_roads")} value={layers.roads} onChange={(v) => setLayer("roads", v)} />
          <LayerRow label={t("layer_graph")} value={layers.graph} onChange={(v) => setLayer("graph", v)} />
          <LayerRow label={t("layer_satellite")} value={layers.satellite} onChange={(v) => setLayer("satellite", v)} />
        </section>
        <AiQueryPanel />
      </div>
    </aside>
  );
};

function LayerRow({ label, value, onChange }: { label: string; value: boolean; onChange: (v: boolean) => void }) {
  return (<div className="flex items-center justify-between text-sm py-0.5"><span>{label}</span><Switch checked={value} onCheckedChange={onChange} /></div>);
}

function MapLegend() {
  return (
    <div className="absolute bottom-3 left-3 z-10 bg-card/95 backdrop-blur border border-border rounded-md px-3 py-2 text-xs space-y-1 shadow-lg">
      <div className="font-semibold text-[10px] uppercase tracking-wider text-muted-foreground mb-1">Land use</div>
      {[
        ["Residential", "#FFD966"],
        ["Commercial", "#E63946"],
        ["Industrial", "#9B5DE5"],
      ].map(([l, c]) => (
        <div key={l} className="flex items-center gap-2">
          <span className="h-3 w-3 rounded-sm" style={{ backgroundColor: c }} />
          <span>{l}</span>
        </div>
      ))}
    </div>
  );
}

export default Index;
