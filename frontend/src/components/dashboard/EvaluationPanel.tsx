import { useState } from "react";
import { Upload, Loader2, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useDash } from "@/store/dashboardStore";
import { useEvaluate } from "@/hooks/api/useEvaluate";
import { evaluationExportUrl, exportJobUrl } from "@/api/endpoints";
import { classHex } from "@/lib/colors";
import { useI18n } from "@/lib/i18n";
import type { EvaluateResponse } from "@/api/types";
import { KpiCard } from "./KpiCard";
import { AccuracyComparison } from "./AccuracyComparison";

export function EvaluationPanel() {
  const cells = useDash((s) => s.cells);
  const classifyJobId = useDash((s) => s.classifyJobId);
  const { t } = useI18n();
  const [metrics, setMetrics] = useState<EvaluateResponse | null>(null);
  const evalM = useEvaluate();
  const loading = evalM.isPending;
  if (cells.length === 0) return <div className="p-6 text-sm text-muted-foreground text-center">{t("no_classification")}</div>;
  const counts: Record<string, number> = { Residential: 0, Commercial: 0, Industrial: 0 };
  cells.forEach((c) => (counts[c.class] += 1));
  const avgConf = cells.reduce((a, c) => a + c.confidence, 0) / cells.length;
  const buckets = Array(10).fill(0);
  cells.forEach((c) => buckets[Math.min(9, Math.floor(c.confidence * 10))]++);
  const maxB = Math.max(...buckets, 1);
  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] ?? null;
    if (!f || !classifyJobId) return;
    evalM.mutate(
      { jobId: classifyJobId, file: f },
      { onSuccess: (data) => setMetrics(data) }
    );
  };
  return (
    <div className="overflow-y-auto h-full p-4 space-y-5">
      {classifyJobId && (
        <section className="border-b border-border pb-3 flex flex-wrap gap-1.5">
          {(["geojson", "csv", "shapefile"] as const).map((fmt) => (
            <Button key={fmt} asChild size="sm" variant="outline" className="h-7 text-[11px]">
              <a href={exportJobUrl(classifyJobId, fmt)} target="_blank" rel="noreferrer">
                <Download className="h-3 w-3" /> {fmt.toUpperCase()}
              </a>
            </Button>
          ))}
        </section>
      )}
      <section>
        <h4 className="text-xs font-semibold mb-2">{t("distribution")}</h4>
        <div className="space-y-1.5 text-xs">
          {(["Residential", "Commercial", "Industrial"] as const).map((k) => {
            const pct = (counts[k] / cells.length) * 100;
            return (
              <div key={k}>
                <div className="flex justify-between"><span>{k}</span><span className="mono text-muted-foreground">{counts[k]} · {pct.toFixed(1)}%</span></div>
                <div className="h-1.5 bg-secondary rounded overflow-hidden"><div className="h-full" style={{ width: `${pct}%`, backgroundColor: classHex[k] }} /></div>
              </div>
            );
          })}
        </div>
      </section>

      <section><h4 className="text-xs font-semibold mb-2">{t("avg_confidence")}</h4><div className="mono text-2xl">{(avgConf * 100).toFixed(1)}%</div></section>

      <section>
        <h4 className="text-xs font-semibold mb-2">Confidence histogram</h4>
        <div className="flex items-end gap-1 h-20 border-b border-border">
          {buckets.map((b, i) => <div key={i} className="flex-1 bg-primary/70 rounded-t" style={{ height: `${(b / maxB) * 100}%` }} />)}
        </div>
        <div className="flex justify-between mono text-[10px] text-muted-foreground pt-1"><span>0.0</span><span>0.5</span><span>1.0</span></div>
      </section>

      <section className="border-t border-border pt-4">
        <label className="block">
          <Button asChild variant="outline" size="sm" className="w-full cursor-pointer">
            <span>{loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}{t("ground_truth")}</span>
          </Button>
          <input type="file" accept=".csv" className="hidden" onChange={handleUpload} disabled={!classifyJobId || loading} />
        </label>
        {!classifyJobId && <p className="text-[11px] text-muted-foreground mt-1">Run classification first to enable evaluation.</p>}
      </section>

      {metrics && <>
        <section className="grid grid-cols-2 gap-2">
          <KpiCard
            label={t("accuracy")}
            value={metrics.overall_accuracy}
            format="percent"
          />
          <KpiCard
            label={t("macro_f1")}
            value={metrics.macro_f1}
            format="decimal"
          />
          <KpiCard
            label={t("weighted_f1")}
            value={metrics.weighted_f1}
            format="decimal"
          />
          <KpiCard
            label={t("spatial_accuracy")}
            value={metrics.spatial_accuracy}
            format="percent"
            tooltip={t("spatial_accuracy_tooltip")}
            detail={t("spatial_accuracy_detail")}
          />
        </section>
        <AccuracyComparison
          overallAccuracy={metrics.overall_accuracy}
          spatialAccuracy={metrics.spatial_accuracy}
        />
        <section>
          <h4 className="text-xs font-semibold mb-2">{t("per_class_f1")}</h4>
          <div className="space-y-1 text-xs">
            {(["Residential", "Commercial", "Industrial"] as const).map((k) => (
              <div key={k} className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-sm" style={{ backgroundColor: classHex[k] }} />
                <span className="flex-1">{k}</span><span className="mono">{metrics.per_class_f1[k].toFixed(3)}</span>
              </div>
            ))}
          </div>
        </section>
        <section>
          <h4 className="text-xs font-semibold mb-2">{t("confusion_matrix")}</h4>
          <ConfusionMatrix matrix={metrics.confusion_matrix} labels={metrics.class_labels ?? ["Residential", "Commercial", "Industrial"]} />
        </section>
        {classifyJobId && (
          <section>
            <Button asChild size="sm" variant="outline" className="w-full">
              <a href={evaluationExportUrl(classifyJobId)} target="_blank" rel="noreferrer">
                <Download className="h-3.5 w-3.5" /> Export evaluation CSV
              </a>
            </Button>
          </section>
        )}
      </>}
    </div>
  );
}

function ConfusionMatrix({ matrix, labels }: { matrix: number[][]; labels: string[] }) {
  const max = Math.max(...matrix.flat(), 1);
  return (
    <div className="inline-grid gap-px text-xs" style={{ gridTemplateColumns: `auto repeat(${labels.length}, 36px)` }}>
      <div />
      {labels.map((l) => <div key={l} className="text-center mono text-[10px] text-muted-foreground">{l.slice(0, 3)}</div>)}
      {matrix.map((row, i) => (
        <div key={i} className="contents">
          <div className="mono text-[10px] text-muted-foreground pr-1 self-center">{labels[i].slice(0, 3)}</div>
          {row.map((v, j) => {
            const intensity = v / max;
            return (
              <div key={`${i}-${j}`} className="h-9 grid place-items-center mono text-xs rounded-sm"
                style={{ backgroundColor: `hsl(var(--primary) / ${0.15 + intensity * 0.75})`, color: intensity > 0.5 ? "hsl(var(--primary-foreground))" : "hsl(var(--foreground))" }}>{v}</div>
            );
          })}
        </div>
      ))}
    </div>
  );
}
