import { useState, useEffect, useMemo, useRef } from "react";
import { Link, useParams } from "react-router-dom";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { ArrowLeft, ImageOff, MapPin } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useCell } from "@/hooks/api/useCell";
import { usePois } from "@/hooks/api/usePois";
import { classHex } from "@/lib/colors";
import { useI18n } from "@/lib/i18n";
import { buildThumbnailUrl } from "@/lib/gridUtils";
import type { LandUseClass } from "@/lib/api/types";
import type { PoiItem } from "@/api/types";
import { pointInPolygon } from "@/lib/api/mockClient";

export default function CellDetailsPage() {
  const { jobId = "", cellId = "" } = useParams();
  const { t } = useI18n();
  const { cell, isLoading, isError } = useCell(jobId, cellId);
  const [thumbState, setThumbState] = useState<"loading" | "loaded" | "error">("loading");

  useEffect(() => {
    setThumbState("loading");
  }, [cell?.id]);

  const gridId = cell?.gridId ?? null;

  if (import.meta.env.DEV) {
    console.log("[CellDetailsPage] cellId:", cellId, "gridId:", gridId, "satellite_thumb:", cell?.satellite_thumb);
  }

  const poisQ = usePois(gridId);

  const cellPois = useMemo(() => {
    if (!cell || !poisQ.data) {
      if (import.meta.env.DEV) {
        console.log("[CellDetailsPage] skip filter - cell:", !!cell, "poisQ.data:", !!poisQ.data, "poisQ.data.length:", poisQ.data?.length);
      }
      return [];
    }
    const ring = cell.geometry.coordinates[0];
    if (import.meta.env.DEV) {
      console.log("[CellDetailsPage] filtering", poisQ.data.length, "POIs against ring of", ring.length, "vertices");
      console.log("  ring sample:", ring[0], ring[1], ring[ring.length-1]);
      console.log("  sample poi:", poisQ.data[0]);
    }
    const filtered = poisQ.data.filter((poi: PoiItem) => {
      const inside = pointInPolygon([poi.lng, poi.lat], ring);
      if (import.meta.env.DEV && inside) {
        console.log("  POI inside:", poi.name, poi.lat, poi.lng);
      }
      return inside;
    });
    if (import.meta.env.DEV) {
      console.log("[CellDetailsPage] filtered POIs:", filtered.length, "/", poisQ.data.length);
    }
    return filtered;
  }, [cell, poisQ.data]);

  const categoryCounts = useMemo(() => {
    return cellPois.reduce((acc, p) => {
      acc[p.category] = (acc[p.category] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
  }, [cellPois]);

  if (isLoading || poisQ.isLoading) {
    return (
      <div className="h-screen flex items-center justify-center bg-background text-foreground">
        <p className="text-muted-foreground">{t("loading")}</p>
      </div>
    );
  }

  if (isError || !cell) {
    return (
      <div className="h-screen flex flex-col items-center justify-center gap-3 bg-background text-foreground">
        <p className="text-muted-foreground">{t("cell_not_found_in_result")}: <span className="mono">{cellId}</span></p>
        <Button asChild variant="outline" size="sm">
          <Link to={`/classification/${jobId}`}><ArrowLeft className="h-4 w-4" /> {t("back_to_classification")}</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-background text-foreground">
      <header className="h-12 border-b border-border flex items-center px-3 gap-3 bg-card">
        <Button asChild variant="ghost" size="sm">
          <Link to={`/classification/${jobId}`}><ArrowLeft className="h-4 w-4" /> {t("back_to_classification")}</Link>
        </Button>
        <h1 className="text-sm font-semibold flex-1">
          {t("cell_details_title")} · <span className="mono text-xs text-muted-foreground">#{cellId}</span>
        </h1>
        <div className="flex items-center gap-2 text-xs">
          <span className="h-3 w-3 rounded-sm" style={{ backgroundColor: classHex[cell.class] }} />
          <span className="font-semibold">{cell.class}</span>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        <aside className="w-[360px] shrink-0 border-r border-border bg-card overflow-y-auto p-4 space-y-4">
          <div className="space-y-1">
            <div className="mono text-xs text-muted-foreground">#{cellId}</div>
            <div className="font-semibold text-lg">{cell.class}</div>
          </div>

          <div>
            <h4 className="text-xs font-semibold mb-1.5">{t("satellite")}</h4>
            {cell.satellite_thumb ? (
              <div className="relative w-full rounded border border-border overflow-hidden bg-secondary/40 aspect-video">
                {thumbState === "loading" && <div className="absolute inset-0 animate-pulse bg-muted" />}
                {thumbState === "error" ? (
                  <div className="absolute inset-0 flex items-center justify-center text-muted-foreground">
                    <ImageOff className="h-5 w-5" />
                  </div>
                ) : (
                  <img
                    src={buildThumbnailUrl(cell.satellite_thumb)}
                    alt="satellite"
                    className={`w-full h-full object-cover ${thumbState === "loading" ? "opacity-0" : "opacity-100"}`}
                    onLoad={() => setThumbState("loaded")}
                    onError={() => setThumbState("error")}
                  />
                )}
              </div>
            ) : (
              <div className="w-full rounded border border-border bg-secondary/40 p-4 text-center text-xs text-muted-foreground">
                {t("thumbnail_empty")}
              </div>
            )}
          </div>

          <div>
            <h4 className="text-xs font-semibold mb-1.5">{t("confidence")}</h4>
            <div className="h-2 bg-secondary rounded overflow-hidden">
              <div className="h-full rounded" style={{ width: `${cell.confidence * 100}%`, backgroundColor: classHex[cell.class] }} />
            </div>
            <p className="mono text-xs text-muted-foreground mt-1">{(cell.confidence * 100).toFixed(1)}%</p>
          </div>

          <div className="space-y-1.5">
            <h4 className="text-xs font-semibold">Class breakdown</h4>
            {(["Residential", "Commercial", "Industrial"] as LandUseClass[]).map((k) => {
              const v = cell.confidences[k];
              return (
                <div key={k} className="text-xs">
                  <div className="flex justify-between mb-0.5"><span>{k}</span><span className="mono text-muted-foreground">{(v * 100).toFixed(1)}%</span></div>
                  <div className="h-1.5 bg-secondary rounded overflow-hidden"><div className="h-full" style={{ width: `${v * 100}%`, backgroundColor: classHex[k] }} /></div>
                </div>
              );
            })}
          </div>

          {Object.keys(categoryCounts).length > 0 && (
            <div>
              <h4 className="text-xs font-semibold mb-1.5 flex items-center gap-1.5">
                <MapPin className="h-3.5 w-3.5" /> POI categories
              </h4>
              <div className="flex flex-wrap gap-1.5">
                {Object.entries(categoryCounts)
                  .sort(([, a], [, b]) => b - a)
                  .map(([cat, count]) => (
                    <span key={cat} className="inline-flex items-center gap-1 rounded-full border border-border bg-secondary/50 px-2.5 py-1 text-[11px] mono">
                      {cat} <span className="text-muted-foreground">({count})</span>
                    </span>
                  ))}
              </div>
            </div>
          )}

          {cellPois.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold mb-1.5">POIs ({cellPois.length})</h4>
              <div className="space-y-1.5">
                {cellPois.map((poi, i) => (
                  <div key={i} className="rounded border border-border bg-secondary/40 p-2 text-xs space-y-0.5">
                    <div className="font-medium mono text-sm">{poi.name}</div>
                    <div className="text-[10px] text-muted-foreground">{poi.category}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div>
            <h4 className="text-xs font-semibold mb-1.5">Graph metrics</h4>
            <div className="grid grid-cols-2 gap-1.5 text-xs">
              <Metric label="road_density" value={cell.road_density.toFixed(2)} />
              <Metric label="node_count" value={cell.node_count.toString()} />
              <Metric label="degree_centrality" value={cell.degree_centrality.toFixed(3)} />
              <Metric label="clustering_coeff" value={cell.clustering_coeff.toFixed(3)} />
              <Metric label="total_road_length_m" value={cell.total_road_length_m.toString()} />
            </div>
          </div>
        </aside>

        <main className="flex-1 relative">
          <CellMap
            geometry={cell.geometry}
            classColor={classHex[cell.class]}
            pois={cellPois}
          />
        </main>
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded bg-secondary/50 px-2 py-1.5 border border-border">
      <div className="text-[9px] uppercase mono text-muted-foreground tracking-wide">{label}</div>
      <div className="mono text-sm">{value}</div>
    </div>
  );
}

function CellMap({
  geometry,
  classColor,
  pois,
}: {
  geometry: { type: "Polygon"; coordinates: number[][][] };
  classColor: string;
  pois: PoiItem[];
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);

  const bbox = useMemo(() => {
    const ring = geometry.coordinates[0];
    const lngs = ring.map((c) => c[0]);
    const lats = ring.map((c) => c[1]);
    return [Math.min(...lngs), Math.min(...lats), Math.max(...lngs), Math.max(...lats)] as [number, number, number, number];
  }, [geometry]);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
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
      map.addSource("cell", { type: "geojson", data: { type: "Feature", properties: {}, geometry: geometry as unknown as GeoJSON.Geometry } });
      map.addLayer({ id: "cell-fill", type: "fill", source: "cell", paint: { "fill-color": classColor, "fill-opacity": 0.18 } });
      map.addLayer({ id: "cell-line", type: "line", source: "cell", paint: { "line-color": classColor, "line-width": 2.5 } });

      pois.forEach((poi) => {
        const el = document.createElement("div");
        el.style.cssText = `width:18px;height:18px;border-radius:50%;background:#22d3ee;border:2px solid hsl(var(--background));box-shadow:0 2px 6px rgba(0,0,0,.4);cursor:pointer`;
        el.title = poi.name;
        const popup = new maplibregl.Popup({ offset: 14, closeButton: false }).setHTML(
          `<div style="font-size:12px;color:#000"><div style="font-weight:600">${poi.name}</div><div style="opacity:.7;font-family:monospace;font-size:10px">${poi.category}</div></div>`
        );
        new maplibregl.Marker({ element: el }).setLngLat([poi.lng, poi.lat]).setPopup(popup).addTo(map);
      });
    });
    return () => { map.remove(); mapRef.current = null; };
  }, [bbox, geometry, classColor, pois]);

  return <div ref={containerRef} className="absolute inset-0" />;
}
