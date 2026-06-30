import pytest
import geopandas as gpd
from shapely.geometry import box


def _make_test_gdf():
    cells = []
    cats = []
    for i in range(5):
        cells.append(box(30.0 + i * 0.01, 30.0, 30.01 + i * 0.01, 30.01))
        cats.append(["shop", "mall"] if i < 3 else ["school"])
    gdf = gpd.GeoDataFrame({"cell_id": list(range(5)), "poi_categories": cats, "geometry": cells}, crs="EPSG:4326")
    return gdf


def test_query_success_fallback(client, monkeypatch):
    from app.infrastructure.job_store import job_store
    gdf = _make_test_gdf()
    monkeypatch.setattr(job_store, "get_grid", lambda x: {"gdf": gdf})

    response = client.post("/api/v1/query", json={"question": "find shop", "grid_id": "grid_1"})
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] is not None
    assert data["query_type"] == "commercial"
    assert data["confidence"] is None
    assert len(data["matched_cells"]) == 3


def test_query_empty_question(client):
    response = client.post("/api/v1/query", json={"question": "   ", "grid_id": "grid_1"})
    assert response.status_code == 400


def test_query_invalid_grid(client, monkeypatch):
    from app.infrastructure.job_store import job_store
    monkeypatch.setattr(job_store, "get_grid", lambda x: None)

    response = client.post("/api/v1/query", json={"question": "find shop", "grid_id": "invalid_grid"})
    assert response.status_code == 404


def test_query_classification_mode(client, monkeypatch):
    from app.infrastructure.job_store import job_store
    gdf = _make_test_gdf()
    monkeypatch.setattr(job_store, "get_grid", lambda x: {"gdf": gdf})
    monkeypatch.setattr(job_store, "get_classify_result", lambda x: [
        {
            "type": "Feature",
            "properties": {
                "cell_id": "0",
                "dominant_class": "Commercial",
                "confidence": 0.92,
                "centroid": [30.005, 30.005],
                "road_density": 0.5,
                "poi_top_categories": ["shop", "mall"]
            },
            "geometry": {"type": "Polygon", "coordinates": [[[30.0, 30.0], [30.01, 30.0], [30.01, 30.01], [30.0, 30.01], [30.0, 30.0]]]}
        },
        {
            "type": "Feature",
            "properties": {
                "cell_id": "1",
                "dominant_class": "Commercial",
                "confidence": 0.88,
                "centroid": [30.015, 30.005],
                "road_density": 0.3,
                "poi_top_categories": ["mall"]
            },
            "geometry": {"type": "Polygon", "coordinates": [[[30.01, 30.0], [30.02, 30.0], [30.02, 30.01], [30.01, 30.01], [30.01, 30.0]]]}
        }
    ])

    response = client.post("/api/v1/query", json={"question": "shop", "grid_id": "grid_1"})
    assert response.status_code == 200
    data = response.json()
    assert data["query_type"] == "commercial"
    assert data["confidence"] == pytest.approx(0.9, abs=0.02)
    assert len(data["matched_cells"]) == 2
    for cell in data["matched_cells"]:
        assert cell["dominant_class"] == "Commercial"
        assert cell["confidence"] is not None
        assert len(cell["centroid"]) == 2


def test_query_fallback_no_match(client, monkeypatch):
    from app.infrastructure.job_store import job_store
    gdf = _make_test_gdf()
    monkeypatch.setattr(job_store, "get_grid", lambda x: {"gdf": gdf})

    response = client.post("/api/v1/query", json={"question": "factory", "grid_id": "grid_1"})
    assert response.status_code == 200
    data = response.json()
    assert data["query_type"] == "industrial"
    assert data["confidence"] is None
    assert len(data["matched_cells"]) == 0
