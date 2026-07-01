import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { ArrowLeft, Upload, RotateCcw, Download, Loader2, FileDown } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

import { useI18n } from "@/lib/i18n";
import { cairoBbox } from "@/lib/api/mockClient";
import {
  usePoiPreviewUpload,
  usePoiImportConfirm,
} from "@/hooks/api/usePoiDataManager";

import { WizardHeader } from "@/components/poi-manager/WizardHeader";
import { ImportSuccessScreen } from "@/components/poi-manager/ImportSuccessScreen";
import { EmptyState } from "@/components/poi-manager/EmptyState";
import { ValidationDashboard } from "@/components/poi-manager/ValidationDashboard";
import { SummaryBar } from "@/components/poi-manager/SummaryBar";
import { PreviewSidebar } from "@/components/poi-manager/PreviewSidebar";
import { ImportConfirmationDialog } from "@/components/poi-manager/ImportConfirmationDialog";
import { ImportSuccessDialog } from "@/components/poi-manager/ImportSuccessDialog";

import type { PoiPreviewFeatureProperties } from "@/api/poiDataManagerTypes";

const OSM_STYLE: maplibregl.StyleSpecification = {
  version: 8,
  glyphs: "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",
  sources: {
    osm: {
      type: "raster",
      tiles: ["https://a.tile.openstreetmap.org/{z}/{x}/{y}.png"],
      tileSize: 256,
      attribution: "© OpenStreetMap contributors",
      maxzoom: 19,
    },
  },
  layers: [{ id: "osm-bg", type: "raster", source: "osm" }],
};

