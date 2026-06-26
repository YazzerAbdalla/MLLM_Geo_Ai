import pytest
import pandas as pd
import numpy as np
from app.infrastructure import poi_cache


VALID_POLYGON = {
    "geometry": {
        "type": "Polygon",
        "coordinates": [[[31.20, 30.00], [31.22, 30.00], [31.22, 30.02],
                          [31.20, 30.02], [31.20, 30.00]]]
    }
}


def _make_df(rows: list) -> pd.DataFrame:
    return pd.DataFrame(rows)


class TestValidPolygon:
    def test_returns_analysis_with_matching_pois(self, client, monkeypatch):
        df = _make_df([
            {"X": 31.21, "Y": 30.01, "osm_id": "1", "name": "Cafe",
             "category": "food", "place_type": "cafe", "label": 1},
            {"X": 31.215, "Y": 30.015, "osm_id": "2", "name": "Shop",
             "category": "retail", "place_type": "store", "label": 2},
            {"X": 31.205, "Y": 30.005, "osm_id": "3", "name": "School",
             "category": "education", "place_type": "school", "label": 3},
        ])
        monkeypatch.setattr(poi_cache, "get_poi_cache", lambda: df)

        response = client.post("/api/v1/internal/poi-analysis", json=VALID_POLYGON)

        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "FeatureCollection"
        assert data["analysis"]["total_pois"] == 3
        assert data["analysis"]["poi_density"] > 0
        assert data["analysis"]["truncated"] is False
        assert data["analysis"]["returned_pois"] == 3
        assert len(data["features"]) == 3

        names = [f["name"] for f in data["features"]]
        assert "Cafe" in names
        assert "Shop" in names
        assert "School" in names

        cats = {item["category"] for item in data["analysis"]["top_categories"]}
        assert "food" in cats
        assert "retail" in cats
        assert "education" in cats

    def test_boundary_point_included(self, client, monkeypatch):
        point_on_edge = {"X": 31.20, "Y": 30.00, "osm_id": "1", "name": "Edge",
                         "category": "test", "place_type": "pt", "label": 0}
        point_inside = {"X": 31.21, "Y": 30.01, "osm_id": "2", "name": "Inside",
                        "category": "test", "place_type": "pt", "label": 0}
        df = _make_df([point_on_edge, point_inside])
        monkeypatch.setattr(poi_cache, "get_poi_cache", lambda: df)

        response = client.post("/api/v1/internal/poi-analysis", json=VALID_POLYGON)

        assert response.status_code == 200
        data = response.json()
        assert data["analysis"]["total_pois"] == 2
        names = [f["name"] for f in data["features"]]
        assert "Edge" in names
        assert "Inside" in names


class TestEmptyResult:
    def test_polygon_with_zero_pois(self, client, monkeypatch):
        df = _make_df([
            {"X": 31.50, "Y": 30.50, "osm_id": "1", "name": "Far",
             "category": "x", "place_type": "x", "label": 0},
        ])
        monkeypatch.setattr(poi_cache, "get_poi_cache", lambda: df)

        response = client.post("/api/v1/internal/poi-analysis", json=VALID_POLYGON)

        assert response.status_code == 200
        data = response.json()
        assert data["analysis"]["total_pois"] == 0
        assert data["analysis"]["poi_density"] == 0.0
        assert data["analysis"]["truncated"] is False
        assert data["analysis"]["returned_pois"] == 0
        assert data["features"] == []

    def test_none_cache_returns_empty(self, client, monkeypatch):
        monkeypatch.setattr(poi_cache, "get_poi_cache", lambda: None)

        response = client.post("/api/v1/internal/poi-analysis", json=VALID_POLYGON)

        assert response.status_code == 200
        data = response.json()
        assert data["analysis"]["total_pois"] == 0
        assert data["features"] == []


