import { useMemo, useState } from "react";
import { Search, MapPin, Building2, Trash2 } from "lucide-react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { CategoryQuickFilters } from "./CategoryQuickFilters";
import type { PoiPreviewFeatureProperties } from "@/api/poiDataManagerTypes";

type StatusFilter = "all" | "new" | "duplicate_poi" | "duplicate_coord" | "warnings" | "errors";

const STATUS_OPTIONS: { key: StatusFilter; labelKey: string }[] = [
  { key: "all", labelKey: "poi_manager_filter_all" },
  { key: "new", labelKey: "poi_manager_filter_new" },
  { key: "duplicate_poi", labelKey: "poi_manager_filter_duplicate_poi" },
  { key: "duplicate_coord", labelKey: "poi_manager_filter_duplicate_coord" },
  { key: "warnings", labelKey: "poi_manager_filter_warnings" },
  { key: "errors", labelKey: "poi_manager_filter_errors" },
];

const STATUS_COLORS: Record<string, string> = {
  new: "bg-blue-500",
  warning: "bg-orange-500",
  duplicate_poi: "bg-yellow-500",
  duplicate_coord: "bg-red-500",
  invalid: "bg-gray-400",
};

const STATUS_LABELS: Record<string, string> = {
  new: "New",
  warning: "Warning",
  duplicate_poi: "Dup POI",
  duplicate_coord: "Dup Coord",
  invalid: "Invalid",
};

interface PreviewSidebarProps {
  features: GeoJSON.Feature<GeoJSON.Point, PoiPreviewFeatureProperties>[];
  allCategories: string[];
  selectedPoiId: string | null;
  onPoiSelect: (f: GeoJSON.Feature<GeoJSON.Point, PoiPreviewFeatureProperties>) => void;
  onDeletePoi: (f: GeoJSON.Feature<GeoJSON.Point, PoiPreviewFeatureProperties>) => void;
  t: (key: string) => string;
}

export function PreviewSidebar({
  features,
  allCategories,
  selectedPoiId,
  onPoiSelect,
  onDeletePoi,
  t,
}: PreviewSidebarProps) {
  console.log("[PreviewSidebar] Rendering with", features.length, "features,", allCategories.length, "categories");

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [categoryFilter, setCategoryFilter] = useState<string | null>(null);

  const filtered = useMemo(() => {
    let list = features;
    if (search) {
      const q = search.toLowerCase();
      list = list.filter((f) => {
        const p = f.properties;
        return (
          p.name.toLowerCase().includes(q) ||
          p.category.toLowerCase().includes(q) ||
          (p.place_type || "").toLowerCase().includes(q) ||
          (p.label || "").toLowerCase().includes(q)
        );
      });
    }
    if (statusFilter === "new") {
      list = list.filter((f) => f.properties.status === "new");
    } else if (statusFilter === "duplicate_poi") {
      list = list.filter((f) => f.properties.status === "duplicate_poi");
    } else if (statusFilter === "duplicate_coord") {
      list = list.filter((f) => f.properties.status === "duplicate_coord");
    } else if (statusFilter === "warnings") {
      list = list.filter(
        (f) =>
          f.properties.status === "warning" ||
          f.properties.status === "duplicate_poi" ||
          f.properties.status === "duplicate_coord"
      );
    } else if (statusFilter === "errors") {
      list = list.filter((f) => f.properties.status === "invalid");
    }
    if (categoryFilter) {
      list = list.filter(
        (f) =>
          f.properties.category.toLowerCase() === categoryFilter.toLowerCase()
      );
    }
    console.log("[PreviewSidebar] Filtered:", list.length, "of", features.length);
    return list;
  }, [features, search, statusFilter, categoryFilter]);

  return (
    <aside className="w-[300px] shrink-0 border-l border-border bg-card flex flex-col">
      <div className="p-3 border-b border-border space-y-2">
        <h3 className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
          <MapPin className="h-3 w-3" />
          {t("poi_manager_sidebar_title")}
          <span className="font-mono text-[10px] text-muted-foreground/60">
            ({filtered.length})
          </span>
        </h3>
        <div className="relative">
          <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3 w-3 text-muted-foreground" />
          <input
            type="text"
            placeholder={t("poi_manager_search_placeholder_v2")}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full h-7 rounded border border-border bg-secondary/40 pl-6 pr-2 text-xs outline-none focus:border-primary"
          />
        </div>
        <Select
          value={statusFilter}
          onValueChange={(v) => setStatusFilter(v as StatusFilter)}
        >
          <SelectTrigger className="h-7 text-[10px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {STATUS_OPTIONS.map((opt) => (
              <SelectItem key={opt.key} value={opt.key} className="text-xs">
                {t(opt.labelKey)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <CategoryQuickFilters
        allCategories={allCategories}
        selected={categoryFilter}
        onSelect={setCategoryFilter}
        t={t}
      />

      <ScrollArea className="flex-1">
        <div className="px-1.5 py-1 space-y-0.5">
          {filtered.map((f, i) => {
            const p = f.properties;
            const coords = (f.geometry as GeoJSON.Point)
              .coordinates as [number, number];
            const id = p.osm_id || `${coords[0]}_${coords[1]}`;
            const isSelected = id === selectedPoiId;
            return (
              <button
                key={p.osm_id || i}
                onClick={() => onPoiSelect(f)}
                className={cn(
                  "w-full text-left rounded px-2 py-1.5 text-xs transition-colors space-y-0.5 group",
                  isSelected
                    ? "bg-primary/15 ring-1 ring-primary"
                    : "hover:bg-secondary/60"
                )}
              >
                <div className="flex items-center gap-1.5">
                  <span
                    className={cn(
                      "w-2 h-2 rounded-full shrink-0",
                      STATUS_COLORS[p.status] || "bg-gray-400"
                    )}
                  />
                  <span className="font-medium truncate flex-1">{p.name}</span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeletePoi(f);
                    }}
                    className="shrink-0 opacity-0 group-hover:opacity-100 hover:text-destructive transition-opacity"
                    title={t("poi_manager_delete_poi") || "Remove"}
                  >
                    <Trash2 className="h-3 w-3" />
                  </button>
                  <span className="text-[9px] uppercase text-muted-foreground shrink-0">
                    {STATUS_LABELS[p.status] || p.status}
                  </span>
                </div>
                <div className="flex items-center gap-1 text-[10px] text-muted-foreground">
                  <Building2 className="h-2.5 w-2.5" />
                  <span className="truncate">{p.category}</span>
                </div>
              </button>
            );
          })}
          {filtered.length === 0 && (
            <p className="text-xs text-muted-foreground text-center py-8">
              {t("no_results") || "No matching POIs"}
            </p>
          )}
        </div>
      </ScrollArea>
    </aside>
  );
}
