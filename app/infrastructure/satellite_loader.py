"""
 * Satellite Imagery Collection using Google Earth Engine.
 """
import ee
import requests
import io
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
import geopandas as gpd

class SatelliteImageLoader:
    """
     * Loader for Google Earth Engine satellite imagery.
     * Assumes ee.Initialize() has been called during app startup.
     """
    def __init__(self):
        self.base_output_dir = "data/thumbnails"

    def _download_patch(self, cell_id, geometry, output_dir, radius_m=250):
        """
         * Download a single image patch for a given geometry.
         * @param {int} cell_id - The ID of the grid cell
         * @param {shapely.geometry.Polygon} geometry - The polygon geometry
         * @param {str} output_dir - The directory to save the image
         * @param {int} radius_m - Buffer radius in meters
         """
        save_path = os.path.join(output_dir, f"cell_{cell_id}.png")
        if os.path.exists(save_path):
            return save_path

        lon, lat = geometry.centroid.x, geometry.centroid.y
        region = ee.Geometry.Point([lon, lat]).buffer(radius_m).bounds()
        
        # Get median Sentinel-2 image (cloud filtered)
        image = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
            .filterBounds(region) \
            .filterDate('2023-01-01', '2023-12-31') \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
            .median() \
            .clip(region)
            
        # Visualize to convert to 8-bit RGB before downloading
        vis_image = image.visualize(bands=['B4', 'B3', 'B2'], min=0, max=3000)
        
        try:
            url = vis_image.getDownloadURL({
                'region': region,
                'dimensions': [256, 256],
                'format': 'png'
            })
            
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                img_path = os.path.join(output_dir, f"cell_{cell_id}.png")
                with open(img_path, 'wb') as f:
                    f.write(response.content)
                return img_path
            else:
                print(f"Failed cell {cell_id}: HTTP {response.status_code}")
                return None
        except Exception as e:
            print(f"Error downloading cell {cell_id}: {e}")
            return None

    def download_for_grid(self, grid_gdf: gpd.GeoDataFrame, grid_id: str = None, output_dir: str = "data/sat_images", radius_m=250):
        """
         * Download satellite images for an entire grid.
         * @param {gpd.GeoDataFrame} grid_gdf - GeoDataFrame containing grid cells
         * @param {str} grid_id - The unique identifier for the grid (ignored, kept for API compat)
         * @param {str} output_dir - The directory to save images (default: data/sat_images)
         * @param {int} radius_m - Buffer radius around centroid
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Convert CRS to EPSG:4326 for Earth Engine (lon/lat)
        if grid_gdf.crs and grid_gdf.crs != "EPSG:4326":
            grid_gdf_4326 = grid_gdf.to_crs("EPSG:4326")
        else:
            grid_gdf_4326 = grid_gdf

        # Use ThreadPoolExecutor for parallel downloading
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for idx, cell in grid_gdf_4326.iterrows():
                # Prefer 'cell_id' column if it exists, else use index
                cell_id = cell.get('cell_id', idx)
                futures.append(
                    executor.submit(self._download_patch, cell_id, cell.geometry, output_dir, radius_m)
                )
            
            for future in futures:
                future.result() # Wait for completion
                
        return output_dir
