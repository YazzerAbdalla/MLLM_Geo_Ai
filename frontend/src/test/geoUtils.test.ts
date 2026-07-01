/**
 * @file geoUtils.test.ts
 * @description Unit tests for geometry utility functions such as bounding box extraction and default area generation.
 */

import { describe, it, expect } from "vitest";
import { getBboxFromGeometry, createSmallDefaultArea } from "../lib/geoUtils";
import type { DrawnGeometry } from "../store/dashboardStore";

describe("getBboxFromGeometry", () => {
  /**
   * Test case for returning null when the input geometry is null or empty.
   */
  it("should return null if geometry is null", () => {
    // Call the function with null and verify output
    const bbox = getBboxFromGeometry(null);
    expect(bbox).toBeNull();
  });

  /**
   * Test case for a valid Polygon geometry.
   */
  it("should extract correct bounding box from a valid Polygon", () => {
    const geometry: DrawnGeometry = {
      type: "Polygon",
      coordinates: [
        [
          [10, 20],
          [30, 20],
          [30, 40],
          [10, 40],
          [10, 20]
        ]
      ]
    };
    
    // Call function and verify that boundaries are extracted correctly
    const bbox = getBboxFromGeometry(geometry);
    expect(bbox).toEqual({
      west: 10,
      east: 30,
      south: 20,
      north: 40
    });
  });
});

describe("createSmallDefaultArea", () => {
  /**
   * Test case to verify that a default 1km x 1km box is generated centered on the coordinates.
   */
  it("should create a valid 1km x 1km polygon centered around target coordinates", () => {
    const lat = 30.0;
    const lng = 31.0;
    
    // Generate default area geometry
    const geom = createSmallDefaultArea(lng, lat);
    expect(geom).not.toBeNull();
    expect(geom.type).toBe("Polygon");
    expect(geom.coordinates[0].length).toBe(5); // Closed polygon with 5 coordinates (4 corners + start/end)

    // Calculate bbox of the generated geometry
    const bbox = getBboxFromGeometry(geom);
    expect(bbox).not.toBeNull();
    
    // Check that the center of the bounding box matches the input coordinates
    if (bbox) {
      const centerLng = (bbox.west + bbox.east) / 2;
      const centerLat = (bbox.south + bbox.north) / 2;
      
      // Center coordinates should be approximately correct
      expect(centerLng).toBeCloseTo(lng, 5);
      expect(centerLat).toBeCloseTo(lat, 5);
      
      // Check scale: lat delta should be approx 1km (1000m / 111000m/deg = 0.009 deg)
      // So north - south should be approximately 0.009009
      expect(bbox.north - bbox.south).toBeCloseTo(0.009009, 4);
    }
  });
});