function escapeHtml(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function poiPopupHtml(
  props: PoiPreviewFeatureProperties,
  coords: [number, number]
): string {
  const statusColors: Record<string, string> = {
    new: "#3B82F6",
    warning: "#F97316",
    duplicate_poi: "#EAB308",
    duplicate_coord: "#E11D48",
    invalid: "#9CA3AF",
  };
  const color = statusColors[props.status] || "#9CA3AF";
  const statusLabel = props.status.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  return `
    <div style="font-size:12px;line-height:1.6;color:#000;max-width:280px">
      <div style="display:flex;align-items:center;gap:6px;margin-bottom:6px">
        <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${color}"></span>
        <span style="font-weight:700;font-size:14px">${escapeHtml(props.name)}</span>
      </div>
      <table style="width:100%;border-collapse:collapse">
        <tr><td style="opacity:.6;padding-right:8px;padding-bottom:2px;white-space:nowrap">Category</td><td style="font-family:monospace;padding-bottom:2px">${props.category}</td></tr>
        <tr><td style="opacity:.6;padding-right:8px;padding-bottom:2px;white-space:nowrap">Place Type</td><td style="font-family:monospace;padding-bottom:2px">${props.place_type || "—"}</td></tr>
        <tr><td style="opacity:.6;padding-right:8px;padding-bottom:2px;white-space:nowrap">Address</td><td style="padding-bottom:2px">${props.label || "—"}</td></tr>
        <tr><td style="opacity:.6;padding-right:8px;padding-bottom:2px;white-space:nowrap">Status</td><td style="font-family:monospace;padding-bottom:2px">${statusLabel}</td></tr>
        <tr><td style="opacity:.6;padding-right:8px;white-space:nowrap">Coords</td><td style="font-family:monospace">${coords[1].toFixed(5)}, ${coords[0].toFixed(5)}</td></tr>
      </table>
    </div>
  `;
}

export default function PoiDataManager() {
  const { t } = useI18n();
  const navigate = useNavigate();

  // Wizard state
  const [currentStep, setCurrentStep] = useState<1 | 2 | 3 | 4 | 5>(1);

  // Upload state
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [dragging, setDragging] = useState(false);

  // Preview state
  const [previewId, setPreviewId] = useState<string | null>(null);
  const [validation, setValidation] = useState<PoiValidationResult | null>(null);
  const [statistics, setStatistics] = useState<PoiPreviewStatistics | null>(null);
  const [features, setFeatures] = useState<GeoJSON.FeatureCollection | null>(null);
  const [categoryCounts, setCategoryCounts] = useState<Record<string, number>>({});

  // Sidebar state
  const [selectedPoiId, setSelectedPoiId] = useState<string | null>(null);
  const [deletedPoiIds, setDeletedPoiIds] = useState<Set<string>>(new Set());

  // Import state
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<PoiImportResponse | null>(null);
  const [processingTimeMs, setProcessingTimeMs] = useState(0);
  const [successDialogOpen, setSuccessDialogOpen] = useState(false);

  // Unsaved changes
  const [unsavedChanges, setUnsavedChanges] = useState(false);
  const [pendingReset, setPendingReset] = useState(false);
  const [pendingNav, setPendingNav] = useState(false);

  // Map refs
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const popupRef = useRef<maplibregl.Popup | null>(null);
  const [mapReady, setMapReady] = useState(false);
  const previewLayersRef = useRef(false);

  // Mutations
  const previewUpload = usePoiPreviewUpload();
  const importConfirm = usePoiImportConfirm();

  // Derived
  const previewFeatures = useMemo(() => {
    if (!features) return [];
    return features.features as GeoJSON.Feature<
      GeoJSON.Point,
      PoiPreviewFeatureProperties
    >[];
  }, [features]);

  const allCategories = useMemo(
    () => Object.keys(categoryCounts),
    [categoryCounts]
  );

  const filteredFeatures = useMemo(() => {
    if (!features) return null;
    return {
      ...features,
      features: features.features.filter((f) => {
        const p = f.properties as PoiPreviewFeatureProperties;
        const coords = (f.geometry as GeoJSON.Point).coordinates;
        const id = p.osm_id || `${coords[0]}_${coords[1]}`;
        return !deletedPoiIds.has(id);
      }),
    };
  }, [features, deletedPoiIds]);

  const canImport =
    validation !== null &&
    validation.valid === true &&
    validation.errors.length === 0;

  // ---- Handlers ----

  const handleDownloadTemplate = useCallback(() => {
    const csv = "name,category,lat,lng,place_type,label\n";
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "poi_template.csv";
    a.click();
    URL.revokeObjectURL(url);
    toast.success("Template downloaded");
  }, []);

  const handleUpload = useCallback(
    (file: File) => {
      setUploadedFile(file);
      setCurrentStep(2);
      setUploadProgress(0);
      setSelectedPoiId(null);

      const interval = setInterval(() => {
        setUploadProgress((prev) => {
          const next = prev + Math.random() * 15;
          return next >= 95 ? 95 : next;
        });
      }, 200);

      previewUpload.mutate(file, {
        onSuccess: (data) => {
          clearInterval(interval);
          setUploadProgress(100);
          setPreviewId(data.session_id ?? null);
          setValidation(data.validation);
          if (data.statistics) setStatistics(data.statistics);
          if (data.features) setFeatures(data.features);
          if (data.category_counts) setCategoryCounts(data.category_counts);
          console.log("[POI Manager] Upload success — full response:", JSON.stringify(data, null, 2).slice(0, 2000));
          console.log("[POI Manager] Upload keys:", Object.keys(data), "features?", data.features ? `FC with ${data.features.features.length} features` : "MISSING");
          console.log("[POI Manager] session_id:", data.session_id);
          setUnsavedChanges(true);
          setTimeout(() => setCurrentStep(3), 400);
        },
        onError: (err) => {
          clearInterval(interval);
          setUploadProgress(0);
          setCurrentStep(1);
          toast.error(t("poi_manager_upload_error"), {
            description: err.message,
          });
        },
      });
    },
    [previewUpload, t]
  );

  const performReset = useCallback(() => {
    setCurrentStep(1);
    setUploadedFile(null);
    setUploadProgress(0);
    setPreviewId(null);
    setValidation(null);
    setStatistics(null);
    setFeatures(null);
    setCategoryCounts({});
    setSelectedPoiId(null);
    setUnsavedChanges(false);
    setImportResult(null);
    setSuccessDialogOpen(false);

    if (popupRef.current) {
      popupRef.current.remove();
      popupRef.current = null;
    }
  }, []);

  const handleReset = useCallback(() => {
    if (unsavedChanges) {
      setPendingReset(true);
      return;
    }
    performReset();
  }, [unsavedChanges, performReset]);

  const handleConfirmReset = useCallback(() => {
    setPendingReset(false);
    performReset();
  }, [performReset]);


  const handleImport = useCallback(() => {
    if (!canImport) return;
    console.log("[POI Manager] Opening import dialog, previewId=%s", previewId);
    setConfirmDialogOpen(true);
  }, [canImport, previewId]);

  const handleConfirmImport = useCallback(() => {
    if (!previewId) {
      toast.error("Missing session ID — cannot import");
      return;
    }
    setConfirmDialogOpen(false);
    setCurrentStep(5);
    setImporting(true);
    const startTime = performance.now();

    importConfirm.mutate(previewId, {
      onSuccess: (data) => {
        setImporting(false);
        setProcessingTimeMs(performance.now() - startTime);
        setImportResult(data);
        setCurrentStep(6);
        setUnsavedChanges(false);
        toast.success(
          `${data.imported} POIs imported successfully`
        );
      },
      onError: (err) => {
        setImporting(false);
        setCurrentStep(4);
        toast.error(t("poi_manager_import_error"), {
          description: err.message,
        });
      },
    });
  }, [previewId, importConfirm, t]);

  const handleImportAnother = useCallback(() => {
    setSuccessDialogOpen(false);
    performReset();
  }, [performReset]);

  // ---- POI Selection ----

  const handlePoiSelect = useCallback(
    (f: GeoJSON.Feature<GeoJSON.Point, PoiPreviewFeatureProperties>) => {
      const coords = (f.geometry as GeoJSON.Point).coordinates as [number, number];
      const id = f.properties.osm_id || `${coords[0]}_${coords[1]}`;
      setSelectedPoiId(id);

      const map = mapRef.current;
      if (!map) return;
      map.flyTo({ center: coords, zoom: 16, essential: true });

      if (popupRef.current) popupRef.current.remove();
      const popup = new maplibregl.Popup({
        offset: 14,
        closeButton: true,
        maxWidth: "300px",
      })
        .setLngLat(coords)
        .setHTML(poiPopupHtml(f.properties, coords))
        .addTo(map);
      popupRef.current = popup;
    },
    []
  );

  const handleDeletePoi = useCallback(
    (f: GeoJSON.Feature<GeoJSON.Point, PoiPreviewFeatureProperties>) => {
      const coords = (f.geometry as GeoJSON.Point).coordinates as [number, number];
      const id = f.properties.osm_id || `${coords[0]}_${coords[1]}`;
      setDeletedPoiIds((prev) => {
        const next = new Set(prev);
        next.add(id);
        return next;
      });
      if (selectedPoiId === id) setSelectedPoiId(null);
    },
    [selectedPoiId]
  );

  // ---- Map Init (OSM only, no preview layers) — creates map when entering Preview step

  useEffect(() => {
    if (currentStep !== 4 || mapRef.current || !containerRef.current) return;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: OSM_STYLE,
      center: [
        (cairoBbox.east + cairoBbox.west) / 2,
        (cairoBbox.north + cairoBbox.south) / 2,
      ],
      zoom: 10.4,
      attributionControl: { compact: true },
    });
    map.addControl(
      new maplibregl.NavigationControl({ showCompass: false }),
      "top-right"
    );
    mapRef.current = map;

    map.on("load", () => {
      map.resize();
      setMapReady(true);
    });
  }, [currentStep]);

  // Clean up map on unmount
  useEffect(() => {
    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
        setMapReady(false);
        previewLayersRef.current = false;
      }
    };
  }, []);

  // ResizeObserver
  useEffect(() => {
    const map = mapRef.current;
    const el = containerRef.current;
    if (!map || !el) return;
    const ro = new ResizeObserver(() => {
      if (map.loaded()) map.resize();
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, [mapReady]);

  // Preview layers lifecycle — created ONLY when features arrive
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady) return;

    if (filteredFeatures && statistics) {
      console.log("[POI Manager] Setting up preview layers:", {
        featureCount: filteredFeatures.features.length,
        bbox: statistics.bbox,
      });

      if (!previewLayersRef.current) {
        map.addSource("preview-source", {
          type: "geojson",
          data: { type: "FeatureCollection", features: [] },
          cluster: true,
          clusterMaxZoom: 14,
          clusterRadius: 50,
        });

        map.addLayer({
          id: "preview-cluster-circle",
          type: "circle",
          source: "preview-source",
          filter: ["has", "point_count"],
          paint: {
            "circle-color": ["step", ["get", "point_count"], "#51bbd6", 100, "#f1f075", 750, "#f28cb1"],
            "circle-radius": ["step", ["get", "point_count"], 20, 100, 30, 750, 40],
            "circle-opacity": 0.6,
            "circle-stroke-color": "#ffffff",
            "circle-stroke-width": 2,
          },
        });

        map.addLayer({
          id: "preview-cluster-count",
          type: "symbol",
          source: "preview-source",
          filter: ["has", "point_count"],
          layout: {
            "text-field": ["get", "point_count_abbreviated"],
            "text-font": ["DIN Offc Pro Medium", "Arial Unicode MS Bold"],
            "text-size": 12,
          },
          paint: { "text-color": "#ffffff" },
        });

        map.addLayer({
          id: "preview-heatmap",
          type: "heatmap",
          source: "preview-source",
          filter: ["!", ["has", "point_count"]],
          paint: {
            "heatmap-weight": ["case", ["has", "weight"], ["interpolate", ["linear"], ["get", "weight"], 0, 0, 1, 1], 1],
            "heatmap-radius": ["interpolate", ["linear"], ["zoom"], 8, 40, 18, 5],
            "heatmap-intensity": ["interpolate", ["linear"], ["zoom"], 8, 1, 18, 0.5],
            "heatmap-color": [
              "interpolate", ["linear"], ["heatmap-density"],
              0, "rgba(255,255,178,0)",
              0.25, "rgb(254,204,92)",
              0.5, "rgb(253,141,60)",
              0.75, "rgb(240,59,32)",
              1, "rgb(153,0,0)",
            ],
            "heatmap-opacity": 0.85,
          },
        });

        map.addLayer({
          id: "preview-circle",
          type: "circle",
          source: "preview-source",
          filter: ["!", ["has", "point_count"]],
          paint: {
            "circle-radius": ["interpolate", ["linear"], ["zoom"], 0, 0, 12, 0, 12.01, 9, 22, 9],
            "circle-color": [
              "match", ["get", "status"],
              "new", "#3B82F6",
              "warning", "#F97316",
              "duplicate_poi", "#EAB308",
              "duplicate_coord", "#E11D48",
              "#9CA3AF",
            ],
            "circle-stroke-color": "#ffffff",
            "circle-stroke-width": 1.5,
            "circle-opacity": 0.9,
          },
        });

        map.addLayer({
          id: "preview-selected-highlight",
          type: "circle",
          source: "preview-source",
          filter: ["!", ["has", "point_count"]],
          layout: { visibility: "none" },
          paint: {
            "circle-radius": 14,
            "circle-color": "#FCD34D",
            "circle-opacity": 0.7,
            "circle-stroke-color": "#ffffff",
            "circle-stroke-width": 3,
          },
        });

        // Event handlers
        map.on("click", "preview-cluster-circle", (e) => {
          const feature = e.features?.[0];
          if (!feature) return;
          const clusterId = feature.properties.cluster_id;
          const source = map.getSource("preview-source") as maplibregl.GeoJSONSource;
          source.getClusterExpansionZoom(clusterId, (err, zoom) => {
            if (err || zoom === undefined) return;
            map.easeTo({
              center: (feature.geometry as GeoJSON.Point).coordinates as [number, number],
              zoom: zoom + 1,
            });
          });
        });

        map.on("click", "preview-circle", (e) => {
          const f = e.features?.[0];
          if (!f) return;
          const props = f.properties as unknown as PoiPreviewFeatureProperties;
          const coords = (f.geometry as GeoJSON.Point).coordinates as [number, number];
          const id = props.osm_id || `${coords[0]}_${coords[1]}`;
          setSelectedPoiId(id);
          if (popupRef.current) popupRef.current.remove();
          const popup = new maplibregl.Popup({ offset: 14, closeButton: true, maxWidth: "300px" })
            .setLngLat(coords)
            .setHTML(poiPopupHtml(props, coords))
            .addTo(map);
          popupRef.current = popup;
        });

        map.on("mouseenter", "preview-circle", () => { map.getCanvas().style.cursor = "pointer"; });
        map.on("mouseleave", "preview-circle", () => { map.getCanvas().style.cursor = ""; });
        map.on("mouseenter", "preview-cluster-circle", () => { map.getCanvas().style.cursor = "pointer"; });
        map.on("mouseleave", "preview-cluster-circle", () => { map.getCanvas().style.cursor = ""; });

        previewLayersRef.current = true;
      }

      // Always update data when features change
      const src = map.getSource("preview-source") as maplibregl.GeoJSONSource | undefined;
      if (src) {
        console.log("[POI Manager] Updating GeoJSON source with", filteredFeatures.features.length, "features");
        src.setData(filteredFeatures);
      }

      // Auto-fit bounds from statistics.bbox
      if (statistics.bbox) {
        const { north, south, east, west } = statistics.bbox;
        if ([north, south, east, west].every((v) => v != null)) {
          console.log("[POI Manager] Fitting bounds:", { north, south, east, west });
          map.fitBounds([[west, south], [east, north]], { padding: 40, maxZoom: 14 });
        }
      }
    } else if (previewLayersRef.current) {
      // Features cleared — remove preview layers
      console.log("[POI Manager] Removing preview layers");
      ["preview-selected-highlight", "preview-circle", "preview-heatmap", "preview-cluster-count", "preview-cluster-circle"].forEach((id) => {
        if (map.getLayer(id)) map.removeLayer(id);
      });
      if (map.getSource("preview-source")) map.removeSource("preview-source");
      previewLayersRef.current = false;
    }
  }, [filteredFeatures, statistics, mapReady]);

  // Auto-fit bounds when entering Preview step
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady || currentStep !== 4) return;
    if (!statistics?.bbox) return;
    const { north, south, east, west } = statistics.bbox;
    if ([north, south, east, west].every((v) => v != null)) {
      console.log("[POI Manager] Fitting bounds on Preview entry:", { north, south, east, west });
      map.fitBounds([[west, south], [east, north]], { padding: 40, maxZoom: 14 });
    }
  }, [currentStep, mapReady, statistics]);

  // Sync selected highlight
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded() || !features) return;
    const layer = map.getLayer("preview-selected-highlight");
    if (!layer) return;
    if (!selectedPoiId) {
      map.setLayoutProperty("preview-selected-highlight", "visibility", "none");
      return;
    }
    const matched = (features.features as GeoJSON.Feature<GeoJSON.Point, PoiPreviewFeatureProperties>[]).find((f) => {
      const coords = (f.geometry as GeoJSON.Point).coordinates;
      const id = f.properties.osm_id || `${coords[0]}_${coords[1]}`;
      return id === selectedPoiId;
    });
    if (matched) {
      map.setLayoutProperty("preview-selected-highlight", "visibility", "visible");
      const src = map.getSource("preview-source") as
        | maplibregl.GeoJSONSource
        | undefined;
      if (src) {
        const allFeatures = features.features.filter(
          (f) => {
            const fProps = f.properties as PoiPreviewFeatureProperties;
            const mProps = matched.properties as PoiPreviewFeatureProperties;
            return (
              fProps.osm_id === mProps.osm_id &&
              (f.geometry as GeoJSON.Point).coordinates[0] ===
                (matched.geometry as GeoJSON.Point).coordinates[0] &&
              (f.geometry as GeoJSON.Point).coordinates[1] ===
                (matched.geometry as GeoJSON.Point).coordinates[1]
            );
          }
        );
      }
    }
  }, [selectedPoiId, features, mapReady]);

  // ---- Navigation guard ----
  useEffect(() => {
    if (!unsavedChanges) return;
    const handler = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      e.returnValue = "";
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [unsavedChanges]);

  // ---- Render ----

  const showToolbar =
    currentStep === 1 || currentStep === 3 || currentStep === 4;

  return (
    <div className="h-screen flex flex-col bg-background text-foreground">
      {/* Top toolbar */}
      <header className="h-12 border-b border-border flex items-center px-3 gap-3 bg-card shrink-0">
        <Button asChild variant="ghost" size="sm">
          <Link to="/">
            <ArrowLeft className="h-4 w-4" /> {t("back_to_dashboard")}
          </Link>
        </Button>
        <h1 className="text-sm font-semibold flex-1">
          {t("poi_manager_wizard_title")}
        </h1>
        {currentStep === 4 && (
          <span className="text-[10px] font-bold mono uppercase tracking-widest px-2 py-0.5 rounded bg-primary/10 text-primary">
            {t("poi_manager_preview_badge")}
          </span>
        )}
        {showToolbar && (
          <div className="flex items-center gap-1.5">
            <Button
              variant="outline"
              size="sm"
              className="h-7 text-xs gap-1"
              onClick={handleDownloadTemplate}
            >
              <FileDown className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">{t("poi_manager_download_template")}</span>
            </Button>
            {currentStep === 1 && (
              <Button
                size="sm"
                className="h-7 text-xs gap-1"
                onClick={() => {
                  const input = document.createElement("input");
                  input.type = "file";
                  input.accept = ".csv";
                  input.onchange = (e) => {
                    const file = (e.target as HTMLInputElement).files?.[0];
                    if (file) handleUpload(file);
                  };
                  input.click();
                }}
              >
                <Upload className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">{t("poi_manager_upload_csv")}</span>
              </Button>
            )}
            {(currentStep > 1) && (
              <Button
                variant="ghost"
                size="sm"
                className="h-7 text-xs gap-1 text-muted-foreground"
                onClick={handleReset}
              >
                <RotateCcw className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">{t("poi_manager_reset")}</span>
              </Button>
            )}
          </div>
        )}
      </header>

      {/* Wizard header */}
      {currentStep > 1 && currentStep < 5 && (
        <WizardHeader currentStep={currentStep} t={t} />
      )}

      {/* Step 1: Empty state */}
      {currentStep === 1 && (
        <EmptyState
          t={t}
          onDownloadTemplate={handleDownloadTemplate}
          onUpload={handleUpload}
          dragging={dragging}
          onDragChange={setDragging}
        />
      )}

      {/* Step 2: Upload progress */}
      {currentStep === 2 && (
        <div className="flex-1 flex items-center justify-center">
          <div className="max-w-sm w-full mx-4 space-y-4">
            <div className="flex items-center gap-3">
              <Loader2 className="h-5 w-5 animate-spin text-primary" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">
                  {uploadedFile?.name}
                </p>
                <p className="text-xs text-muted-foreground">
                  {t("poi_manager_uploading")}
                </p>
              </div>
            </div>
            <Progress value={uploadProgress} className="h-2" />
            <p className="text-xs text-muted-foreground text-center">
              {t("poi_manager_upload_progress").replace(
                "{percent}",
                Math.round(uploadProgress).toString()
              )}
            </p>
          </div>
        </div>
      )}

      {/* Step 3: Validation */}
      {currentStep === 3 && validation && statistics && (
        <div className="flex-1 overflow-y-auto">
          {/* SummaryBar */}
          <SummaryBar statistics={statistics} validation={validation} t={t} />

          {/* Validation cards */}
          <ValidationDashboard validation={validation} t={t} />

          {/* Continue button */}
          <div className="flex justify-center pb-6">
            <Button onClick={() => setCurrentStep(4)} disabled={!canImport}>
              {t("poi_manager_step_next")} → {t("poi_manager_step_preview")}
            </Button>
          </div>
        </div>
      )}

      {/* Step 4: Preview */}
      {currentStep === 4 && (
        <div className="flex-1 flex flex-col overflow-hidden">
          <SummaryBar statistics={statistics} validation={validation} t={t} />
          <div className="flex-1 flex overflow-hidden">
            <main className="flex-1 relative">
              {filteredFeatures && filteredFeatures.features.length > 0 ? (
                <div ref={containerRef} className="absolute inset-0" />
              ) : (
                <div className="absolute inset-0 flex items-center justify-center bg-muted/30">
                  <p className="text-sm text-muted-foreground">
                    {features && features.features.length > 0
                      ? t("poi_manager_all_deleted") || "All POIs have been removed"
                      : t("poi_manager_no_valid_pois") || "No valid POIs available for preview."}
                  </p>
                </div>
              )}
            </main>
            {filteredFeatures && filteredFeatures.features.length > 0 && (
              <PreviewSidebar
                features={filteredFeatures.features as GeoJSON.Feature<GeoJSON.Point, PoiPreviewFeatureProperties>[]}
                allCategories={allCategories}
                selectedPoiId={selectedPoiId}
                onPoiSelect={handlePoiSelect}
                onDeletePoi={handleDeletePoi}
                t={t}
              />
            )}
          </div>
          {/* Bottom action bar */}
          <div className="h-12 border-t border-border flex items-center justify-end px-4 gap-2 bg-card shrink-0">
            <Button
              variant="outline"
              size="sm"
              className="h-7 text-xs"
              onClick={handleReset}
            >
              {t("cancel")}
            </Button>
            <Button
              size="sm"
              className="h-7 text-xs gap-1"
              disabled={!canImport}
              onClick={handleImport}
            >
              <Download className="h-3.5 w-3.5" />
              {t("poi_manager_import")}
            </Button>
          </div>
        </div>
      )}

      {/* Step 5: Importing */}
      {currentStep === 5 && importing && (
        <div className="flex-1 flex items-center justify-center">
          <div className="flex flex-col items-center gap-4">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <p className="text-sm text-muted-foreground">
              {t("poi_manager_importing")}
            </p>
          </div>
        </div>
      )}

      {/* Step 6: Import Success */}
      {currentStep === 6 && importResult && (
        <div className="flex-1 flex items-center justify-center p-8">
          <ImportSuccessScreen
            result={importResult}
            processingTimeMs={processingTimeMs}
            onDashboard={() => navigate("/")}
            onImportAnother={handleImportAnother}
            t={t}
          />
        </div>
      )}

      {/* Loading skeletons for Step 3 while data loads */}
      {currentStep === 3 && !validation && (
        <div className="flex-1 p-4 space-y-4">
          <div className="flex gap-2">
            {[1, 2, 3, 4, 5].map((i) => (
              <Skeleton key={i} className="h-20 flex-1 rounded-lg" />
            ))}
          </div>
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-32 w-full" />
        </div>
      )}

      {/* Dialogs */}
      <ImportConfirmationDialog
        open={confirmDialogOpen}
        onOpenChange={setConfirmDialogOpen}
        onConfirm={handleConfirmImport}
        validation={validation}
        t={t}
      />

      {importResult && (
        <ImportSuccessDialog
          open={successDialogOpen}
          onOpenChange={setSuccessDialogOpen}
          result={importResult}
          processingTimeMs={processingTimeMs}
          onImportAnother={handleImportAnother}
          t={t}
        />
      )}

      {/* Unsaved changes dialog */}
      <AlertDialog
        open={pendingReset}
        onOpenChange={setPendingReset}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {t("poi_manager_unsaved_title")}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {t("poi_manager_unsaved_desc")}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="text-xs">
              {t("poi_manager_stay_page")}
            </AlertDialogCancel>
            <AlertDialogAction
              className="text-xs"
              onClick={handleConfirmReset}
            >
              {t("poi_manager_discard")}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

// Type imports for local use
import type {
  PoiValidationResult,
  PoiPreviewStatistics,
  PoiImportResponse,
} from "@/api/poiDataManagerTypes";
