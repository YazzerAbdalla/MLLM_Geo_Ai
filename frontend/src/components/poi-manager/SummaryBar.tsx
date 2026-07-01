import { Database, CheckCircle2, SkipForward, Building2, MapPin, Layers, Crosshair, Maximize2 } from "lucide-react";

interface PoiValidationSummary {
  valid: boolean;
  total_rows: number;
  errors: Array<unknown>;
  warnings: Array<unknown>;
}

interface PoiStats {
  total?: number;
  valid?: number;
  skipped?: number;
  duplicate_pois?: number;
  duplicate_coords?: number;
  category_count?: number;
  center?: { lat?: number; lng?: number } | null;
  bbox?: { north?: number; south?: number; east?: number; west?: number } | null;
}

interface SummaryBarProps {
  statistics: PoiStats | null;
  validation?: PoiValidationSummary | null;
  t: (key: string) => string;
}

function Metric({
  icon,
  label,
  value,
  valueColor,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  valueColor?: string;
}) {
  return (
    <div className="flex items-center gap-1.5 text-xs px-2 py-1 rounded bg-secondary/40 border border-border">
      <span className="text-muted-foreground shrink-0">{icon}</span>
      <span className="text-muted-foreground hidden sm:inline">{label}:</span>
      <span className={`font-semibold mono ${valueColor ?? ""}`}>{value}</span>
    </div>
  );
}

export function SummaryBar({ statistics, validation, t }: SummaryBarProps) {
  console.log("[SummaryBar] Rendering with stats:", statistics, "validation:", validation);

  const safeVal = (v: number | undefined | null, fallback = "0") =>
    v != null ? v.toLocaleString() : fallback;

  // Derive metrics from validation when statistics is null
  const total = statistics?.total ?? validation?.total_rows ?? 0;
  const validCount = statistics?.valid ?? (validation?.valid === true ? validation.total_rows : 0);
  const skipped = statistics?.skipped ?? 0;
  const dupPois = statistics?.duplicate_pois ?? 0;
  const dupCoords = statistics?.duplicate_coords ?? 0;
  const catCount = statistics?.category_count ?? 0;

  const center = statistics?.center?.lat != null && statistics?.center?.lng != null
    ? `${statistics.center.lat.toFixed(4)}, ${statistics.center.lng.toFixed(4)}`
    : "—";

  const bbox = statistics?.bbox?.south != null && statistics?.bbox?.north != null
    ? `${statistics.bbox.south.toFixed(2)}°S, ${statistics.bbox.north.toFixed(2)}°N`
    : "—";

  return (
    <div className="flex flex-wrap items-center gap-1.5 px-4 py-2 border-b border-border bg-card/50">
      <Metric
        icon={<Database className="h-3 w-3" />}
        label={t("poi_manager_summary_uploaded")}
        value={safeVal(total)}
        valueColor="text-blue-600"
      />
      <Metric
        icon={<CheckCircle2 className="h-3 w-3 text-green-600" />}
        label={t("poi_manager_summary_valid")}
        value={safeVal(validCount)}
        valueColor="text-green-600"
      />
      <Metric
        icon={<SkipForward className="h-3 w-3 text-muted-foreground" />}
        label={t("poi_manager_summary_skipped")}
        value={safeVal(skipped)}
        valueColor="text-gray-500"
      />
      <Metric
        icon={<Building2 className="h-3 w-3 text-orange-600" />}
        label={t("poi_manager_duplicate_pois")}
        value={safeVal(dupPois)}
        valueColor="text-orange-600"
      />
      <Metric
        icon={<MapPin className="h-3 w-3 text-rose-600" />}
        label={t("poi_manager_duplicate_coords")}
        value={safeVal(dupCoords)}
        valueColor="text-rose-600"
      />
      <Metric
        icon={<Layers className="h-3 w-3" />}
        label={t("poi_manager_summary_categories")}
        value={safeVal(catCount)}
        valueColor="text-violet-600"
      />
      <Metric
        icon={<Crosshair className="h-3 w-3" />}
        label={t("poi_manager_summary_center")}
        value={center}
      />
      <Metric
        icon={<Maximize2 className="h-3 w-3" />}
        label={t("poi_manager_summary_bbox")}
        value={bbox}
      />
    </div>
  );
}