class TestReverseGeocoding:
    def test_disabled_by_default(self, client, monkeypatch):
        df = _make_df([
            {"X": 31.21, "Y": 30.01, "osm_id": "1", "name": "Cafe",
             "category": "food", "place_type": "cafe", "label": 0},
        ])
        monkeypatch.setattr(poi_cache, "get_poi_cache", lambda: df)

        response = client.post("/api/v1/internal/poi-analysis", json=VALID_POLYGON)

        assert response.status_code == 200
        data = response.json()
        assert data["analysis"]["reverse_geocoding"] is None

    def test_enabled_returns_location(self, client, monkeypatch):
        df = _make_df([
            {"X": 31.21, "Y": 30.01, "osm_id": "1", "name": "Cafe",
             "category": "food", "place_type": "cafe", "label": 0},
        ])
        monkeypatch.setattr(poi_cache, "get_poi_cache", lambda: df)

        import app.application.poi_analysis_service as svc
        original = svc._reverse_geocode

        def mock_reverse_geocode(centroid):
            return {"area_name": "Tanta, Egypt", "city": "Tanta", "country": "Egypt"}

        monkeypatch.setattr(svc, "_reverse_geocode", mock_reverse_geocode)

        body = {**VALID_POLYGON, "include_location": True}
        response = client.post("/api/v1/internal/poi-analysis", json=body)

        assert response.status_code == 200
        data = response.json()
        geo = data["analysis"]["reverse_geocoding"]
        assert geo["area_name"] == "Tanta, Egypt"
        assert geo["city"] == "Tanta"
        assert geo["country"] == "Egypt"

    def test_failure_returns_null_fields(self, client, monkeypatch):
        df = _make_df([
            {"X": 31.21, "Y": 30.01, "osm_id": "1", "name": "Cafe",
             "category": "food", "place_type": "cafe", "label": 0},
        ])
        monkeypatch.setattr(poi_cache, "get_poi_cache", lambda: df)

        import app.application.poi_analysis_service as svc

        def mock_fail(centroid):
            return {"area_name": None, "city": None, "country": None}

        monkeypatch.setattr(svc, "_reverse_geocode", mock_fail)

        body = {**VALID_POLYGON, "include_location": True}
        response = client.post("/api/v1/internal/poi-analysis", json=body)

        assert response.status_code == 200
        geo = response.json()["analysis"]["reverse_geocoding"]
        assert geo["area_name"] is None
        assert geo["city"] is None
        assert geo["country"] is None


class TestTruncation:
    def test_truncates_at_max_pois(self, client, monkeypatch):
        rows = []
        for i in range(1500):
            lng = 31.20 + (i % 100) * 0.0002
            lat = 30.00 + (i // 100) * 0.0002
            rows.append({
                "X": lng, "Y": lat, "osm_id": str(i), "name": f"POI_{i}",
                "category": "test", "place_type": "point", "label": 0,
            })
        df = _make_df(rows)
        monkeypatch.setattr(poi_cache, "get_poi_cache", lambda: df)

        response = client.post("/api/v1/internal/poi-analysis", json=VALID_POLYGON)

        assert response.status_code == 200
        data = response.json()
        assert data["analysis"]["total_pois"] == 1500
        assert data["analysis"]["returned_pois"] == 1000
        assert data["analysis"]["truncated"] is True
        assert len(data["features"]) == 1000


class TestValidation:
    def test_invalid_geojson_type(self, client):
        body = {"geometry": {"type": "Invalid", "coordinates": [[]]}}
        response = client.post("/api/v1/internal/poi-analysis", json=body)
        assert response.status_code == 400

    def test_unsupported_geometry_type(self, client):
        body = {"geometry": {"type": "Point", "coordinates": [31.0, 30.0]}}
        response = client.post("/api/v1/internal/poi-analysis", json=body)
        assert response.status_code == 400

    def test_empty_coordinates(self, client):
        body = {"geometry": {"type": "Polygon", "coordinates": []}}
        response = client.post("/api/v1/internal/poi-analysis", json=body)
        assert response.status_code == 400

    def test_missing_geometry(self, client):
        response = client.post("/api/v1/internal/poi-analysis", json={})
        assert response.status_code == 422

    def test_none_geometry(self, client):
        response = client.post("/api/v1/internal/poi-analysis",
                               json={"geometry": None})
        assert response.status_code == 422
