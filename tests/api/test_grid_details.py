import pytest
from app.models.grid import Grid
from app.infrastructure.job_store import job_store
import geopandas as gpd
from shapely.geometry import Polygon

# Mock db for grid details?
# The endpoint gets grid info. Let's see what the implementation will be.
def test_get_grid_details_not_found(client):
    response = client.get("/api/v1/grid/unknown/details")
    assert response.status_code == 404

def test_get_grid_details_success(client, monkeypatch):
    # Mock job_store.get_grid
    poly = Polygon([(0,0), (0,1), (1,1), (1,0), (0,0)])
    gdf = gpd.GeoDataFrame({"geometry": [poly]}, crs="EPSG:4326")
    def mock_get_grid(grid_id):
        if grid_id == "grid_1":
            return {"gdf": gdf, "bbox": [0,0,1,1]}
        return None
    monkeypatch.setattr(job_store, "get_grid", mock_get_grid)
    
    response = client.get("/api/v1/grid/grid_1/details")
    assert response.status_code == 200
    data = response.json()
    assert data["grid_id"] == "grid_1"
    assert data["cell_count"] == 1
