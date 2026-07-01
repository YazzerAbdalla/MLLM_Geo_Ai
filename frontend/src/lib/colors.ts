import type { LandUseClass } from "./api/types";

export const classHex: Record<LandUseClass, string> = {
  Residential: "#FFD966",
  Commercial: "#E63946",
  Industrial: "#9B5DE5",
};

export function opacityFromConfidence(c: number) {
  return 0.35 + c * 0.6;
}