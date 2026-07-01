import { Brain } from "lucide-react";
import { StubPage } from "./StubPage";

export default function MllmBuilder() {
  return (
    <StubPage
      title="MLLM Builder"
      subtitle="Author and curate multilingual POI semantic embeddings"
      description="Compose prompts, fine-tune the paraphrase-multilingual-MiniLM-L12-v2 backbone on your city's POI corpus, and inspect 384-dim semantic clusters before sending them to the classification pipeline."
      features={[
        "Prompt templates for POI → semantic vector aggregation",
        "Side-by-side comparison of base vs. fine-tuned embeddings",
        "Cluster explorer (UMAP / t-SNE) over the cell-level fingerprints",
        "Export adapters as a swappable module for the Classify endpoint",
      ]}
      icon={<Brain className="h-7 w-7" />}
    />
  );
}