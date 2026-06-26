import pytest
import pandas as pd
import numpy as np
from app.infrastructure import poi_cache


def test_returns_200_with_valid_geojson(client, monkeypatch):
    """Returns 200 with valid GeoJSON FeatureCollection containing metadata and features."""
    df = pd.DataFrame({
        "X": [31.235, 31.238],
        "Y": [30.044, 30.047],
        "osm_id": ["1001", "1002"],
        "name": ["Cafe", "Shop"],
        "category": ["food", "retail"],
        "place_type": ["cafe", "store"],
        "label": [1, 2]
    })
    monkeypatch.setattr(poi_cache, "get_poi_cache", lambda: df)

    response = client.get("/api/v1/internal/poi-heatmap")
    assert response.status_code == 200
    data = response.json()

    assert data["type"] == "FeatureCollection"
    assert data["metadata"]["total_pois"] == 2
    assert data["metadata"]["source"] == "project.csv"
    assert len(data["features"]) == 2

    feature = data["features"][0]
    assert feature["type"] == "Feature"
    assert feature["geometry"]["type"] == "Point"
    assert len(feature["geometry"]["coordinates"]) == 2
    assert feature["properties"]["osm_id"] == "1001"
    assert feature["properties"]["name"] == "Cafe"
    assert feature["properties"]["category"] == "food"
    assert feature["properties"]["place_type"] == "cafe"
    assert feature["properties"]["label"] == 1
    assert feature["properties"]["weight"] == 1


def test_empty_cache_returns_empty_feature_collection(client, monkeypatch):
    """When cache is empty, returns 200 with empty features and total_pois=0."""
    monkeypatch.setattr(poi_cache, "get_poi_cache", lambda: None)

    response = client.get("/api/v1/internal/poi-heatmap")
    assert response.status_code == 200
    data = response.json()

    assert data["type"] == "FeatureCollection"
    assert data["metadata"]["total_pois"] == 0
    assert data["metadata"]["source"] == "project.csv"
    assert data["features"] == []


def test_invalid_coordinates_removed(client, monkeypatch):
    """Null and out-of-range coordinates are removed."""
    df = pd.DataFrame({
        "X": [31.235, np.nan, 200.0, 31.238],
        "Y": [30.044, 30.045, 30.046, np.nan],
        "osm_id": ["1001", "1002", "1003", "1004"],
        "name": ["Valid", "NullX", "OutLng", "NullY"],
        "category": ["a", "b", "c", "d"],
        "place_type": ["x", "y", "z", "w"],
        "label": [1, 2, 3, 4]
    })
    monkeypatch.setattr(poi_cache, "get_poi_cache", lambda: df)

    response = client.get("/api/v1/internal/poi-heatmap")
    assert response.status_code == 200
    data = response.json()

    assert data["metadata"]["total_pois"] == 1
    names = [f["properties"]["name"] for f in data["features"]]
    assert "Valid" in names
    assert "NullX" not in names
    assert "OutLng" not in names
    assert "NullY" not in names


def test_osm_id_deduplication(client, monkeypatch):
    """Duplicate osm_ids are removed (first kept)."""
    df = pd.DataFrame({
        "X": [31.235, 31.236, 31.237],
        "Y": [30.044, 30.045, 30.046],
        "osm_id": ["1001", "1001", "1002"],
        "name": ["First", "Duplicate", "Second"],
        "category": ["a", "b", "c"],
        "place_type": ["x", "y", "z"],
        "label": [1, 2, 3]
    })
    monkeypatch.setattr(poi_cache, "get_poi_cache", lambda: df)

    response = client.get("/api/v1/internal/poi-heatmap")
    assert response.status_code == 200
    data = response.json()

    assert data["metadata"]["total_pois"] == 2
    names = [f["properties"]["name"] for f in data["features"]]
    assert "First" in names
    assert "Duplicate" not in names
    assert "Second" in names


def test_null_osm_id_preserved(client, monkeypatch):
    """Rows with null osm_id are not deduplicated against each other."""
    df = pd.DataFrame({
        "X": [31.235, 31.236],
        "Y": [30.044, 30.045],
        "osm_id": [np.nan, np.nan],
        "name": ["NoID1", "NoID2"],
        "category": ["a", "b"],
        "place_type": ["x", "y"],
        "label": [1, 2]
    })
    monkeypatch.setattr(poi_cache, "get_poi_cache", lambda: df)

    response = client.get("/api/v1/internal/poi-heatmap")
    assert response.status_code == 200
    data = response.json()

    assert data["metadata"]["total_pois"] == 2
