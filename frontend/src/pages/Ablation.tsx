import { GitCompare } from "lucide-react";
import { StubPage } from "./StubPage";

export default function Ablation() {
  return (
    <StubPage
      title="Ablation Studies"
      subtitle="Side-by-side modality and fusion comparisons"
      description="Run the same bbox through every modality combination — POI only, POI+Image, +Graph, +Text — and every fusion strategy, then compare accuracy, macro-F1, and per-class confusion matrices in one view."
      features={[
        "Matrix view: modality combo × fusion method",
        "Delta heatmap vs. the POI-only baseline",
        "Per-class F1 radar chart across runs",
        "Export LaTeX-ready table for academic write-up",
      ]}
      icon={<GitCompare className="h-7 w-7" />}
    />
  );
}