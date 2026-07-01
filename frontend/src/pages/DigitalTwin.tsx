import { Cpu } from "lucide-react";
import { StubPage } from "./StubPage";

export default function DigitalTwin() {
  return (
    <StubPage
      title="Digital Twin"
      subtitle="Natural-language queries over the live Cairo grid"
      description="Ask the twin in plain English or Arabic — 'show industrial cells with low road density near the Nile' — and have it route to the classified grid, road graph, and POI layers in real time."
      features={[
        "Bilingual NL → spatial query compiler (EN / AR)",
        "Scenario simulation: re-classify under hypothetical POI changes",
        "Time-slider for OSM history snapshots",
        "Shareable saved queries with reproducible bbox + grid config",
      ]}
      icon={<Cpu className="h-7 w-7" />}
    />
  );
}