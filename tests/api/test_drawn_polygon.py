import pytest
from app.interfaces.api import LoadAreaRequest

def test_load_area_polygon_test():
    req = LoadAreaRequest(
        area_geometry={"type": "Polygon", "coordinates": [[[0,0], [0,1], [1,1], [1,0], [0,0]]]},
        grid_size=500
    )
    assert req.area_geometry is not None

def test_invalid_polygon_test(client):
    response = client.post("/api/v1/load-area", json={
        "area_geometry": {"type": "Invalid", "coordinates": []},
        "grid_size": 500
    })
    assert response.status_code == 400

def test_load_area_bbox_test():
    req = LoadAreaRequest(
        bbox=[0,0,1,1],
        grid_size=500
    )
    assert req.bbox == [0,0,1,1]
