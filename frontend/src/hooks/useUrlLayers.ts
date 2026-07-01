import { useEffect, useRef } from "react";
import { useDash, type LayerKey } from "@/store/dashboardStore";

const KEYS: LayerKey[] = ["classification", "poi", "roads", "graph", "satellite"];

export function useUrlLayers() {
  const layers = useDash((s) => s.layers);
  const setLayer = useDash((s) => s.setLayer);
  const initialized = useRef(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const raw = params.get("layers");
    if (raw !== null) {
      const active = new Set(raw.split(",").filter(Boolean));
      KEYS.forEach((k) => setLayer(k, active.has(k)));
    }
    initialized.current = true;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!initialized.current) return;
    const active = KEYS.filter((k) => layers[k]).join(",");
    const params = new URLSearchParams(window.location.search);
    if (active) params.set("layers", active); else params.delete("layers");
    const qs = params.toString();
    window.history.replaceState(null, "", window.location.pathname + (qs ? "?" + qs : ""));
  }, [layers]);
}
