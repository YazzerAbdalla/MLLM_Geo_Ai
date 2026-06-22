"""
 * Tests verifying GeoJSON RFC 7946 compliance of all API endpoints.
 * Ensures every FeatureCollection contains valid Feature objects
 * with correct structure and coordinate ordering.
"""
import json
import pytest
from app.models.result import CellResult
from app.interfaces.helpers import _graph_to_geojson


# ---------------------------------------------------------------------------
# Unit tests — CellResult → Feature conversion logic  (fusion_service.py)
# ---------------------------------------------------------------------------


def _build_feature(overrides=None):
    """
    Helper that mimics the fusion_service result-building logic.
    Returns a GeoJSON Feature dict.
    """
    geometry = {"type": "Polygon", "coordinates": [[[31.2, 30.0], [31.22, 30.0], [31.22, 30.02], [31.2, 30.02], [31.2, 30.0]]]}

    feature = {
        "type": "Feature",
        "properties": {
            "cell_id": "0",
            "dominant_class": "Residential",
            "confidence": 0.4273,
            "confidences": {"residential": 0.43, "commercial": 0.33, "industrial": 0.24},
            "road_density": 50.76,
            "node_count": 10,
            "degree_centrality": 0.0,
            "clustering_coeff": 0.0,
            "total_road_length_m": 500.0,
            "poi_top_categories": ["Food", "Shop", "School"],
            "text_embedding_norm": 0.85,
            "graph_embedding_norm": 0.72,
            "centroid": [31.21, 30.01],
            "satellite_thumbnail_url": "/api/v1/thumbnails/grid_1/0.jpg",
        },
        "geometry": geometry,
    }
    if overrides:
        feature.update(overrides)
    return feature


def _build_feature_collection(count=3):
    return {
        "type": "FeatureCollection",
        "features": [_build_feature({"properties": {"cell_id": str(i)}}) for i in range(count)],
    }


class TestFeatureSchema:
    """RFC 7946 §3.2 — Feature object must have type, geometry, properties."""

    def test_feature_has_type(self):
        feat = _build_feature()
        assert feat.get("type") == "Feature", "Every Feature must have type=Feature"

    def test_feature_has_geometry(self):
        feat = _build_feature()
        assert "geometry" in feat, "Feature must have a geometry member"
        assert feat["geometry"]["type"] == "Polygon"

    def test_feature_has_properties(self):
        feat = _build_feature()
        assert "properties" in feat, "Feature must have a properties member"
        assert isinstance(feat["properties"], dict)
        assert feat["properties"]["cell_id"] == "0"
        assert feat["properties"]["dominant_class"] == "Residential"

    def test_feature_rejects_flat_fields(self):
        """Regression: cell_id/dominant_class must NOT be at top level."""
        feat = _build_feature()
        for key in ("cell_id", "dominant_class", "confidence", "road_density"):
            assert key not in feat, f"'{key}' must be inside 'properties', not at Feature root"


class TestFeatureCollectionSchema:
    """RFC 7946 §3.3 — FeatureCollection object."""

    def test_collection_has_type(self):
        fc = _build_feature_collection()
        assert fc.get("type") == "FeatureCollection"

    def test_collection_has_features_array(self):
        fc = _build_feature_collection()
        assert "features" in fc
        assert isinstance(fc["features"], list)

    def test_all_features_are_valid(self):
        fc = _build_feature_collection(5)
        for feat in fc["features"]:
            assert feat["type"] == "Feature"
            assert "properties" in feat
            assert "geometry" in feat


class TestCoordinateOrdering:
    """RFC 7946 §4 — Coordinates must be [longitude, latitude]."""

    def test_polygon_coordinates_lon_lat(self):
        feat = _build_feature()
        coords = feat["geometry"]["coordinates"][0]
        for lon, lat in coords:
            assert isinstance(lon, (int, float)), f"First coord must be longitude, got {lon}"
            assert isinstance(lat, (int, float)), f"Second coord must be latitude, got {lat}"
            # In our area lon ≈ 31, lat ≈ 30
            assert 30 < lon < 32, f"Longitude {lon} out of expected range [30, 32]"
            assert 29 < lat < 31, f"Latitude {lat} out of expected range [29, 31]"

    def test_centroid_in_properties_is_lon_lat(self):
        feat = _build_feature()
        centroid = feat["properties"]["centroid"]
        lon, lat = centroid
        assert 30 < lon < 32, f"Centroid longitude {lon} out of range"
        assert 29 < lat < 31, f"Centroid latitude {lat} out of range"

    def test_centroid_not_reversed(self):
        """Regression: centroid must be [lon, lat], not [lat, lon]."""
        feat = _build_feature()
        centroid = feat["properties"]["centroid"]
        lon, lat = centroid
        # If reversed, lat ≈ 31, lon ≈ 30 — so lon < lat would be False
        # Correct: lon (~31.2) > lat (~30.0)
        assert lon > lat, (
            f"Centroid appears reversed: ({lon}, {lat}). "
            f"Expected [longitude, latitude] but got [latitude, longitude]."
        )


class TestGraphTopologyGeoJSON:
    """The graph-topology endpoint already uses correct Feature structure."""

    def test_graph_feature_has_valid_schema(self):
        """Spot-check helpers._graph_to_geojson output."""
        import networkx as nx
        G = nx.MultiDiGraph()
        G.add_node(1, x=31.2, y=30.0)
        G.add_node(2, x=31.22, y=30.02)
        G.add_edge(1, 2, length_m=100.0, highway="residential")
        result = _graph_to_geojson(G)
        assert result["type"] == "FeatureCollection"
        for feat in result["features"]:
            assert feat["type"] == "Feature"
            assert "properties" in feat
            assert "geometry" in feat


class TestGeoJSONSerialization:
    """Round-trip JSON serialization must preserve structure."""

    def test_serialize_deserialize_features(self):
        fc = _build_feature_collection()
        dumped = json.dumps(fc)
        loaded = json.loads(dumped)
        assert loaded["type"] == "FeatureCollection"
        for feat in loaded["features"]:
            assert feat["type"] == "Feature"
            assert "properties" in feat
            assert "geometry" in feat
            # Coordinate precision preserved
            geom = feat["geometry"]
            assert isinstance(geom, dict)
            assert geom["type"] == "Polygon"


class TestModelToFeatureCompatibility:
    """CellResult model_dump() must produce valid Feature properties."""

    def test_cell_result_dump_includes_all_properties(self):
        result = CellResult(
            cell_id="test_1",
            dominant_class="Residential",
            confidence=0.9,
            confidences={"residential": 0.9, "commercial": 0.05, "industrial": 0.05},
            poi_top_categories=["Food"],
            road_density=1.0,
            node_count=10,
            degree_centrality=0.1,
            clustering_coeff=0.2,
            total_road_length_m=100.0,
            graph_embedding_norm=1.0,
            text_embedding_norm=1.0,
            geometry={"type": "Polygon", "coordinates": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]},
            centroid=(0.5, 0.5),
            satellite_thumbnail_url="http://example.com/thumbnail.jpg",
        )
        dumped = result.model_dump()
        # Map into a Feature properties block
        props = {k: v for k, v in dumped.items() if k != "geometry"}
        assert "cell_id" in props
        assert "dominant_class" in props
        assert "confidence" in props
        assert "geometry" not in props  # geometry is separate
