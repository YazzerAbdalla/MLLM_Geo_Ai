import { useCallback, useEffect, useMemo, useRef, useState, useReducer } from "react";
import { Link } from "react-router-dom";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import {
  ArrowLeft, Database, Layers, Hash, ZoomIn, Crosshair, MapPin, Search, Filter,
  Square, Triangle, Trash2, Maximize2, Download,
  Send, Copy, Sparkles, Bot, User, RefreshCw, X, Plus,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Textarea } from "@/components/ui/textarea";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { useInternalPoiHeatmap } from "@/hooks/api/useInternalPoiHeatmap";
import { usePoiChat } from "@/hooks/api/usePoiChat";
import MessageBubble from "@/components/chat/MessageBubble";
import type { ChatMessage } from "@/api/types";
import { usePoiAnalysis } from "@/hooks/api/usePoiAnalysis";
import { useDebounce } from "@/hooks/useDebounce";
import { useI18n } from "@/lib/i18n";
import { cairoBbox } from "@/lib/api/mockClient";
import { getBboxFromGeometry } from "@/lib/geoUtils";
import booleanPointInPolygon from "@turf/boolean-point-in-polygon";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LabelList,
} from "recharts";
import type { InternalPoiHeatmapPoiProperties } from "@/api/types";
import type { DrawnGeometry } from "@/store/dashboardStore";

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

function rectRing(a: maplibregl.LngLat, b: maplibregl.LngLat): [number, number][] {
  return [
    [a.lng, a.lat],
    [b.lng, a.lat],
    [b.lng, b.lat],
    [a.lng, b.lat],
    [a.lng, a.lat],
  ];
}

function poiPopupHtml(props: InternalPoiHeatmapPoiProperties, coords: [number, number]): string {
  return `
    <div style="font-size:12px;line-height:1.6;color:#000;max-width:260px">
      <div style="font-weight:700;font-size:13px;margin-bottom:4px">${props.name}</div>
      <table style="width:100%;border-collapse:collapse">
        <tr><td style="opacity:.6;padding-right:8px;white-space:nowrap">Category</td><td style="font-family:monospace">${props.category}</td></tr>
        <tr><td style="opacity:.6;padding-right:8px;white-space:nowrap">Place Type</td><td style="font-family:monospace">${props.place_type}</td></tr>
        <tr><td style="opacity:.6;padding-right:8px;white-space:nowrap">OSM ID</td><td style="font-family:monospace">${props.osm_id}</td></tr>
        <tr><td style="opacity:.6;padding-right:8px;white-space:nowrap">Label</td><td style="font-family:monospace">${props.label}</td></tr>
        <tr><td style="opacity:.6;padding-right:8px;white-space:nowrap">Coords</td><td style="font-family:monospace">${coords[1].toFixed(5)}, ${coords[0].toFixed(5)}</td></tr>
      </table>
    </div>
  `;
}

function formatCentroid(centroid: { type: string; coordinates: [number, number] } | undefined | null): string {
  if (!centroid?.coordinates) return "—";
  const [lng, lat] = centroid.coordinates;
  return `Lat: ${typeof lat === "number" ? lat.toFixed(6) : "—"}, Lng: ${typeof lng === "number" ? lng.toFixed(6) : "—"}`;
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">{title}</h3>
      {children}
    </div>
  );
}

