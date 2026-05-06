"""
 * Tests for the Satellite Image Loader.
 """
import pytest
from unittest.mock import patch, MagicMock
import app.infrastructure.satellite_loader as satellite_module
from app.infrastructure.satellite_loader import SatelliteImageLoader
import geopandas as gpd
from shapely.geometry import Polygon


@patch('app.infrastructure.satellite_loader.requests')
@patch('app.infrastructure.satellite_loader.ee.Image')
def test_satellite_loader(mock_ee_image, mock_requests):
    # Skip if ee not available/initialized
    if not hasattr(satellite_module, 'ee') or satellite_module.ee is None:
        pytest.skip("GEE not available")
    
    # Mock the request response  
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b'mock_image_data'
    mock_requests.get.return_value = mock_response
    
    loader = SatelliteImageLoader()
    
    # Create a dummy grid cell
    poly = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    grid_gdf = gpd.GeoDataFrame(geometry=[poly], crs="EPSG:4326")
    grid_gdf['cell_id'] = [42]
    
    with patch('builtins.open', MagicMock()):
        result = loader.download_for_grid(grid_gdf, grid_id='test_grid')
    
    # Just verify it runs without error
    assert result is not None
