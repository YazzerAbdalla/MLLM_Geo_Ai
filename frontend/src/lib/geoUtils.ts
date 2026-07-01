/**
 * @file geoUtils.ts
 * @description Geometry helper functions for calculating bounding boxes and generating default polygons around points.
 */

import type { DrawnGeometry } from "../store/dashboardStore";

/**
 * Calculates the bounding box of a given drawn polygon geometry.
 *
 * @param geom The DrawnGeometry polygon coordinates (coordinates[0] contains the outer ring)
 * @returns An object containing west, south, east, north coordinates, or null if geometry is invalid
 */
export function getBboxFromGeometry(geom: DrawnGeometry): { west: number; south: number; east: number; north: number } | null {
  if (!geom || geom.type !== "Polygon" || !geom.coordinates || geom.coordinates.length === 0) {
    // Return null if the geometry is invalid
    return null;
  }
  const ring = geom.coordinates[0];
  if (!ring || ring.length === 0) {
    // Return null if the ring is empty
    return null;
  }
  
  let west = Infinity;
  let east = -Infinity;
  let south = Infinity;
  let north = -Infinity;
  
  // Find min and max longitude and latitude coordinates
  for (const [lng, lat] of ring) {
    if (lng < west) west = lng;
    if (lng > east) east = lng;
    if (lat < south) south = lat;
    if (lat > north) north = lat;
  }
  
  return { west, south, east, north };
}

/**
 * Creates a default 1km x 1km polygon area centered on the provided longitude and latitude.
 *
 * @param lng Longitude of the center point
 * @param lat Latitude of the center point
 * @returns A DrawnGeometry object representing the 1km x 1km box
 */
export function createSmallDefaultArea(lng: number, lat: number): DrawnGeometry {
  // Approximate conversion: 1 degree latitude is 111,000 meters.
  // 1 degree longitude at given latitude is 111,000 * cos(lat) meters.
  const deltaLat = 0.5 * 1000 / 111000;
  const deltaLng = 0.5 * 1000 / (111000 * Math.cos(lat * Math.PI / 180));
  
  const west = lng - deltaLng;
  const east = lng + deltaLng;
  const south = lat - deltaLat;
  const north = lat + deltaLat;
  
  // Return the polygon representation (closed loop)
  return {
    type: "Polygon",
    coordinates: [
      [
        [west, south],
        [east, south],
        [east, north],
        [west, north],
        [west, south]
      ]
    ]
  };
}