export default function InternalPoiHeatmap() {
  const { t } = useI18n();
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const popupRef = useRef<maplibregl.Popup | null>(null);
  const drawVerticesRef = useRef<[number, number][]>([]);
  const polygonLiveRef = useRef<boolean>(false);

  const [zoom, setZoom] = useState(10.4);
  const [mouseCoords, setMouseCoords] = useState<{ lng: number; lat: number } | null>(null);
  const [poiSearch, setPoiSearch] = useState("");
  const [searchCategory, setSearchCategory] = useState("__all");
  const [cairoOnly, setCairoOnly] = useState(false);
  const [drawMode, setDrawMode] = useState<"idle" | "draw-rect" | "draw-polygon">("idle");
  const [drawnGeometry, setDrawnGeometry] = useState<DrawnGeometry>(null);
  const [selectedPoiId, setSelectedPoiId] = useState<string | null>(null);
  const [mapReady, setMapReady] = useState(false);
  const mapDataRef = useRef<GeoJSON.FeatureCollection | null>(null);

  // Chat reducer
  type ChatState = {
    open: boolean;
    input: string;
    messages: ChatMessage[];
    loading: boolean;
    error: string | null;
    summary: string | null;
    copiedMessageId: string | null;
  };

  type ChatAction =
    | { type: "SET_OPEN"; payload: boolean }
    | { type: "SET_INPUT"; payload: string }
    | { type: "ADD_MESSAGE"; payload: ChatMessage }
    | { type: "UPDATE_MESSAGE"; payload: { id: string; changes: Partial<ChatMessage> } }
    | { type: "SET_LOADING"; payload: boolean }
    | { type: "SET_ERROR"; payload: string | null }
    | { type: "SET_SUMMARY"; payload: string }
    | { type: "SET_COPIED_ID"; payload: string | null }
    | { type: "CLEAR" }
    | { type: "TRIM_MESSAGES"; payload: number }
    | { type: "RESTORE"; payload: Partial<ChatState> & { messages: ChatMessage[] } };

  const initialChatState: ChatState = {
    open: false,
    input: "",
    messages: [],
    loading: false,
    error: null,
    summary: null,
    copiedMessageId: null,
  };

  function chatReducer(state: ChatState, action: ChatAction): ChatState {
    switch (action.type) {
      case "SET_OPEN":
        return { ...state, open: action.payload };
      case "SET_INPUT":
        return { ...state, input: action.payload };
      case "ADD_MESSAGE":
        return { ...state, messages: [...state.messages, action.payload] };
      case "UPDATE_MESSAGE":
        return {
          ...state,
          messages: state.messages.map((m) =>
            m.id === action.payload.id ? { ...m, ...action.payload.changes } : m,
          ),
        };
      case "SET_LOADING":
        return { ...state, loading: action.payload };
      case "SET_ERROR":
        return { ...state, error: action.payload };
      case "SET_SUMMARY":
        return { ...state, summary: action.payload };
      case "SET_COPIED_ID":
        return { ...state, copiedMessageId: action.payload };
      case "CLEAR":
        return { ...initialChatState, open: state.open };
      case "TRIM_MESSAGES":
        return {
          ...state,
          messages:
            state.messages.length > action.payload
              ? state.messages.slice(-action.payload)
              : state.messages,
        };
      case "RESTORE":
        return {
          ...state,
          messages: action.payload.messages,
          summary: action.payload.summary ?? state.summary,
          open: action.payload.open ?? state.open,
          loading: false,
          error: null,
          input: "",
        };
      default:
        return state;
    }
  }

  const [chat, dispatch] = useReducer(chatReducer, initialChatState);
  const poiChatMutation = usePoiChat();
  const chatBottomRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const chatInputRef = useRef<HTMLTextAreaElement>(null);
  const chatScrollRef = useRef<number>(0);
  const pendingNewAnalysisRef = useRef(false);
  const prevAnalysisKeyRef = useRef<string | null>(null);

  const { data, isLoading, isError } = useInternalPoiHeatmap();
  const debouncedGeometry = useDebounce(drawnGeometry, 400);
  const { data: analysis, isLoading: analysisLoading, isError: analysisError } = usePoiAnalysis(debouncedGeometry);

  const metadata = data?.metadata;
  const pois = useMemo(() => data?.features ?? [], [data]);
  const isEmpty = !isLoading && !isError && pois.length === 0;

  const isInsideCairo = useCallback((coords: [number, number]) => {
    const [lng, lat] = coords;
    return lat >= cairoBbox.south && lat <= cairoBbox.north && lng >= cairoBbox.west && lng <= cairoBbox.east;
  }, []);

  const poiCairoFlags = useMemo(() => {
    const inside = new Set<string>();
    const outside = new Set<string>();
    pois.forEach((f) => {
      const coords = (f.geometry as GeoJSON.Point).coordinates;
      const key = f.properties.osm_id || `${coords[0]}_${coords[1]}`;
      if (isInsideCairo(coords as [number, number])) {
        inside.add(key);
      } else {
        outside.add(key);
      }
    });
    return { inside, outside };
  }, [pois, isInsideCairo]);

  const insideCount = poiCairoFlags.inside.size;
  const outsideCount = poiCairoFlags.outside.size;

  const categorySet = useMemo(() => {
    const cats = new Set<string>();
    pois.forEach((f) => cats.add(f.properties.category));
    return cats;
  }, [pois]);

  const allCategories = useMemo(() => {
    const cats = [...new Set(pois.map((f) => f.properties.category))];
    cats.sort();
    return cats;
  }, [pois]);

  const filteredPois = useMemo(() => {
    let list = pois;
    if (cairoOnly) {
      list = list.filter((f) => {
        const coords = (f.geometry as GeoJSON.Point).coordinates;
        return isInsideCairo(coords as [number, number]);
      });
    }
    if (poiSearch) {
      const q = poiSearch.toLowerCase();
      list = list.filter((f) => {
        const props = f.properties;
        return (
          props.name.toLowerCase().includes(q) ||
          props.category.toLowerCase().includes(q) ||
          props.place_type.toLowerCase().includes(q)
        );
      });
    }
    if (searchCategory !== "__all") {
      list = list.filter((f) => f.properties.category === searchCategory);
    }
    return list;
  }, [pois, cairoOnly, poiSearch, searchCategory, isInsideCairo]);

  const mapData = useMemo(() => {
    if (!data) return null;
    const fc = !cairoOnly
      ? (data as unknown as GeoJSON.FeatureCollection)
      : {
          type: "FeatureCollection" as const,
          features: data.features.filter((f) => {
            const coords = (f.geometry as GeoJSON.Point).coordinates;
            return isInsideCairo(coords as [number, number]);
          }),
        };
    mapDataRef.current = fc;
    return fc;
  }, [data, cairoOnly, isInsideCairo]);

  const showPoiPopup = useCallback((props: InternalPoiHeatmapPoiProperties, coords: [number, number]) => {
    const map = mapRef.current;
    if (!map) return;
    if (popupRef.current) popupRef.current.remove();
    const popup = new maplibregl.Popup({ offset: 14, closeButton: true, maxWidth: "300px" })
      .setLngLat(coords)
      .setHTML(poiPopupHtml(props, coords))
      .addTo(map);
    popupRef.current = popup;
  }, []);

  const flyToPoi = useCallback((coords: [number, number]) => {
    const map = mapRef.current;
    if (!map) return;
    map.flyTo({ center: coords, zoom: 16, essential: true });
  }, []);

  const handlePoiSelect = useCallback((f: GeoJSON.Feature<GeoJSON.Point, InternalPoiHeatmapPoiProperties>) => {
    const coords = (f.geometry as GeoJSON.Point).coordinates as [number, number];
    const id = f.properties.osm_id || `${coords[0]}_${coords[1]}`;
    setSelectedPoiId(id);
    flyToPoi(coords);
    showPoiPopup(f.properties, coords);
  }, [flyToPoi, showPoiPopup]);

  // Map init
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: OSM_STYLE,
      center: [(cairoBbox.east + cairoBbox.west) / 2, (cairoBbox.north + cairoBbox.south) / 2],
      zoom: 10.4,
      attributionControl: { compact: true },
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    mapRef.current = map;

    map.on("load", () => {
      map.resize();
      map.addSource("internal-poi-source", {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
      });

      // Drawn polygon sources
      map.addSource("drawn", {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
      });
      map.addSource("draw-preview", {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
      });

      // POI highlight sources
      map.addSource("poi-inside", {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
      });
      map.addSource("poi-outside", {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
      });
      map.addSource("poi-selected", {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
      });

      // Heatmap layer
      map.addLayer({
        id: "internal-poi-heatmap",
        type: "heatmap",
        source: "internal-poi-source",
        paint: {
          "heatmap-weight": [
            "case",
            ["has", "weight"],
            ["interpolate", ["linear"], ["get", "weight"], 0, 0, 1, 1],
            1,
          ],
          "heatmap-radius": [
            "interpolate", ["linear"], ["zoom"],
            8, 40,
            18, 5,
          ],
          "heatmap-intensity": [
            "interpolate", ["linear"], ["zoom"],
            8, 1,
            18, 0.5,
          ],
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

      // Circle layers
      map.addLayer({
        id: "internal-poi-circle",
        type: "circle",
        source: "internal-poi-source",
        paint: {
          "circle-radius": [
            "interpolate", ["linear"], ["zoom"],
            0, 0,
            12, 0,
            12.01, 9,
            22, 9,
          ],
          "circle-color": "#e63946",
          "circle-stroke-color": "#ffffff",
          "circle-stroke-width": 1.5,
          "circle-opacity": 0.9,
        },
      });

      // POI outside (faded) — hidden by default
      map.addLayer({
        id: "poi-outside-faded",
        type: "circle",
        source: "poi-outside",
        layout: { visibility: "none" },
        paint: {
          "circle-radius": [
            "interpolate", ["linear"], ["zoom"],
            0, 0,
            12, 0,
            12.01, 9,
            22, 9,
          ],
          "circle-color": "#6b7280",
          "circle-opacity": 0.15,
          "circle-stroke-color": "#6b7280",
          "circle-stroke-width": 0.5,
        },
      });

      // POI inside (highlight) — hidden by default
      map.addLayer({
        id: "poi-inside-highlight",
        type: "circle",
        source: "poi-inside",
        layout: { visibility: "none" },
        paint: {
          "circle-radius": [
            "interpolate", ["linear"], ["zoom"],
            0, 0,
            12, 0,
            12.01, 10,
            22, 10,
          ],
          "circle-color": "#3B82F6",
          "circle-opacity": 0.85,
          "circle-stroke-color": "#ffffff",
          "circle-stroke-width": 2,
        },
      });

      // Drawn polygon fill
      map.addLayer({
        id: "drawn-fill",
        type: "fill",
        source: "drawn",
        paint: {
          "fill-color": "#3B82F6",
          "fill-opacity": 0.15,
        },
      });

      // Drawn polygon line
      map.addLayer({
        id: "drawn-line",
        type: "line",
        source: "drawn",
        paint: {
          "line-color": "#3B82F6",
          "line-width": 2.5,
          "line-dasharray": [4, 2],
        },
      });

      // Drawn vertices
      map.addLayer({
        id: "drawn-vertices",
        type: "circle",
        source: "draw-preview",
        paint: {
          "circle-radius": 5,
          "circle-color": "#3B82F6",
          "circle-stroke-color": "#ffffff",
          "circle-stroke-width": 1.5,
        },
      });

      // Selected POI highlight (topmost)
      map.addLayer({
        id: "poi-selected-highlight",
        type: "circle",
        source: "poi-selected",
        layout: { visibility: "none" },
        paint: {
          "circle-radius": 14,
          "circle-color": "#FCD34D",
          "circle-opacity": 0.7,
          "circle-stroke-color": "#ffffff",
          "circle-stroke-width": 3,
        },
      });

      // Click on existing circles
      map.on("click", "internal-poi-circle", (e) => {
        const f = e.features?.[0];
        if (!f) return;
        const props = f.properties as unknown as InternalPoiHeatmapPoiProperties;
        const coords = (f.geometry as GeoJSON.Point).coordinates as [number, number];
        showPoiPopup(props, coords);
      });

      // Click on inside highlight
      map.on("click", "poi-inside-highlight", (e) => {
        const f = e.features?.[0];
        if (!f) return;
        const props = f.properties as unknown as InternalPoiHeatmapPoiProperties;
        const coords = (f.geometry as GeoJSON.Point).coordinates as [number, number];
        const id = props.osm_id || `${coords[0]}_${coords[1]}`;
        setSelectedPoiId(id);
        showPoiPopup(props, coords);
      });

      map.on("mouseenter", "internal-poi-circle", () => (map.getCanvas().style.cursor = "pointer"));
      map.on("mouseleave", "internal-poi-circle", () => (map.getCanvas().style.cursor = ""));
      map.on("mouseenter", "poi-inside-highlight", () => (map.getCanvas().style.cursor = "pointer"));
      map.on("mouseleave", "poi-inside-highlight", () => (map.getCanvas().style.cursor = ""));

      map.on("zoom", () => setZoom(map.getZoom()));
      map.on("mousemove", (e) => setMouseCoords({ lng: e.lngLat.lng, lat: e.lngLat.lat }));

      // If data already loaded, populate sources now
      const existingData = mapDataRef.current;
      if (existingData && existingData.features.length > 0) {
        const src = map.getSource("internal-poi-source") as maplibregl.GeoJSONSource | undefined;
        if (src) src.setData(existingData);
      }

      setMapReady(true);
    });

    return () => {
      map.remove();
      mapRef.current = null;
      setMapReady(false);
    };
  }, [showPoiPopup]);

  // Resize map when container dimensions change
  useEffect(() => {
    const map = mapRef.current;
    const el = containerRef.current;
    if (!map || !el) return;
    const ro = new ResizeObserver(() => { if (map.loaded()) map.resize(); });
    ro.observe(el);
    return () => ro.disconnect();
  }, [mapReady]);

  // Sync heatmap data
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded() || !mapData) return;
    const src = map.getSource("internal-poi-source") as maplibregl.GeoJSONSource | undefined;
    if (src) src.setData(mapData);
  }, [mapData, mapReady]);

  // Sync drawn geometry to map
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;
    const src = map.getSource("drawn") as maplibregl.GeoJSONSource | undefined;
    if (!src) return;
    const empty: GeoJSON.FeatureCollection = { type: "FeatureCollection", features: [] };
    if (drawnGeometry) {
      src.setData({
        type: "FeatureCollection",
        features: [{ type: "Feature", properties: {}, geometry: drawnGeometry } as GeoJSON.Feature],
      });
    } else {
      src.setData(empty);
    }
  }, [drawnGeometry, mapReady]);

  // Clear previous selection when starting a new draw
  useEffect(() => {
    if (drawMode !== "idle") {
      setDrawnGeometry(null);
      setSelectedPoiId(null);
      drawVerticesRef.current = [];
      polygonLiveRef.current = false;
      if (popupRef.current) {
        popupRef.current.remove();
        popupRef.current = null;
      }
    }
  }, [drawMode]);

  // Rectangle drawing
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    if (drawMode !== "draw-rect") {
      map.getCanvas().style.cursor = "";
      return;
    }
    const canvas = map.getCanvas();
    canvas.style.cursor = "crosshair";
    map.dragPan.disable();
    map.boxZoom.disable();

    let start: maplibregl.LngLat | null = null;

    const onDown = (e: maplibregl.MapMouseEvent) => { start = e.lngLat; };
    const onMove = (e: maplibregl.MapMouseEvent) => {
      if (!start) return;
      const ring = rectRing(start, e.lngLat);
      const src = map.getSource("drawn") as maplibregl.GeoJSONSource | undefined;
      const fc: GeoJSON.FeatureCollection = {
        type: "FeatureCollection",
        features: [{ type: "Feature", properties: {}, geometry: { type: "Polygon", coordinates: [ring] } as GeoJSON.Polygon }],
      };
      src?.setData(fc);
    };
    const onUp = (e: maplibregl.MapMouseEvent) => {
      if (!start) return;
      const ring = rectRing(start, e.lngLat);
      setDrawnGeometry({ type: "Polygon", coordinates: [ring] });
      setDrawMode("idle");
      map.dragPan.enable();
      map.boxZoom.enable();
      start = null;
    };

    map.on("mousedown", onDown);
    map.on("mousemove", onMove);
    map.on("mouseup", onUp);
    return () => {
      map.off("mousedown", onDown);
      map.off("mousemove", onMove);
      map.off("mouseup", onUp);
      map.dragPan.enable();
      map.boxZoom.enable();
    };
  }, [drawMode]);

  // Polygon drawing
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    if (drawMode !== "draw-polygon") {
      map.getCanvas().style.cursor = "";
      return;
    }
    const canvas = map.getCanvas();
    canvas.style.cursor = "crosshair";
    map.dragPan.disable();
    map.boxZoom.disable();
    map.doubleClickZoom.disable();
    drawVerticesRef.current = [];
    polygonLiveRef.current = true;

    const onClick = (e: maplibregl.MapMouseEvent) => {
      drawVerticesRef.current.push([e.lngLat.lng, e.lngLat.lat]);
      updatePreview(map, drawVerticesRef.current);
    };

    const onDblClick = () => {
      finishPolygon(map);
    };

    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        cancelPolygon(map);
      }
    };

    map.on("click", onClick);
    map.on("dblclick", onDblClick);
    window.addEventListener("keydown", onKeyDown);

    return () => {
      map.off("click", onClick);
      map.off("dblclick", onDblClick);
      window.removeEventListener("keydown", onKeyDown);
      map.dragPan.enable();
      map.boxZoom.enable();
      map.doubleClickZoom.enable();
    };
  }, [drawMode]);

  function updatePreview(map: maplibregl.Map, vertices: [number, number][]) {
    const previewSrc = map.getSource("draw-preview") as maplibregl.GeoJSONSource | undefined;
    if (!previewSrc) return;
    if (vertices.length < 2) {
      const fc: GeoJSON.FeatureCollection = {
        type: "FeatureCollection",
        features: vertices.length === 1 ? [{
          type: "Feature", properties: {},
          geometry: { type: "Point", coordinates: vertices[0] },
        } as GeoJSON.Feature] : [],
      };
      previewSrc.setData(fc);
      return;
    }
    const fc: GeoJSON.FeatureCollection = {
      type: "FeatureCollection",
      features: [
        { type: "Feature", properties: {}, geometry: { type: "LineString", coordinates: [...vertices, vertices[0]] } as GeoJSON.LineString },
        ...vertices.map((v): GeoJSON.Feature => ({ type: "Feature", properties: {}, geometry: { type: "Point", coordinates: v } })),
      ],
    };
    previewSrc.setData(fc);
  }

  function finishPolygon(map: maplibregl.Map) {
    const vertices = drawVerticesRef.current;
    if (vertices.length < 3) {
      setDrawMode("idle");
      map.dragPan.enable();
      map.boxZoom.enable();
      map.doubleClickZoom.enable();
      return;
    }
    const ring = [...vertices, vertices[0]];
    setDrawnGeometry({ type: "Polygon", coordinates: [ring] });
    setDrawMode("idle");
    polygonLiveRef.current = false;
    const empty: GeoJSON.FeatureCollection = { type: "FeatureCollection", features: [] };
    const previewSrc = map.getSource("draw-preview") as maplibregl.GeoJSONSource | undefined;
    previewSrc?.setData(empty);
    map.dragPan.enable();
    map.boxZoom.enable();
    map.doubleClickZoom.enable();
  }

  function cancelPolygon(map: maplibregl.Map) {
    drawVerticesRef.current = [];
    polygonLiveRef.current = false;
    setDrawMode("idle");
    const empty: GeoJSON.FeatureCollection = { type: "FeatureCollection", features: [] };
    const previewSrc = map.getSource("draw-preview") as maplibregl.GeoJSONSource | undefined;
    previewSrc?.setData(empty);
    const drawnSrc = map.getSource("drawn") as maplibregl.GeoJSONSource | undefined;
    drawnSrc?.setData(empty);
    map.dragPan.enable();
    map.boxZoom.enable();
    map.doubleClickZoom.enable();
  }

  // Zoom to selection on draw complete
  useEffect(() => {
    if (!drawnGeometry) return;
    const map = mapRef.current;
    if (!map) return;
    const bbox = getBboxFromGeometry(drawnGeometry);
    if (bbox) {
      map.fitBounds([[bbox.west, bbox.south], [bbox.east, bbox.north]], { padding: 60, maxZoom: 16 });
    }
  }, [drawnGeometry]);

  const handleZoomToSelection = useCallback(() => {
    if (!drawnGeometry) return;
    const map = mapRef.current;
    if (!map) return;
    const bbox = getBboxFromGeometry(drawnGeometry);
    if (bbox) {
      map.fitBounds([[bbox.west, bbox.south], [bbox.east, bbox.north]], { padding: 60, maxZoom: 16 });
    }
  }, [drawnGeometry]);

  const handleDelete = useCallback(() => {
    setDrawnGeometry(null);
    setSelectedPoiId(null);
    setDrawMode("idle");
  }, []);

  // Sync POI highlight/fade layers
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;

    const insideSrc = map.getSource("poi-inside") as maplibregl.GeoJSONSource | undefined;
    const outsideSrc = map.getSource("poi-outside") as maplibregl.GeoJSONSource | undefined;
    if (!insideSrc || !outsideSrc) return;

    const circleLayer = map.getLayer("internal-poi-circle");
    const fadedLayer = map.getLayer("poi-outside-faded");
    const highlightLayer = map.getLayer("poi-inside-highlight");

    const empty: GeoJSON.FeatureCollection = { type: "FeatureCollection", features: [] };
    if (!drawnGeometry) {
      if (circleLayer) map.setLayoutProperty("internal-poi-circle", "visibility", "visible");
      if (fadedLayer) map.setLayoutProperty("poi-outside-faded", "visibility", "none");
      if (highlightLayer) map.setLayoutProperty("poi-inside-highlight", "visibility", "none");
      insideSrc.setData(empty);
      outsideSrc.setData(empty);
      return;
    }

    const polygon = drawnGeometry;
    const inside: GeoJSON.Feature[] = [];
    const outside: GeoJSON.Feature[] = [];

    for (const f of pois) {
      const coords = (f.geometry as GeoJSON.Point).coordinates;
      const insidePoly = booleanPointInPolygon(coords as [number, number], polygon as GeoJSON.Polygon);
      if (insidePoly) {
        inside.push(f);
      } else {
        outside.push(f);
      }
    }

    if (circleLayer) map.setLayoutProperty("internal-poi-circle", "visibility", "none");
    if (fadedLayer) map.setLayoutProperty("poi-outside-faded", "visibility", "visible");
    if (highlightLayer) map.setLayoutProperty("poi-inside-highlight", "visibility", "visible");

    insideSrc.setData({ type: "FeatureCollection", features: inside });
    outsideSrc.setData({ type: "FeatureCollection", features: outside });
  }, [drawnGeometry, pois, mapReady]);

  // Sync selected POI highlight
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;
    const src = map.getSource("poi-selected") as maplibregl.GeoJSONSource | undefined;
    const layer = map.getLayer("poi-selected-highlight");
    if (!src || !layer) return;

    const empty: GeoJSON.FeatureCollection = { type: "FeatureCollection", features: [] };
    if (!selectedPoiId) {
      map.setLayoutProperty("poi-selected-highlight", "visibility", "none");
      src.setData(empty);
      return;
    }

    const matched = pois.find((f) => {
      const coords = (f.geometry as GeoJSON.Point).coordinates;
      const id = f.properties.osm_id || `${coords[0]}_${coords[1]}`;
      return id === selectedPoiId;
    });
    if (matched) {
      map.setLayoutProperty("poi-selected-highlight", "visibility", "visible");
      src.setData({ type: "FeatureCollection", features: [matched] });
    }
  }, [selectedPoiId, pois, mapReady]);

  const handleExport = useCallback(() => {
    if (!drawnGeometry || !analysis) return;
    const exportData = {
      polygon: drawnGeometry,
      statistics: analysis.analysis,
      matching_pois: analysis.features,
    };
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    const name = analysis.analysis.reverse_geocoding?.area_name || "selection";
    a.download = `poi-analysis-${name.replace(/[^a-zA-Z0-9_-]/g, "_")}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [drawnGeometry, analysis]);

  // Chat handlers
  const createMessage = useCallback((role: ChatMessage["role"], content: string, status: ChatMessage["status"]): ChatMessage => {
    return { id: crypto.randomUUID(), role, content, status };
  }, []);

  const handleSend = useCallback(() => {
    const question = chat.input.trim();
    if (!question || !analysis) return;

    const userMsg = createMessage("user", question, "completed");
    const pendingMsg = createMessage("assistant", "", "pending");

    dispatch({ type: "ADD_MESSAGE", payload: userMsg });
    dispatch({ type: "ADD_MESSAGE", payload: pendingMsg });
    dispatch({ type: "SET_LOADING", payload: true });
    dispatch({ type: "SET_ERROR", payload: null });
    dispatch({ type: "SET_INPUT", payload: "" });

    const history = chat.messages
      .filter((m) => m.status !== "pending")
      .map((m) => ({ role: m.role, content: m.content }));

    const requestPayload = {
      analysis: analysis.analysis,
      question,
      history,
    };

    poiChatMutation.mutate(requestPayload, {
      onSuccess: (response) => {
        dispatch({
          type: "UPDATE_MESSAGE",
          payload: { id: pendingMsg.id, changes: { content: response.answer, status: "completed" } },
        });
        if (response.summary) {
          dispatch({ type: "SET_SUMMARY", payload: response.summary });
        }
        dispatch({ type: "SET_LOADING", payload: false });
        dispatch({ type: "TRIM_MESSAGES", payload: 50 });
      },
      onError: () => {
        dispatch({
          type: "UPDATE_MESSAGE",
          payload: {
            id: pendingMsg.id,
            changes: {
              content: "Request failed",
              status: "failed",
              request: requestPayload,
            },
          },
        });
        dispatch({ type: "SET_LOADING", payload: false });
        dispatch({ type: "SET_ERROR", payload: "Request failed" });
      },
    });
  }, [chat.input, chat.messages, analysis, poiChatMutation, createMessage]);

  const handleRetry = useCallback(
    (request: ChatMessage["request"]) => {
      if (!request || !analysis) return;

      const pendingMsg = createMessage("assistant", "", "pending");
      dispatch({ type: "ADD_MESSAGE", payload: pendingMsg });
      dispatch({ type: "SET_LOADING", payload: true });

      poiChatMutation.mutate(request, {
        onSuccess: (response) => {
          dispatch({
            type: "UPDATE_MESSAGE",
            payload: { id: pendingMsg.id, changes: { content: response.answer, status: "completed" } },
          });
          if (response.summary) {
            dispatch({ type: "SET_SUMMARY", payload: response.summary });
          }
          dispatch({ type: "SET_LOADING", payload: false });
          dispatch({ type: "TRIM_MESSAGES", payload: 50 });
        },
        onError: () => {
          dispatch({
            type: "UPDATE_MESSAGE",
            payload: {
              id: pendingMsg.id,
              changes: { content: "Request failed", status: "failed", request },
            },
          });
          dispatch({ type: "SET_LOADING", payload: false });
        },
      });
    },
    [analysis, poiChatMutation, createMessage],
  );

  const handleCopy = useCallback((content: string, messageId: string) => {
    navigator.clipboard.writeText(content);
    dispatch({ type: "SET_COPIED_ID", payload: messageId });
    setTimeout(() => dispatch({ type: "SET_COPIED_ID", payload: null }), 2000);
  }, []);

  const suggestions = useMemo(() => {
    if (!analysis) {
      return [
        "Summarize this area.",
        "Explain the POI distribution.",
        "What services dominate this area?",
        "Which categories are underrepresented?",
        "Is this area mixed-use?",
        "Is it suitable for a pharmacy?",
        "Is it suitable for a supermarket?",
        "What businesses could be added?",
        "Explain the POI density.",
        "What are the strengths of this area?",
        "What are the weaknesses of this area?",
      ];
    }

    const topCats = analysis.analysis.top_categories ?? [];
    const dominant = topCats[0]?.category;
    const density = analysis.analysis.poi_density;

    const s: string[] = ["Summarize this area.", "Explain the POI distribution."];

    if (dominant) {
      const d = dominant.toLowerCase();
      s.push(`Why are ${d} businesses dominant here?`);
      if (d.includes("restaurant") || d.includes("food") || d.includes("cafe")) {
        s.push("Is this area a dining destination?");
      } else if (d.includes("retail") || d.includes("shop") || d.includes("supermarket")) {
        s.push("Is this area suitable for another supermarket?");
      }
    }

    const present = new Set(topCats.map((c) => c.category.toLowerCase()));
    if (!present.has("pharmacy") && !present.has("healthcare")) {
      s.push("Would a pharmacy fit this area?");
    }
    if (!present.has("supermarket") && !present.has("grocery")) {
      s.push("Would a supermarket fit this area?");
    }

    s.push(
      "Which categories are underrepresented?",
      "Is this area mixed-use?",
      "What businesses could be added?",
    );
    if (density !== undefined) {
      s.push(`Explain the POI density of ${density.toFixed(1)}/km².`);
    }
    s.push("What are the strengths of this area?", "What are the weaknesses of this area?");
    return s.slice(0, 12);
  }, [analysis]);

  // Smart auto-scroll
  useEffect(() => {
    const container = chatContainerRef.current;
    if (!container) return;
    const threshold = 100;
    const dist = container.scrollHeight - container.scrollTop - container.clientHeight;
    if (dist < threshold) {
      chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [chat.messages]);

  // Preserve chat during polygon editing — clear only after new analysis for a different polygon
  useEffect(() => {
    if (drawnGeometry === null) {
      pendingNewAnalysisRef.current = true;
    }
  }, [drawnGeometry]);

  useEffect(() => {
    if (analysis && pendingNewAnalysisRef.current) {
      const newKey = JSON.stringify(debouncedGeometry);
      const oldKey = prevAnalysisKeyRef.current;
      if (oldKey !== null && newKey !== oldKey) {
        dispatch({ type: "CLEAR" });
        dispatch({ type: "SET_SUMMARY", payload: null });
      }
      prevAnalysisKeyRef.current = newKey;
      pendingNewAnalysisRef.current = false;
    }
  }, [analysis, debouncedGeometry]);

  // Session persistence
  const STORAGE_KEY = "poi-analysis-chat";
  const analysisHashRef = useRef<string | null>(null);

  // Compute current analysis hash
  const currentAnalysisHash = useMemo(() => {
    if (!analysis) return null;
    return JSON.stringify(debouncedGeometry);
  }, [analysis, debouncedGeometry]);

  // Restore from sessionStorage on mount
  useEffect(() => {
    try {
      const stored = sessionStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        if (parsed.messages && parsed.analysisHash && parsed.analysisHash === currentAnalysisHash) {
          dispatch({ type: "RESTORE", payload: parsed });
        }
      }
    } catch { /* ignore corrupt storage */ }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Persist to sessionStorage on state changes
  useEffect(() => {
    analysisHashRef.current = currentAnalysisHash;
    const data = {
      messages: chat.messages,
      summary: chat.summary,
      open: chat.open,
      analysisHash: currentAnalysisHash,
      timestamp: Date.now(),
    };
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    } catch { /* storage full */ }
  }, [chat.messages, chat.summary, chat.open, currentAnalysisHash, analysis]);

  // Auto-focus input + restore scroll when drawer opens
  useEffect(() => {
    if (chat.open) {
      setTimeout(() => {
        chatInputRef.current?.focus();
        if (chatContainerRef.current && chatScrollRef.current > 0) {
          chatContainerRef.current.scrollTop = chatScrollRef.current;
        }
      }, 100);
    } else {
      // Save scroll position before closing
      if (chatContainerRef.current) {
        chatScrollRef.current = chatContainerRef.current.scrollTop;
      }
    }
  }, [chat.open]);

  const drawHint = drawMode === "draw-rect"
    ? t("poi_analysis_draw_hint_rect")
    : drawMode === "draw-polygon"
      ? t("poi_analysis_draw_hint_polygon")
      : null;

  if (isLoading) {
    return (
      <div className="h-screen flex items-center justify-center bg-background text-foreground">
        <p className="text-muted-foreground">{t("loading")}</p>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="h-screen flex flex-col items-center justify-center gap-3 bg-background text-foreground">
        <p className="text-muted-foreground">Failed to load POI dataset.</p>
        <Button asChild variant="outline" size="sm">
          <Link to="/"><ArrowLeft className="h-4 w-4" /> {t("back_to_dashboard")}</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-background text-foreground">
      <header className="h-12 border-b border-border flex items-center px-3 gap-3 bg-card shrink-0">
        <Button asChild variant="ghost" size="sm">
          <Link to="/"><ArrowLeft className="h-4 w-4" /> {t("back_to_dashboard")}</Link>
        </Button>
        <h1 className="text-sm font-semibold flex-1">{t("internal_poi_heatmap_title")}</h1>
        <span className="text-[10px] font-bold mono uppercase tracking-widest px-2 py-0.5 rounded bg-secondary text-muted-foreground">
          {t("internal_poi_heatmap_badge")}
        </span>
        {drawMode !== "idle" && (
          <span className="text-[11px] text-primary font-mono font-semibold">
            ● {drawMode === "draw-rect" ? t("poi_analysis_draw_rect") : t("poi_analysis_draw_polygon")} mode
          </span>
        )}
      </header>

      <div className="flex-1 flex overflow-hidden">
        <main className="flex-1 relative">
          {isEmpty && (
            <div className="absolute inset-0 flex items-center justify-center z-10 bg-background/80">
              <p className="text-muted-foreground">{t("internal_poi_heatmap_empty")}</p>
            </div>
          )}
          <div ref={containerRef} className="absolute inset-0" />
          {drawHint && (
            <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-10 bg-card/90 backdrop-blur border border-border rounded-lg px-4 py-2 text-xs text-muted-foreground shadow-lg">
              {drawHint}
            </div>
          )}
        </main>

        <aside className="w-[300px] shrink-0 border-l border-border bg-card overflow-y-auto p-3 space-y-4">
          {/* Drawing Tools */}
          <Section title={t("poi_analysis_title")}>
            <div className="flex gap-1.5 mb-1.5">
              <Button
                size="sm"
                variant={drawMode === "draw-rect" ? "default" : "outline"}
                className="h-7 text-xs gap-1"
                onClick={() => setDrawMode(drawMode === "draw-rect" ? "idle" : "draw-rect")}
              >
                <Square className="h-3 w-3" /> {t("poi_analysis_draw_rect")}
              </Button>
              <Button
                size="sm"
                variant={drawMode === "draw-polygon" ? "default" : "outline"}
                className="h-7 text-xs gap-1"
                onClick={() => setDrawMode(drawMode === "draw-polygon" ? "idle" : "draw-polygon")}
              >
                <Triangle className="h-3 w-3" /> {t("poi_analysis_draw_polygon")}
              </Button>
            </div>
            {drawnGeometry && (
              <div className="flex gap-1.5">
                <Button size="sm" variant="outline" className="h-7 text-xs gap-1" onClick={handleZoomToSelection}>
                  <Maximize2 className="h-3 w-3" /> {t("poi_analysis_zoom_selection")}
                </Button>
                <Button size="sm" variant="outline" className="h-7 text-xs gap-1 text-destructive" onClick={handleDelete}>
                  <Trash2 className="h-3 w-3" /> {t("poi_analysis_delete")}
                </Button>
              </div>
            )}
          </Section>

          {/* Analysis Panel */}
          {drawnGeometry && (
            <div className="border-t border-border pt-3 space-y-3">
              <h3 className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                {t("poi_analysis_title")}
              </h3>

              {analysisLoading && (
                <div className="space-y-2">
                  <Skeleton className="h-6 w-full" />
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-20 w-full" />
                </div>
              )}

              {analysisError && (
                <p className="text-xs text-destructive">Analysis request failed.</p>
              )}

              {analysis && !analysisLoading && (
                <>
                  {/* Summary Header */}
                  <div className="flex flex-wrap gap-1.5">
                    <CompactStat
                      label={t("poi_analysis_summary_area")}
                      value={analysis.analysis.reverse_geocoding?.area_name ?? "Not available"}
                    />
                    <CompactStat
                      label={t("poi_analysis_summary_pois")}
                      value={analysis.analysis.total_pois?.toLocaleString() ?? "—"}
                    />
                    <CompactStat
                      label={t("poi_analysis_summary_density")}
                      value={typeof analysis.analysis.poi_density === "number" ? `${analysis.analysis.poi_density.toFixed(1)}/km²` : "—"}
                    />
                    <CompactStat
                      label={t("poi_analysis_summary_dominant")}
                      value={analysis.analysis.top_categories?.[0]?.category ?? "—"}
                    />
                  </div>

                  {/* Stats */}
                  <div className="grid grid-cols-2 gap-1.5">
                    <Stat icon={<MapPin className="h-3.5 w-3.5" />} label={t("poi_analysis_summary_area")} value={analysis.analysis.reverse_geocoding?.area_name ?? "Not available"} />
                    <Stat icon={<MapPin className="h-3.5 w-3.5" />} label={t("poi_analysis_city") || "City"} value={analysis.analysis.reverse_geocoding?.city ?? "Not available"} />
                    <Stat icon={<MapPin className="h-3.5 w-3.5" />} label={t("poi_analysis_country") || "Country"} value={analysis.analysis.reverse_geocoding?.country ?? "Not available"} />
                    <Stat icon={<Database className="h-3.5 w-3.5" />} label={t("poi_analysis_area")} value={typeof analysis.analysis.area_km2 === "number" ? `${analysis.analysis.area_km2.toFixed(2)} km²` : "—"} />
                    <Stat icon={<Layers className="h-3.5 w-3.5" />} label={t("poi_analysis_perimeter")} value={typeof analysis.analysis.perimeter_m === "number" ? `${(analysis.analysis.perimeter_m / 1000).toFixed(2)} km` : "—"} />
                    <Stat icon={<Hash className="h-3.5 w-3.5" />} label={t("poi_analysis_summary_pois")} value={analysis.analysis.total_pois?.toLocaleString() ?? "—"} />
                    <Stat icon={<Crosshair className="h-3.5 w-3.5" />} label={t("poi_analysis_center")} value={formatCentroid(analysis.analysis.centroid)} mono />
                  </div>

                  {/* Category Breakdown Chart */}
                  {analysis.analysis.top_categories && analysis.analysis.top_categories.length > 0 && (
                    <div className="pt-1">
                      <h4 className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1.5">
                        {t("internal_poi_heatmap_stat_categories")}
                      </h4>
                      <div className="rounded border border-border bg-secondary/20 p-2">
                        <ResponsiveContainer width="100%" height={Math.min(analysis.analysis.top_categories.length * 32, 180)}>
                          <BarChart data={analysis.analysis.top_categories} layout="vertical" margin={{ left: 0, right: 36, top: 0, bottom: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="hsl(var(--border))" />
                            <XAxis type="number" tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} />
                            <YAxis type="category" dataKey="category" tick={{ fontSize: 10, fill: "hsl(var(--foreground))" }} width={80} />
                            <Tooltip
                              contentStyle={{
                                backgroundColor: "hsl(var(--card))",
                                border: "1px solid hsl(var(--border))",
                                borderRadius: "6px",
                                fontSize: "12px",
                                color: "hsl(var(--foreground))",
                              }}
                              formatter={(value: number) => [value.toLocaleString(), "Count"]}
                            />
                            <Bar dataKey="count" fill="#3B82F6" radius={[0, 4, 4, 0]} minPointSize={3}>
                              <LabelList dataKey="count" position="right" style={{ fontSize: "10px", fill: "#3B82F6", fontWeight: 600 }} />
                            </Bar>
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  )}

                  {/* Export */}
                  <Button size="sm" variant="outline" className="w-full h-7 text-xs gap-1" onClick={handleExport}>
                    <Download className="h-3 w-3" /> {t("poi_analysis_export")}
                  </Button>
                </>
              )}
            </div>
          )}

          {/* Existing sections */}
          <div className="border-t border-border pt-2">
            <h2 className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">
              {t("internal_poi_heatmap_statistics")}
            </h2>
            <Stat icon={<Database className="h-3.5 w-3.5" />} label={t("internal_poi_heatmap_stat_total")} value={metadata?.total_pois?.toLocaleString() ?? pois.length.toLocaleString()} />
            <Stat icon={<Layers className="h-3.5 w-3.5" />} label={t("internal_poi_heatmap_stat_categories")} value={metadata?.num_categories?.toLocaleString() ?? categorySet.size.toLocaleString()} />
            <Stat icon={<Hash className="h-3.5 w-3.5" />} label={t("internal_poi_heatmap_stat_source")} value={metadata?.dataset_source ?? "project.csv"} />
            <Stat icon={<ZoomIn className="h-3.5 w-3.5" />} label={t("internal_poi_heatmap_stat_zoom")} value={zoom.toFixed(1)} />
            {mouseCoords && (
              <Stat
                icon={<Crosshair className="h-3.5 w-3.5" />}
                label={t("internal_poi_heatmap_stat_coords")}
                value={`${mouseCoords.lat.toFixed(4)}, ${mouseCoords.lng.toFixed(4)}`}
                mono
              />
            )}
          </div>

          <div className="border-t border-border pt-2">
            <h3 className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">
              {t("internal_poi_heatmap_legend")}
            </h3>
            <div className="space-y-1.5">
              <div className="flex items-center gap-2 text-xs">
                <div className="w-4 h-4 rounded" style={{ background: "linear-gradient(to right, rgb(254,204,92), rgb(253,141,60), rgb(240,59,32))" }} />
                <span className="text-muted-foreground">{t("internal_poi_heatmap_density")}</span>
              </div>
              <div className="flex items-center gap-2 text-xs">
                <div className="w-4 h-4 rounded-full border border-white bg-[#e63946]" />
                <span className="text-muted-foreground">{t("internal_poi_heatmap_point")}</span>
              </div>
            </div>
          </div>

          <div className="border-t border-border space-y-2 pt-2">
            <h3 className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">{t("filter")}</h3>
            <div className="flex items-center justify-between rounded border border-border bg-secondary/40 px-2.5 py-2">
              <div className="flex items-center gap-1.5 text-xs">
                <Filter className="h-3.5 w-3.5 text-muted-foreground" />
                <span className="text-muted-foreground">Cairo bbox only</span>
              </div>
              <button
                onClick={() => setCairoOnly(!cairoOnly)}
                className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${cairoOnly ? "bg-primary" : "bg-border"}`}
              >
                <span className={`inline-block h-3.5 w-3.5 rounded-full bg-white transition-transform ${cairoOnly ? "translate-x-[18px]" : "translate-x-[3px]"}`} />
              </button>
            </div>
            <div className="grid grid-cols-2 gap-1.5 text-xs">
              <div className="rounded border border-border bg-secondary/40 px-2 py-1.5">
                <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Inside</div>
                <div className="font-semibold mono">{insideCount.toLocaleString()}</div>
              </div>
              <div className="rounded border border-border bg-secondary/40 px-2 py-1.5">
                <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Outside</div>
                <div className="font-semibold mono">{outsideCount.toLocaleString()}</div>
              </div>
            </div>
          </div>

          {/* POI Search + List */}
          <div className="border-t border-border pt-2 flex-1 flex flex-col min-h-0">
            <h3 className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-2 flex items-center gap-1.5">
              <MapPin className="h-3 w-3" />
              POIs
              <span className="font-mono text-[10px] text-muted-foreground/60">({filteredPois.length})</span>
            </h3>
            <div className="flex gap-1 mb-2">
              <div className="relative flex-1">
                <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3 w-3 text-muted-foreground" />
                <input
                  type="text"
                  placeholder={t("poi_analysis_search_placeholder")}
                  value={poiSearch}
                  onChange={(e) => setPoiSearch(e.target.value)}
                  className="w-full h-7 rounded border border-border bg-secondary/40 pl-6 pr-2 text-xs outline-none focus:border-primary"
                />
              </div>
              <Select value={searchCategory} onValueChange={setSearchCategory}>
                <SelectTrigger className="h-7 w-[90px] text-[10px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="__all" className="text-xs">{t("poi_analysis_all_categories")}</SelectItem>
                  {allCategories.map((cat) => (
                    <SelectItem key={cat} value={cat} className="text-xs">{cat}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex-1 overflow-y-auto space-y-0.5 scrollbar-thin">
              {filteredPois.map((f, i) => {
                const p = f.properties;
                const coords = (f.geometry as GeoJSON.Point).coordinates;
                const id = p.osm_id || `${coords[0]}_${coords[1]}`;
                const isSelected = id === selectedPoiId;
                return (
                  <button
                    key={p.osm_id || i}
                    onClick={() => handlePoiSelect(f)}
                    className={`w-full text-left rounded px-2 py-1.5 text-xs transition-colors space-y-0.5 ${
                      isSelected ? "bg-primary/15 ring-1 ring-primary" : "hover:bg-secondary/60"
                    }`}
                  >
                    <div className="font-medium truncate">{p.name}</div>
                    <div className="text-[10px] text-muted-foreground truncate">{p.category} · {p.place_type}</div>
                  </button>
                );
              })}
            </div>
          </div>
        </aside>
      </div>

      {/* Floating AI button */}
      {drawnGeometry && analysis && !analysisLoading && (
        <button
          onClick={() => dispatch({ type: "SET_OPEN", payload: true })}
          className="fixed bottom-6 right-6 z-40 flex items-center gap-2 rounded-full bg-primary text-primary-foreground px-4 py-3 shadow-lg hover:bg-primary/90 transition-all duration-200"
        >
          <Bot className="h-5 w-5" />
          <span className="text-sm font-medium">AI Assistant</span>
        </button>
      )}

      {/* AI Drawer (Dialog) */}
      <Dialog open={chat.open} onOpenChange={(v) => dispatch({ type: "SET_OPEN", payload: v })}>
        <DialogContent hideCloseButton className="flex flex-col max-w-[900px] w-[calc(100%-2rem)] h-[85vh] p-0 gap-0 sm:rounded-xl">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-border px-5 py-4 shrink-0">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
                <Sparkles className="h-5 w-5 text-primary" />
              </div>
              <div>
                <DialogTitle className="text-base font-semibold">Urban Planning Assistant</DialogTitle>
                <p className="text-[11px] text-muted-foreground">
                  {analysis?.analysis.reverse_geocoding?.area_name
                    ? `Analyzing: ${analysis.analysis.reverse_geocoding.area_name}`
                    : "Ask questions about the selected analysis"}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {chat.messages.length > 0 && (
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-8 text-xs gap-1 text-muted-foreground"
                  onClick={() => {
                    dispatch({ type: "CLEAR" });
                    dispatch({ type: "SET_SUMMARY", payload: null });
                    sessionStorage.removeItem(STORAGE_KEY);
                  }}
                >
                  <Plus className="h-3.5 w-3.5" /> New Session
                </Button>
              )}
              <button
                onClick={() => dispatch({ type: "SET_OPEN", payload: false })}
                className="flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground hover:text-foreground transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* AI Summary Card (inside drawer, above conversation) */}
          {chat.summary && (
            <div className="mx-5 mt-3 rounded-lg border border-primary/30 bg-primary/5 p-3 space-y-1 shrink-0">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-primary">
                <Sparkles className="h-3.5 w-3.5" />
                AI Summary
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">{chat.summary}</p>
            </div>
          )}

          {/* Messages */}
          <ScrollArea className="flex-1 px-5 py-4" ref={chatContainerRef}>
            {chat.messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center py-12">
                <div className="flex h-14 w-14 items-center justify-center rounded-full bg-primary/10 mb-4">
                  <Bot className="h-7 w-7 text-primary" />
                </div>
                <p className="text-sm font-medium text-foreground mb-1">How can I help you?</p>
                <p className="text-xs text-muted-foreground max-w-md">
                  Ask me anything about the selected area. I can explain land use, identify dominant services,
                  highlight missing facilities, and help interpret the POI analysis.
                </p>
              </div>
            ) : (
              <div className="space-y-4 pb-2">
                {chat.messages.map((msg) => (
                  <MessageBubble
                    key={msg.id}
                    message={msg}
                    onCopy={handleCopy}
                    onRetry={handleRetry}
                    copiedId={chat.copiedMessageId}
                  />
                ))}
                <div ref={chatBottomRef} />
              </div>
            )}
          </ScrollArea>

          {/* Input area */}
          <div className="border-t border-border px-5 py-4 shrink-0 space-y-3">
            {/* Suggested questions */}
            {chat.messages.length === 0 && (
              <div className="flex gap-1.5 overflow-x-auto pb-1 scrollbar-thin">
                {suggestions.slice(0, 8).map((s) => (
                  <button
                    key={s}
                    onClick={() => {
                      dispatch({ type: "SET_INPUT", payload: s });
                      chatInputRef.current?.focus();
                    }}
                    className="shrink-0 text-[11px] px-3 py-1 rounded-full border border-border bg-secondary/30 text-muted-foreground hover:bg-secondary hover:text-foreground transition-colors whitespace-nowrap"
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}

            <div className="flex gap-2">
              <Textarea
                ref={chatInputRef}
                value={chat.input}
                onChange={(e) => {
                  dispatch({ type: "SET_INPUT", payload: e.target.value });
                  e.target.style.height = "auto";
                  e.target.style.height = `${Math.min(e.target.scrollHeight, 120)}px`;
                }}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                placeholder="Ask about this area..."
                disabled={chat.loading}
                className="min-h-[44px] max-h-[120px] text-sm resize-none"
                rows={1}
              />
              <Button
                size="icon"
                onClick={handleSend}
                disabled={!chat.input.trim() || chat.loading}
                className="shrink-0 self-end h-[44px] w-[44px]"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function Stat({ icon, label, value, mono }: { icon: React.ReactNode; label: string; value: string; mono?: boolean }) {
  return (
    <div className="rounded border border-border bg-secondary/40 px-2.5 py-2 space-y-0.5">
      <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-muted-foreground">
        {icon}
        <span>{label}</span>
      </div>
      <div className={`text-sm font-semibold ${mono ? "mono" : ""}`}>{value}</div>
    </div>
  );
}

function CompactStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex-1 min-w-0 rounded border border-border bg-secondary/40 px-2 py-1 text-center">
      <div className="text-[9px] uppercase tracking-wider text-muted-foreground truncate">{label}</div>
      <div className="text-[11px] font-semibold truncate">{value}</div>
    </div>
  );
}
