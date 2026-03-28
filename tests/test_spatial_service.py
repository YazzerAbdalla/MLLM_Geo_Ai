"""
 * Unit tests for the spatial service domain logic.
 * Ensures grid generation and other spatial operations work correctly.
 """
import pytest
import geopandas as gpd
from shapely.geometry import Point
from app.domain.spatial_service import generate_grid

def test_generate_grid_dimensions():
    """
    * Tests that generate_grid creates the correct number of cells and dimensions.
    * Uses a mock 1km x 1km area in Cairo.
    """
    # Define a small area (approximately 1km x 1km) in Cairo
    # Using UTM 36N (EPSG:32636) for metrics
    # Cairo is around Lon 31.2, Lat 30.0
    
    # Mock bounds in EPSG:32636
    # 325000, 3320000 -> 326000, 3321000
    bounds = (325000, 3320000, 326000, 3321000)
    grid_gdf = generate_grid(bounds, cell_size_m=500)
    
    # Area of each cell should be approx 500 * 500 = 250,000 sq m
    for poly in grid_gdf.geometry:
        assert abs(poly.area - 250000) < 1.0 # Tolerance for float precision
        
    # Check that it covers the bounds (2x2 grid for 1km area)
    assert len(grid_gdf) == 4
