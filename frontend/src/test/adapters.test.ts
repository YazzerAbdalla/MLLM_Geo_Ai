/**
 * @file adapters.test.ts
 * @description Unit tests for the featureToCell adapter covering both the flat
 * backend shape and the legacy wrapped shape.
 */

import { describe, it, expect } from "vitest";
import { featureToCell } from "../lib/adapters";
import type { BackendFeatureFlat } from "../api/types";

// ---------------------------------------------------------------------------
// Shared geometry fixture
// ---------------------------------------------------------------------------

/** A tiny polygon around central Cairo for testing */
const GEO: GeoJSON.Polygon = {
  type: "Polygon",
  coordinates: [
    [
      [31.2175, 29.9807],
      [31.2220, 29.9807],
      [31.2220, 29.9852],
      [31.2175, 29.9852],
      [31.2175, 29.9807],
    ],
  ],
};

// ---------------------------------------------------------------------------
// Flat shape tests  (real backend format)
// ---------------------------------------------------------------------------

describe("featureToCell — flat backend shape", () => {
  /** Full flat feature matching the real backend JSON */
  const flatFeature: BackendFeatureFlat = {
    cell_id: 0,
    dominant_class: "Commercial",
    confidence: 0.42,
    confidences: {
      residential: 0.286,
      commercial: 0.42,
      industrial: 0.294,
    },
    road_density: 35.95,
    node_count: 71,
    degree_centrality: 0.0,
    clustering_coeff: 0.0,
    total_road_length_m: 10436.75,
    poi_top_categories: ["restaurant", "shop"],
    text_embedding_norm: 0.0,
    graph_embedding_norm: 10436.99,
    satellite_thumbnail_url: "/api/v1/thumbnails/grid_bb85adf5/0.jpg",
    geometry: GEO,
    // backend sends centroid as [lat, lng]
    centroid: [29.983024, 31.215739],
  };

  it("maps cell_id number to string id", () => {
    // cell_id is a number in the flat shape — must become a string
    const cell = featureToCell(flatFeature as any);
    expect(cell.id).toBe("0");
  });

  it("resolves dominant_class to title-case LandUseClass", () => {
    // 'Commercial' from 'commercial' dominant_class
    const cell = featureToCell(flatFeature as any);
    expect(cell.class).toBe("Commercial");
  });

  it("capitalises confidence keys from lowercase to LandUseClass", () => {
    const cell = featureToCell(flatFeature as any);
    // All three keys must exist as title-case
    expect(cell.confidences.Residential).toBeCloseTo(0.286);
    expect(cell.confidences.Commercial).toBeCloseTo(0.42);
    expect(cell.confidences.Industrial).toBeCloseTo(0.294);
  });

  it("computes max confidence from normalised confidences map", () => {
    const cell = featureToCell(flatFeature as any);
    // Max of 0.286, 0.42, 0.294 = 0.42
    expect(cell.confidence).toBeCloseTo(0.42);
  });

  it("maps poi_top_categories to top5_poi", () => {
    const cell = featureToCell(flatFeature as any);
    expect(cell.top5_poi).toEqual(["restaurant", "shop"]);
  });

  it("maps satellite_thumbnail_url to satellite_thumb", () => {
    const cell = featureToCell(flatFeature as any);
    expect(cell.satellite_thumb).toBe("/api/v1/thumbnails/grid_bb85adf5/0.jpg");
  });

  it("flips backend centroid [lat, lng] to [lng, lat]", () => {
    const cell = featureToCell(flatFeature as any);
    // Backend: [29.983024, 31.215739] → expected centroid: [31.215739, 29.983024]
    expect(cell.centroid[0]).toBeCloseTo(31.215739, 4);
    expect(cell.centroid[1]).toBeCloseTo(29.983024, 4);
  });

  it("falls back to computed centroid when backend centroid is missing", () => {
    const nocentroid = { ...flatFeature, centroid: undefined };
    const cell = featureToCell(nocentroid as any);
    // Should not throw — centroid is derived from geometry ring
    expect(cell.centroid).toHaveLength(2);
  });

  it("does not crash when optional fields are absent", () => {
    const minimal: BackendFeatureFlat = {
      cell_id: 1,
      dominant_class: "Residential",
      confidence: 0.9,
      confidences: { residential: 0.9, commercial: 0.05, industrial: 0.05 },
      geometry: GEO,
    };
    const cell = featureToCell(minimal as any);
    expect(cell.road_density).toBe(0);
    expect(cell.top5_poi).toEqual([]);
    expect(cell.satellite_thumb).toBe("");
  });

  it("handles flat feature with empty properties: {} (valid GeoJSON)", () => {
    // Some backends include a standard GeoJSON `properties` field alongside
    // flat fields. The adapter must not be tricked into the wrapped path.
    const withProps = {
      ...flatFeature,
      properties: {},
    };
    const cell = featureToCell(withProps as any);
    expect(cell.id).toBe("0");
    expect(cell.class).toBe("Commercial");
    expect(cell.confidences.Residential).toBeCloseTo(0.286);
  });
});

// ---------------------------------------------------------------------------
// Wrapped shape tests  (legacy / mock format)
// ---------------------------------------------------------------------------

describe("featureToCell — wrapped GeoJSON properties shape", () => {
  /** Standard GeoJSON Feature with a `properties` object */
  const wrappedFeature = {
    type: "Feature" as const,
    properties: {
      cell_id: "abc-123",
      class: "Industrial" as const,
      confidences: { Residential: 0.1, Commercial: 0.2, Industrial: 0.7 },
      road_density: 12.5,
      node_count: 30,
      degree_centrality: 0.05,
      clustering_coeff: 0.2,
      total_road_length_m: 5000,
      graph_embedding_norm: 1.2,
      text_embedding_norm: 0.8,
      top_poi: ["hospital"],
      satellite_thumb: "/thumbs/abc.jpg",
    },
    geometry: GEO,
  };

  it("reads cell_id string from properties", () => {
    const cell = featureToCell(wrappedFeature as any);
    expect(cell.id).toBe("abc-123");
  });

  it("reads class from properties.class", () => {
    const cell = featureToCell(wrappedFeature as any);
    expect(cell.class).toBe("Industrial");
  });

  it("reads top_poi from properties", () => {
    const cell = featureToCell(wrappedFeature as any);
    expect(cell.top5_poi).toEqual(["hospital"]);
  });

  it("reads satellite_thumb from properties", () => {
    const cell = featureToCell(wrappedFeature as any);
    expect(cell.satellite_thumb).toBe("/thumbs/abc.jpg");
  });

  it("normalises lowercase class to title-case LandUseClass", () => {
    // Backend might return lowercase class values — adapter must capitalise
    const lower = {
      ...wrappedFeature,
      properties: { ...wrappedFeature.properties, class: "residential" },
    };
    const cell = featureToCell(lower as any);
    expect(cell.class).toBe("Residential");
  });
});
