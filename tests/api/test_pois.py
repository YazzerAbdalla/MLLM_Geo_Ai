import pytest
from app.infrastructure.job_store import job_store

def test_get_pois_not_found(client):
    response = client.get("/api/v1/grid/unknown/pois")
    assert response.status_code == 404

def test_get_pois_empty(client, monkeypatch):
    monkeypatch.setattr(job_store, "get_grid", lambda x: {"gdf": []})
    # mock os.path.exists to return False
    import os
    monkeypatch.setattr(os.path, "exists", lambda x: False)
    
    response = client.get("/api/v1/grid/grid_1/pois")
    assert response.status_code == 200
    assert response.json() == []

def test_get_pois_success(client, monkeypatch):
    monkeypatch.setattr(job_store, "get_grid", lambda x: {"gdf": []})
    import os
    monkeypatch.setattr(os.path, "exists", lambda x: True)
    
    # Mock geopandas
    import geopandas as gpd
    from shapely.geometry import Point
    
    gdf = gpd.GeoDataFrame({
        "name": ["Restaurant"],
        "amenity": ["Food"],
        "geometry": [Point(31.21, 30.01)]
    })
    monkeypatch.setattr(gpd, "read_file", lambda x: gdf)
    
    response = client.get("/api/v1/grid/grid_1/pois")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Restaurant"
    assert data[0]["category"] == "Food"
    assert data[0]["lat"] == 30.01
    assert data[0]["lng"] == 31.21
