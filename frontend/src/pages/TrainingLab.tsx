import { FlaskConical } from "lucide-react";
import { StubPage } from "./StubPage";

export default function TrainingLab() {
  return (
    <StubPage
      title="Training Lab"
      subtitle="Fine-tune classifiers on labelled urban grids"
      description="Upload a labelled GeoJSON, pick MLP or GNN, watch loss / F1 curves stream in, and promote the winning checkpoint into the live Classify endpoint."
      features={[
        "Drag-and-drop labelled GeoJSON / CSV ingestion",
        "Live training curves (loss, accuracy, macro-F1) via WebSocket",
        "Hyperparameter sweep grid with per-run confusion matrix",
        "Promote-to-production checkpoint registry",
      ]}
      icon={<FlaskConical className="h-7 w-7" />}
    />
  );
}