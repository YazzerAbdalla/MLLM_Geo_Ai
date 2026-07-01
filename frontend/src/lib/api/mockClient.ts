/**
 * Geo helpers that survived the mock → real backend migration.
 * The mock data files and fake job/evaluate functions have been removed —
 * see `src/api/*` and `src/hooks/api/*` for the live FastAPI client.
 */

/** Default Cairo bbox used to seed /api/v1/load-area requests. */
export const cairoBbox = { north: 30.10, south: 29.90, east: 31.30, west: 31.10 };

/** Rough grid-cell count estimate based on bbox + cell size in meters. */
export function estimateCells(
  bbox: { north: number; south: number; east: number; west: number },
  gridSizeM: number
) {
  const latM = (bbox.north - bbox.south) * 111_000;
  const lngM =
    (bbox.east - bbox.west) * 111_000 *
    Math.cos(((bbox.north + bbox.south) / 2) * Math.PI / 180);
  return Math.max(0, Math.ceil(latM / gridSizeM) * Math.ceil(lngM / gridSizeM));
}

/** Ray-casting point-in-polygon test for a single linear ring [[lng,lat],...]. */
export function pointInPolygon(pt: [number, number], ring: number[][]): boolean {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i];
    const [xj, yj] = ring[j];
    const intersect =
      yi > pt[1] !== yj > pt[1] &&
      pt[0] < ((xj - xi) * (pt[1] - yi)) / (yj - yi + 1e-12) + xi;
    if (intersect) inside = !inside;
  }
  return inside;
}