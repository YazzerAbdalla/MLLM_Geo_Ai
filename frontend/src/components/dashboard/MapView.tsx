import { useEffect, useMemo, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { useNavigate } from "react-router-dom";
import { useDash } from "@/store/dashboardStore";
import { cairoBbox } from "@/lib/api/mockClient";
import { useGraphTopology } from "@/hooks/api/useGraphTopology";
import { usePoiHeatmap } from "@/hooks/api/usePoiHeatmap";
import { classHex, opacityFromConfidence } from "@/lib/colors";
import { createSmallDefaultArea } from "@/lib/geoUtils";
import type { CellDatum } from "@/lib/api/types";

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
    sat: {
      type: "raster",
      tiles: [
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
      ],
      tileSize: 256,
      attribution: "Tiles © Esri",
      maxzoom: 19,
    },
  },
  layers: [
    { id: "osm-bg", type: "raster", source: "osm" },
    { id: "sat-bg", type: "raster", source: "sat", layout: { visibility: "none" } },
  ],
};

interface MapViewProps {
  jobId?: string | null;
  gridId?: string | null;
  cells?: CellDatum[];
}

export function MapView({ jobId, gridId: propGridId, cells: propCells }: MapViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const navigate = useNavigate();

  const [mapReady, setMapReady] = useState(false);

  const storeCells = useDash((s) => s.cells);
  const layers = useDash((s) => s.layers);
  const loaded = useDash((s) => s.loaded);
  const selectedCellId = useDash((s) => s.selectedCellId);
  const setSelectedCellId = useDash((s) => s.setSelectedCellId);
  const drawnGeometry = useDash((s) => s.drawnGeometry);
  const setDrawnGeometry = useDash((s) => s.setDrawnGeometry);
  const drawMode = useDash((s) => s.drawMode);
  const setDrawMode = useDash((s) => s.setDrawMode);
  const searchLocation = useDash((s) => s.searchLocation);
  const storeGridId = useDash((s) => s.gridId);
  const matchedCellIds = useDash((s) => s.matchedCellIds);
  const queryResults = useDash((s) => s.queryResults);

  // Use passed props when available, fall back to store values
  const effectiveCells = propCells ?? storeCells;
  const effectiveGridId = propGridId ?? storeGridId;
  const graphQ = useGraphTopology(effectiveGridId, { enabled: !!effectiveGridId && layers.graph });
  const poiHeatmapQ = usePoiHeatmap(effectiveGridId, {
    enabled: !!effectiveGridId && layers.poi,
  });

  // Refs so the mount-only click handlers always read latest values
  const cellsRef = useRef(effectiveCells);
  cellsRef.current = effectiveCells;
  const jobIdRef = useRef(jobId);
  jobIdRef.current = jobId;
  const gridIdRef = useRef(propGridId);
  gridIdRef.current = propGridId;

  // FeatureCollection for current classified cells
  const cellsFC = useMemo(() => {
    const features = effectiveCells.map((c) => {
      const fill = classHex[c.class as keyof typeof classHex] || classHex.Residential;
      const opacity = opacityFromConfidence(c.confidence);
      return {
        type: "Feature" as const,
        id: c.id,
        properties: { id: c.id, class: c.class, confidence: c.confidence, fill, opacity },
        geometry: c.geometry,
      };
    });
    if (import.meta.env.DEV) {
      console.log("[MapView] cellsFC features:", features.length);
      features.forEach((f) => console.log("  id:", f.id, "class:", f.properties.class, "fill:", f.properties.fill));
    }
    return { type: "FeatureCollection" as const, features };
  }, [effectiveCells]);

  // FeatureCollection for query-matched cells (subset of cellsFC)
  const matchedFC = useMemo(() => {
    const ids = new Set(matchedCellIds);
    const features = cellsFC.features.filter((f) => ids.has(f.properties.id as string));
    return { type: "FeatureCollection" as const, features };
  }, [cellsFC, matchedCellIds]);

  // Split backend graph-topology FeatureCollection into nodes + edges
  const graphSplit = useMemo(() => {
    const empty = { type: "FeatureCollection" as const, features: [] };
    const fc = graphQ.data;
    if (!fc) return { nodes: empty, edges: empty };
    const nodes: any = { type: "FeatureCollection", features: [] };
    const edges: any = { type: "FeatureCollection", features: [] };
    for (const f of fc.features as any[]) {
      const t = f.geometry?.type;
      if (t === "Point") nodes.features.push(f);
      else if (t === "LineString" || t === "MultiLineString") edges.features.push(f);
    }
    return { nodes, edges };
  }, [graphQ.data]);

  // Init map
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
      // BBox outline
      map.addSource("bbox", {
        type: "geojson",
        data: {
          type: "Feature",
          properties: {},
          geometry: {
            type: "LineString",
            coordinates: [
              [cairoBbox.west, cairoBbox.south],
              [cairoBbox.east, cairoBbox.south],
              [cairoBbox.east, cairoBbox.north],
              [cairoBbox.west, cairoBbox.north],
              [cairoBbox.west, cairoBbox.south],
            ],
          },
        },
      });
      map.addLayer({
        id: "bbox-line",
        type: "line",
        source: "bbox",
        paint: { "line-color": "#22d3ee", "line-width": 1.5, "line-dasharray": [3, 2] },
      });

      // POI Heatmap
      if (!map.getSource("poi-heatmap-source")) {
        map.addSource("poi-heatmap-source", {
          type: "geojson",
          data: { type: "FeatureCollection", features: [] },
        });
      }
      if (!map.getLayer("poi-heatmap-layer")) {
        map.addLayer(
          {
            id: "poi-heatmap-layer",
            type: "heatmap",
            source: "poi-heatmap-source",
            layout: { visibility: "none" },
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
          },
        );
      }
      if (!map.getLayer("poi-heatmap-debug")) {
        map.addLayer({
          id: "poi-heatmap-debug",
          type: "circle",
          source: "poi-heatmap-source",
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
      }

      map.on("click", "poi-heatmap-debug", (e) => {
        const f = e.features?.[0];
        if (!f) return;
        const p = f.properties || {};
        const coords = (f.geometry as GeoJSON.Point).coordinates;
        const html = `
          <div style="font-size:12px;line-height:1.6;color:#000;max-width:260px">
            <div style="font-weight:700;font-size:13px;margin-bottom:4px">${p.name || "—"}</div>
            <table style="width:100%;border-collapse:collapse">
              <tr><td style="opacity:.6;padding-right:8px;white-space:nowrap">Category</td><td style="font-family:monospace">${p.category || "—"}</td></tr>
              <tr><td style="opacity:.6;padding-right:8px;white-space:nowrap">Place Type</td><td style="font-family:monospace">${p.place_type || "—"}</td></tr>
              <tr><td style="opacity:.6;padding-right:8px;white-space:nowrap">OSM ID</td><td style="font-family:monospace">${p.osm_id || "—"}</td></tr>
              <tr><td style="opacity:.6;padding-right:8px;white-space:nowrap">Label</td><td style="font-family:monospace">${p.label || "—"}</td></tr>
              <tr><td style="opacity:.6;padding-right:8px;white-space:nowrap">Coords</td><td style="font-family:monospace">${coords[1].toFixed(5)}, ${coords[0].toFixed(5)}</td></tr>
            </table>
          </div>
        `;
        new maplibregl.Popup({ offset: 14, closeButton: true, maxWidth: "300px" })
          .setLngLat(coords as [number, number])
          .setHTML(html)
          .addTo(map);
      });

      map.on("mouseenter", "poi-heatmap-debug", () => (map.getCanvas().style.cursor = "pointer"));
      map.on("mouseleave", "poi-heatmap-debug", () => (map.getCanvas().style.cursor = ""));

      // Classified cells
      map.addSource("cells", { type: "geojson", data: cellsFC });
      map.addLayer({
        id: "cells-fill",
        type: "fill",
        source: "cells",
        paint: {
          "fill-color": ["get", "fill"],
          "fill-opacity": ["get", "opacity"],
        },
      });
      map.addLayer({
        id: "cells-stroke",
        type: "line",
        source: "cells",
        paint: {
          "line-color": "#0f172a",
          "line-width": ["case", ["boolean", ["feature-state", "selected"], false], 2.5, 0.4],
        },
      });

      // Graph topology
      map.addSource("graph-edges", { type: "geojson", data: graphSplit.edges });
      map.addLayer({
        id: "graph-edges",
        type: "line",
        source: "graph-edges",
        paint: { "line-color": "#22d3ee", "line-width": 0.6, "line-opacity": 0.55 },
        layout: { visibility: "none" },
      });
      map.addSource("graph-nodes", { type: "geojson", data: graphSplit.nodes });
      map.addLayer({
        id: "graph-nodes",
        type: "circle",
        source: "graph-nodes",
        paint: {
          "circle-radius": 1.6,
          "circle-color": "#22d3ee",
          "circle-stroke-color": "#0f172a",
          "circle-stroke-width": 0.4,
        },
        layout: { visibility: "none" },
      });

      // Drawn custom area
      map.addSource("drawn", {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
      });
      map.addLayer({
        id: "drawn-fill",
        type: "fill",
        source: "drawn",
        paint: { "fill-color": "#22d3ee", "fill-opacity": 0.12 },
      });
      map.addLayer({
        id: "drawn-line",
        type: "line",
        source: "drawn",
        paint: { "line-color": "#22d3ee", "line-width": 2 },
      });

      // Query-matched cells highlight
      map.addSource("matched-cells", {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
      });
      map.addLayer({
        id: "matched-cells-highlight",
        type: "line",
        source: "matched-cells",
        paint: {
          "line-color": "#22d3ee",
          "line-width": 3,
          "line-opacity": 0.9,
        },
      });
      map.addLayer({
        id: "matched-cells-glow",
        type: "line",
        source: "matched-cells",
        paint: {
          "line-color": "#22d3ee",
          "line-width": 7,
          "line-opacity": 0.25,
        },
      });

      // Click handler for matched cells popup
      const popup = new maplibregl.Popup({ offset: 14, closeButton: true, maxWidth: "320px" });
      map.on("click", "cells-fill", (e) => {
        if (useDash.getState().drawMode) return;
        const f = e.features?.[0];
        if (!f) return;
        const cellId = String(f.properties?.id ?? "");
        if (!useDash.getState().matchedCellIds.includes(cellId)) return;
        const matched = useDash.getState().queryResults?.matched_cells.find((c) => c.cell_id === cellId);
        if (!matched) return;
        const html = `
          <div style="font-size:12px;line-height:1.6;color:#000;max-width:300px">
            <div style="font-weight:700;font-size:13px;margin-bottom:4px">Cell ${matched.cell_id}</div>
            <table style="width:100%;border-collapse:collapse">
              <tr><td style="opacity:.6;padding-right:8px;white-space:nowrap">Dominant Class</td><td style="font-family:monospace">${matched.dominant_class}</td></tr>
              <tr><td style="opacity:.6;padding-right:8px;white-space:nowrap">Confidence</td><td style="font-family:monospace">${(matched.confidence * 100).toFixed(0)}%</td></tr>
              <tr><td style="opacity:.6;padding-right:8px;white-space:nowrap">Road Density</td><td style="font-family:monospace">${matched.road_density.toFixed(2)} km/km²</td></tr>
              <tr><td style="opacity:.6;padding-right:8px;white-space:nowrap">Top Categories</td><td style="font-family:monospace">${matched.poi_categories.slice(0, 3).join(", ") || "—"}</td></tr>
              <tr><td style="opacity:.6;padding-right:8px;white-space:nowrap">Centroid</td><td style="font-family:monospace">${matched.centroid[1].toFixed(5)}, ${matched.centroid[0].toFixed(5)}</td></tr>
            </table>
          </div>`;
        popup.setLngLat(e.lngLat).setHTML(html).addTo(map);
      });

      setMapReady(true);

      // Click handler
      map.on("click", "cells-fill", (e) => {
        if (useDash.getState().drawMode) return;
        const f = e.features?.[0];
        if (f) {
          const id = f.properties?.id as string;
          setSelectedCellId(id);
          // double-click navigates to details page
        }
      });
      map.on("dblclick", "cells-fill", (e) => {
        const f = e.features?.[0];
        if (!f) return;
        e.preventDefault();
        if (import.meta.env.DEV) {
          console.log("[MapView] double-click feature properties:", f.properties);
        }
        const cellId = String(f.properties?.id ?? f.properties?.cell_id ?? "");
        const cell = cellsRef.current.find((c) => c.id === cellId);
        const jId = jobIdRef.current ?? useDash.getState().classifyJobId;
        if (jId && cellId) {
          navigate(`/classification/${jId}/cell/${cellId}`);
        }
      });
      map.on("mouseenter", "cells-fill", () => (map.getCanvas().style.cursor = "pointer"));
      map.on("mouseleave", "cells-fill", () => (map.getCanvas().style.cursor = ""));
    });

    return () => {
      map.remove();
      mapRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Update cell data
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;
    const src = map.getSource("cells") as maplibregl.GeoJSONSource | undefined;
    if (src) {
      src.setData(cellsFC as any);
      if (import.meta.env.DEV) {
        console.log("[MapView] setData on 'cells' source — features:", cellsFC.features.length);
        // Log first feature's properties to verify fill value
        if (cellsFC.features.length > 0) {
          console.log("  first feature props:", cellsFC.features[0].properties);
        }
      }
    }
  }, [cellsFC]);

  // Update graph data when backend returns it
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;
    (map.getSource("graph-edges") as maplibregl.GeoJSONSource | undefined)?.setData(graphSplit.edges as any);
    (map.getSource("graph-nodes") as maplibregl.GeoJSONSource | undefined)?.setData(graphSplit.nodes as any);
  }, [graphSplit]);

  // POI Heatmap data sync
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;

    const data = poiHeatmapQ.data;
    if (!data) return;

    if (data.type !== "FeatureCollection" || !Array.isArray(data.features)) {
      if (import.meta.env.DEV) console.warn("[MapView] poi-heatmap: invalid GeoJSON");
      return;
    }

    const src = map.getSource("poi-heatmap-source") as maplibregl.GeoJSONSource;
    if (!src) return;

    if (data.features.length === 0) {
      useDash.getState().setPoiHeatmapEmpty(true);
      map.setLayoutProperty("poi-heatmap-layer", "visibility", "none");
      return;
    }

    useDash.getState().setPoiHeatmapEmpty(false);
    src.setData(data as any);

    map.setLayoutProperty("poi-heatmap-layer", "visibility", "visible");

    if (import.meta.env.DEV) {
      const srcCheck = map.getSource("poi-heatmap-source") as maplibregl.GeoJSONSource;
      console.log(`[MapView] poi-heatmap loaded — ${data.features.length} features, source exists: ${!!srcCheck}, layer visible: ${map.getLayoutProperty("poi-heatmap-layer", "visibility")}`);
      data.features.forEach((f, i) => {
        console.log(`  [${i}]`, f.geometry?.coordinates, f.properties?.name);
      });
    }
  }, [poiHeatmapQ.data, mapReady]);

  // Compute active preview geometry (priority: drawnGeometry, fallback: searchLocation default area)
  const displayGeometry = useMemo(() => {
    if (drawnGeometry) return drawnGeometry;
    if (searchLocation) return createSmallDefaultArea(searchLocation.lng, searchLocation.lat);
    return null;
  }, [drawnGeometry, searchLocation]);

  // Sync drawn-area source
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;
    const src = map.getSource("drawn") as maplibregl.GeoJSONSource | undefined;
    src?.setData({
      type: "FeatureCollection",
      features: displayGeometry
        ? [{ type: "Feature", properties: {}, geometry: displayGeometry as any }]
        : [],
    } as any);
  }, [displayGeometry]);

  // Center and zoom map when searchLocation changes
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !searchLocation) return;
    map.flyTo({
      center: [searchLocation.lng, searchLocation.lat],
      zoom: 13,
      essential: true
    });
  }, [searchLocation]);

  // Rectangle drawing mode (native MapLibre, no extra deps)
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const canvas = map.getCanvas();
    if (!drawMode) {
      canvas.style.cursor = "";
      return;
    }
    canvas.style.cursor = "crosshair";
    map.dragPan.disable();
    map.boxZoom.disable();

    let start: maplibregl.LngLat | null = null;

    const onDown = (e: maplibregl.MapMouseEvent) => {
      start = e.lngLat;
    };
    const onMove = (e: maplibregl.MapMouseEvent) => {
      if (!start) return;
      const ring = rectRing(start, e.lngLat);
      const src = map.getSource("drawn") as maplibregl.GeoJSONSource | undefined;
      src?.setData({
        type: "FeatureCollection",
        features: [{
          type: "Feature", properties: {},
          geometry: { type: "Polygon", coordinates: [ring] },
        }],
      } as any);
    };
    const onUp = (e: maplibregl.MapMouseEvent) => {
      if (!start) return;
      const ring = rectRing(start, e.lngLat);
      setDrawnGeometry({ type: "Polygon", coordinates: [ring] });
      setDrawMode(false);
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
  }, [drawMode, setDrawnGeometry, setDrawMode]);

  // Layer visibility
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;
    map.setLayoutProperty("cells-fill", "visibility", layers.classification ? "visible" : "none");
    map.setLayoutProperty("cells-stroke", "visibility", layers.classification ? "visible" : "none");
    map.setLayoutProperty("graph-edges", "visibility", layers.graph ? "visible" : "none");
    map.setLayoutProperty("graph-nodes", "visibility", layers.graph ? "visible" : "none");
    map.setLayoutProperty("sat-bg", "visibility", layers.satellite ? "visible" : "none");
    map.setLayoutProperty("osm-bg", "visibility", layers.satellite ? "none" : "visible");
    if (map.getLayer("poi-heatmap-layer")) {
      const vis = layers.poi && !useDash.getState().poiHeatmapEmpty ? "visible" : "none";
      map.setLayoutProperty("poi-heatmap-layer", "visibility", vis);
      if (import.meta.env.DEV && vis === "visible") {
        console.log("[MapView] poi-heatmap visibility: visible");
      }
    }
    if (map.getLayer("poi-heatmap-debug")) {
      const vis = layers.poi && !useDash.getState().poiHeatmapEmpty ? "visible" : "none";
      map.setLayoutProperty("poi-heatmap-debug", "visibility", vis);
    }
  }, [layers, loaded]);

  // Selection feature-state
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;
    cellsFC.features.forEach((f) => {
      map.setFeatureState({ source: "cells", id: f.id as string }, { selected: f.id === selectedCellId });
    });
  }, [selectedCellId, cellsFC]);

  // Update matched-cells source data
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;
    const src = map.getSource("matched-cells") as maplibregl.GeoJSONSource | undefined;
    if (src) src.setData(matchedFC as any);
    const ids = new Set(matchedCellIds);
    const matched = cellsFC.features.filter((f) => ids.has(f.properties.id as string));
    if (matched.length > 1) {
      const bounds = new maplibregl.LngLatBounds();
      matched.forEach((f) => {
        const coords = (f.geometry as GeoJSON.Polygon).coordinates[0];
        coords.forEach((c) => bounds.extend(c as [number, number]));
      });
      map.fitBounds(bounds, { padding: 60, maxZoom: 15, duration: 800 });
    } else if (matched.length === 1) {
      const geom = matched[0].geometry as GeoJSON.Polygon;
      const coords = geom.coordinates[0];
      let x = 0, y = 0;
      for (const [lng, lat] of coords) { x += lng; y += lat; }
      const cx = x / coords.length;
      const cy = y / coords.length;
      map.flyTo({ center: [cx, cy], zoom: 14, duration: 800 });
    }
  }, [matchedFC, matchedCellIds, cellsFC]);

  return <div ref={containerRef} className="absolute inset-0" aria-label="Map" />;
}

function rectRing(a: maplibregl.LngLat, b: maplibregl.LngLat): number[][] {
  const w = Math.min(a.lng, b.lng), e = Math.max(a.lng, b.lng);
  const s = Math.min(a.lat, b.lat), n = Math.max(a.lat, b.lat);
  return [[w, s], [e, s], [e, n], [w, n], [w, s]];
}