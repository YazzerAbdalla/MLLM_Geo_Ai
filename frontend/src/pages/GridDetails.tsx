import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { ArrowLeft, MapPin } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { useDash } from "@/store/dashboardStore";
import type { CellDatum } from "@/lib/api/types";
import { classHex } from "@/lib/colors";
import { useI18n } from "@/lib/i18n";
import { FEATURES } from "@/config/features";

type PoiPin = { id: string; name: string; category: string; lat: number; lng: number; class: CellDatum["class"] };

export default function GridDetails() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const { t } = useI18n();
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const cells = useDash((s) => s.cells);
  const [data, setData] = useState<{ cell: CellDatum; pois: PoiPin[] } | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [showRoads, setShowRoads] = useState(true);

  useEffect(() => {
    // Backend per-cell endpoint is not live yet (FEATURES.gridDetailsApi === false).
    // Read the cell from the cached classification result in the dashboard store.
    const cell = cells.find((c) => c.id === id);
    if (!cell) { setNotFound(true); return; }
    setData({ cell, pois: [] });
  }, [id, cells]);

  const bbox = useMemo(() => {
    if (!data) return null;
    const ring = data.cell.geometry.coordinates[0];
    const lngs = ring.map((c) => c[0]);
    const lats = ring.map((c) => c[1]);
    return [Math.min(...lngs), Math.min(...lats), Math.max(...lngs), Math.max(...lats)] as [number, number, number, number];
  }, [data]);

  useEffect(() => {
    if (!containerRef.current || mapRef.current || !data || !bbox) return;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: {
        version: 8,
        glyphs: "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",
        sources: {
          osm: { type: "raster", tiles: ["https://a.tile.openstreetmap.org/{z}/{x}/{y}.png"], tileSize: 256, attribution: "© OSM" },
        },
        layers: [{ id: "osm", type: "raster", source: "osm" }],
      },
      bounds: bbox,
      fitBoundsOptions: { padding: 80, maxZoom: 16 },
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    mapRef.current = map;

    map.on("load", () => {
      // Cell outline
      map.addSource("cell", {
        type: "geojson",
        data: { type: "Feature", properties: {}, geometry: data.cell.geometry as any },
      });
      map.addLayer({
        id: "cell-fill", type: "fill", source: "cell",
        paint: { "fill-color": classHex[data.cell.class], "fill-opacity": 0.18 },
      });
      map.addLayer({
        id: "cell-line", type: "line", source: "cell",
        paint: { "line-color": classHex[data.cell.class], "line-width": 2.5 },
      });

      // Simulated roads
      const roads = simulatedRoads(bbox);
      map.addSource("roads", { type: "geojson", data: roads });
      map.addLayer({
        id: "roads", type: "line", source: "roads",
        paint: { "line-color": "#22d3ee", "line-width": 1, "line-opacity": 0.7 },
      });

      // POI pins
      data.pois.forEach((p) => {
        const el = document.createElement("div");
        el.style.cssText = `width:22px;height:22px;border-radius:50%;background:${classHex[p.class]};border:2px solid hsl(var(--background));box-shadow:0 2px 6px rgba(0,0,0,.4);display:flex;align-items:center;justify-content:center;color:#000;font-size:11px;font-weight:700;cursor:pointer`;
        el.textContent = p.category[0]?.toUpperCase() ?? "•";
        const popup = new maplibregl.Popup({ offset: 14, closeButton: false }).setHTML(
          `<div style="font-size:12px"><div style="font-weight:600">${p.name}</div><div style="opacity:.7;font-family:monospace;font-size:10px">${p.category}</div></div>`
        );
        new maplibregl.Marker({ element: el }).setLngLat([p.lng, p.lat]).setPopup(popup).addTo(map);
      });
    });

    return () => { map.remove(); mapRef.current = null; };
  }, [data, bbox]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;
    if (map.getLayer("roads")) map.setLayoutProperty("roads", "visibility", showRoads ? "visible" : "none");
  }, [showRoads]);

  if (notFound) {
    return (
      <div className="h-screen flex flex-col items-center justify-center gap-3 bg-background text-foreground">
        <p className="text-muted-foreground">{t("cell_not_found")}: <span className="mono">{id}</span></p>
        <Button asChild variant="outline" size="sm"><Link to="/"><ArrowLeft className="h-4 w-4" /> {t("back_to_dashboard")}</Link></Button>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-background text-foreground">
      <header className="h-12 border-b border-border flex items-center px-3 gap-3 bg-card">
        <Button variant="ghost" size="sm" onClick={() => navigate(-1)}><ArrowLeft className="h-4 w-4" /> {t("back_to_dashboard")}</Button>
        <h1 className="text-sm font-semibold flex-1">
          {t("grid_details")} · <span className="mono text-xs text-muted-foreground">{id}</span>
        </h1>
        {data && (
          <div className="flex items-center gap-2 text-xs">
            <span className="h-3 w-3 rounded-sm" style={{ backgroundColor: classHex[data.cell.class] }} />
            <span className="font-semibold">{data.cell.class}</span>
          </div>
        )}
      </header>

      <div className="flex-1 flex overflow-hidden">
        <aside className="w-[320px] shrink-0 border-r border-border bg-card overflow-y-auto p-4 space-y-4">
          {!FEATURES.gridDetailsApi && (
            <div className="rounded border border-dashed border-border bg-secondary/30 px-3 py-2 text-[11px] text-muted-foreground">
              Per-cell detail endpoint coming soon — showing data from the latest classification result.
            </div>
          )}
          {!data ? (
            <p className="text-sm text-muted-foreground">{t("loading")}</p>
          ) : (
            <>
              <Stat label={t("dominant_class")} value={data.cell.class} />
              <Stat label={t("confidence")} value={`${(data.cell.confidence * 100).toFixed(1)}%`} />
              <Stat label="road_density" value={`${data.cell.road_density.toFixed(2)} km/km²`} mono />
              <Stat label="node_count" value={String(data.cell.node_count)} mono />
              <Stat label="degree_centrality" value={data.cell.degree_centrality.toFixed(3)} mono />

              <div className="flex items-center justify-between text-sm pt-2 border-t border-border">
                <span>{t("show_roads")}</span>
                <Switch checked={showRoads} onCheckedChange={setShowRoads} />
              </div>

              {data.cell.top5_poi.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold mb-2 flex items-center gap-1.5">
                    <MapPin className="h-3.5 w-3.5" /> Top POI categories
                  </h4>
                  <ul className="space-y-1.5">
                    {data.cell.top5_poi.map((p, i) => (
                      <li key={i} className="text-xs flex items-center gap-2 rounded border border-border px-2 py-1.5 bg-secondary/40">
                        <span className="mono text-[10px] text-muted-foreground">{i + 1}.</span>
                        <span className="flex-1 truncate mono">{p}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}
        </aside>
        <main className="flex-1 relative">
          <div ref={containerRef} className="absolute inset-0" />
        </main>
      </div>
    </div>
  );
}

function Stat({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="rounded border border-border bg-secondary/40 px-3 py-2">
      <div className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
      <div className={`text-sm font-semibold ${mono ? "mono" : ""}`}>{value}</div>
    </div>
  );
}

/** Deterministic fake road network for visual context only. */
function simulatedRoads(bbox: [number, number, number, number]) {
  const [w, s, e, n] = bbox;
  const lines: number[][][] = [];
  for (let i = 1; i < 5; i++) {
    const lat = s + ((n - s) * i) / 5;
    lines.push([[w, lat], [e, lat]]);
    const lng = w + ((e - w) * i) / 5;
    lines.push([[lng, s], [lng, n]]);
  }
  return {
    type: "FeatureCollection" as const,
    features: lines.map((coords) => ({
      type: "Feature" as const,
      properties: {},
      geometry: { type: "LineString" as const, coordinates: coords },
    })),
  };
}