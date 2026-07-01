import { useState, useMemo } from "react";
import { Search, Square, Play, AlertTriangle, Lock, Pencil, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { useDash } from "@/store/dashboardStore";
import { useI18n } from "@/lib/i18n";
import { estimateCells } from "@/lib/api/mockClient";
import { cn } from "@/lib/utils";
import type { FusionMethod, Modality } from "@/lib/api/types";
import { AiQueryPanel } from "./AiQueryPanel";
import { getBboxFromGeometry, createSmallDefaultArea } from "@/lib/geoUtils";

/**
 * Predefined search suggestions for common city locations to support offline lookup.
 */
const SUGGESTIONS = [
  { label: "Cairo, Egypt", lat: 30.0444, lng: 31.2357 },
  { label: "New Cairo, Egypt", lat: 30.0263, lng: 31.4913 },
  { label: "Giza, Egypt", lat: 30.0131, lng: 31.2089 },
];

const PRESETS: Record<string, Record<Modality, boolean>> = {
  poi_only: { poi: true, image: false, graph: false, text: false },
  poi_image: { poi: true, image: true, graph: false, text: false },
  poi_image_graph: { poi: true, image: true, graph: true, text: false },
  all: { poi: true, image: true, graph: true, text: true },
};

interface Props { onLoadArea: () => void; onClassify: () => void; onCancel: () => void; }

export function Sidebar({ onLoadArea, onClassify, onCancel }: Props) {
  const { t } = useI18n();
  const [search, setSearch] = useState("");
  const [suggestions, setSuggestions] = useState<{ label: string; lat: number; lng: number }[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [loadingSearch, setLoadingSearch] = useState(false);

  const {
    gridSize,
    setGridSize,
    modalities,
    setModality,
    modelType,
    setModelType,
    fusion,
    setFusion,
    loaded,
    classifying,
    layers,
    setLayer,
    drawMode,
    setDrawMode,
    drawnGeometry,
    setDrawnGeometry,
    searchLocation,
    setSearchLocation,
    poiHeatmapEmpty,
  } = useDash();

  /**
   * Geocodes the search query via OpenStreetMap Nominatim with local fallback.
   *
   * @param query Search text entered by user
   */
  const triggerGeocode = async (query: string) => {
    if (!query.trim()) return;
    setLoadingSearch(true);
    try {
      const res = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=5`);
      const data = await res.json();
      if (Array.isArray(data)) {
        const results = data.map((item: { display_name: string; lat: string; lon: string }) => ({
          label: item.display_name,
          lat: parseFloat(item.lat),
          lng: parseFloat(item.lon),
        }));
        setSuggestions(results);
        setShowSuggestions(true);
      }
    } catch (err) {
      console.error("Geocoding failed, falling back to local presets", err);
      // Fallback to presets matching query
      const matches = SUGGESTIONS.filter(s =>
        s.label.toLowerCase().includes(query.toLowerCase())
      );
      setSuggestions(matches);
      setShowSuggestions(true);
    } finally {
      setLoadingSearch(false);
    }
  };

  /**
   * Selects a search suggestion.
   *
   * @param s Selected suggestion object
   */
  const selectSuggestion = (s: { label: string; lat: number; lng: number }) => {
    setSearchLocation(s);
    setSearch(s.label);
    setShowSuggestions(false);
  };

  // Compute active geometry for preview and cell count estimation
  const activeGeometry = useMemo(() => {
    if (drawnGeometry) return drawnGeometry;
    if (searchLocation) return createSmallDefaultArea(searchLocation.lng, searchLocation.lat);
    return null;
  }, [drawnGeometry, searchLocation]);

  // Extract bbox from active geometry
  const activeBbox = useMemo(() => {
    return getBboxFromGeometry(activeGeometry);
  }, [activeGeometry]);

  // Compute cell estimate dynamically
  const cellEstimate = activeBbox ? estimateCells(activeBbox, gridSize) : 0;
  const tooMany = cellEstimate > 500;
  const warn = cellEstimate > 300 && !tooMany;
  const anyModality = Object.values(modalities).some(Boolean);

  return (
    <aside className="w-[320px] shrink-0 border-r border-border bg-card overflow-y-auto">
      <div className="p-4 space-y-5">
        <Section title={t("area_selection")}>
          <div className="flex gap-1.5 relative">
            <div className="relative flex-1">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  const matches = SUGGESTIONS.filter(s =>
                    s.label.toLowerCase().includes(e.target.value.toLowerCase())
                  );
                  setSuggestions(matches);
                  setShowSuggestions(true);
                }}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    triggerGeocode(search);
                  }
                }}
                placeholder={t("search_place")}
                className="pl-8 pr-8 h-9 text-xs"
              />
              {(search || searchLocation) && (
                <button
                  onClick={() => {
                    setSearch("");
                    setSearchLocation(null);
                    setSuggestions([]);
                    setShowSuggestions(false);
                  }}
                  className="absolute right-2 top-2.5 text-muted-foreground hover:text-foreground"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>
            <Button variant="outline" size="sm" className="h-9" title={t("draw_bbox")} onClick={onLoadArea}><Square className="h-4 w-4" /></Button>

            {showSuggestions && suggestions.length > 0 && (
              <div className="absolute z-50 w-full top-10 bg-popover text-popover-foreground border border-border rounded-md shadow-lg max-h-60 overflow-y-auto">
                {suggestions.map((s, idx) => (
                  <button
                    key={idx}
                    onClick={() => selectSuggestion(s)}
                    className="w-full text-left px-3 py-2 text-xs hover:bg-muted transition-colors border-b border-border/50 last:border-b-0"
                  >
                    {s.label}
                  </button>
                ))}
              </div>
            )}
          </div>
          <div className="flex gap-1.5">
            <Button
              variant={drawMode ? "default" : "outline"}
              size="sm"
              className="h-8 flex-1 text-xs"
              onClick={() => setDrawMode(!drawMode)}
              title={t("draw_area")}
            >
              <Pencil className="h-3.5 w-3.5" /> {t("draw_area")}
            </Button>
            {drawnGeometry && (
              <Button variant="ghost" size="sm" className="h-8 text-xs" onClick={() => setDrawnGeometry(null)} title={t("clear_area")}>
                <X className="h-3.5 w-3.5" />
              </Button>
            )}
          </div>
          {drawMode && <p className="text-[11px] text-accent">{t("drawing_mode")}</p>}
          
          <div className="space-y-1 bg-secondary/30 p-2 rounded border border-border/40">
            {drawnGeometry ? (
              <p className="text-[11px] text-primary font-medium">
                ● Using drawn area (City boundary is NOT analyzed)
              </p>
            ) : searchLocation ? (
              <p className="text-[11px] text-primary font-medium">
                ● Using default area around selected location (City boundary is NOT analyzed)
              </p>
            ) : (
              <p className="text-[11px] text-muted-foreground italic">
                Please draw an area or select a location
              </p>
            )}
          </div>

          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">{t("cells_estimate")}</span>
            <span className={cn("mono font-semibold", tooMany && "text-destructive", warn && "text-accent")}>{cellEstimate}</span>
          </div>
          {warn && <p className="text-[11px] text-accent flex items-center gap-1"><AlertTriangle className="h-3 w-3" /> {t("warn_300")}</p>}
          {tooMany && <p className="text-[11px] text-destructive flex items-center gap-1"><AlertTriangle className="h-3 w-3" /> {t("block_500")}</p>}
          <Button className="w-full h-9" onClick={onLoadArea} disabled={tooMany || loaded}>{t("load_area")}</Button>
        </Section>

        <Section title={t("grid_config")}>
          <Label className="text-xs text-muted-foreground">{t("grid_size")}</Label>
          <div className="grid grid-cols-3 gap-1">
            {[200, 500, 1000].map((n) => (
              <button key={n} onClick={() => setGridSize(n as 200 | 500 | 1000)}
                className={cn("h-8 text-xs rounded border mono", gridSize === n ? "bg-primary text-primary-foreground border-primary" : "border-border bg-secondary hover:bg-muted")}>{n}m</button>
            ))}
          </div>
          <p className="text-[10px] text-muted-foreground mono pt-1">{t("projection_label")}</p>
        </Section>

        <Section title={t("modalities")}>
          <div className="space-y-2">
            <ModRow id="poi" label="POI" dim="64-d MiniLM" checked={modalities.poi} onCheck={(v) => setModality("poi", v)} />
            <ModRow id="image" label="Image" dim="64-d ResNet" checked={modalities.image} onCheck={(v) => setModality("image", v)} />
            <ModRow id="graph" label="Graph" dim="32-d OSMnx" checked={modalities.graph} locked={modelType === "gnn"} onCheck={(v) => setModality("graph", v)} />
            <ModRow id="text" label="Text" dim="64-d BERT" checked={modalities.text} onCheck={(v) => setModality("text", v)} />
          </div>
          <div className="pt-2">
            <Label className="text-xs text-muted-foreground">{t("ablation_preset")}</Label>
            <Select onValueChange={(v) => { const p = PRESETS[v]; if (p) (Object.keys(p) as Modality[]).forEach((k) => setModality(k, p[k])); }}>
              <SelectTrigger className="h-8 mt-1"><SelectValue placeholder={t("preset_custom")} /></SelectTrigger>
              <SelectContent>
                <SelectItem value="poi_only">{t("preset_poi_only")}</SelectItem>
                <SelectItem value="poi_image">{t("preset_poi_image")}</SelectItem>
                <SelectItem value="poi_image_graph">{t("preset_poi_image_graph")}</SelectItem>
                <SelectItem value="all">{t("preset_all")}</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </Section>

        <div>
          {classifying
            ? <Button variant="destructive" className="w-full h-10" onClick={onCancel}>{t("cancel")}</Button>
            : <Button className="w-full h-10" onClick={onClassify} disabled={!loaded || !anyModality}><Play className="h-4 w-4" /> {t("classify")}</Button>}
        </div>

        <Section title={t("layers")}>
          <LayerRow label={t("layer_classification")} value={layers.classification} onChange={(v) => setLayer("classification", v)} />
          <LayerRow label={t("layer_poi")} value={layers.poi} onChange={(v) => setLayer("poi", v)} />
          {poiHeatmapEmpty && (
            <p className="text-[11px] text-muted-foreground pl-6">No POIs available for the selected area.</p>
          )}
          <LayerRow label={t("layer_satellite")} value={layers.satellite} onChange={(v) => setLayer("satellite", v)} />
        </Section>
        <AiQueryPanel />
      </div>
    </aside>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (<section className="space-y-2"><h3 className="text-[11px] uppercase tracking-wider text-muted-foreground font-semibold">{title}</h3>{children}</section>);
}
function ModRow({ id, label, dim, checked, onCheck, locked }: { id: string; label: string; dim: string; checked: boolean; onCheck: (v: boolean) => void; locked?: boolean }) {
  return (
    <label htmlFor={id} className="flex items-center gap-2 text-sm cursor-pointer rounded px-1 py-0.5 hover:bg-muted/50">
      <Checkbox id={id} checked={checked} disabled={locked} onCheckedChange={(v) => onCheck(!!v)} />
      <span className="flex-1">{label}</span>
      <span className="mono text-[10px] text-muted-foreground">{dim}</span>
      {locked && <Lock className="h-3 w-3 text-muted-foreground" />}
    </label>
  );
}
function LayerRow({ label, value, onChange }: { label: string; value: boolean; onChange: (v: boolean) => void }) {
  return (<div className="flex items-center justify-between text-sm py-0.5"><span>{label}</span><Switch checked={value} onCheckedChange={onChange} /></div>);
}
