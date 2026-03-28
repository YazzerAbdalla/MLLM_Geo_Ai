"""
 * Domain layer for spatial services.
 * Contains logic for grid generation and spatial join operations.
 """
import geopandas as gpd
import numpy as np
from shapely.geometry import box

def generate_grid(bounds: tuple, cell_size_m: float = 500.0) -> gpd.GeoDataFrame:
    """
    * Generate a square grid of polygons covering the given bounds.
    *
    * @param {tuple} bounds - (min_x, min_y, max_x, max_y) in metric CRS
    * @param {float} cell_size_m - Dimensions of each side of the square cell in meters
    * @returns {gpd.GeoDataFrame} A GeoDataFrame containing the generated grid cells
    """
    min_x, min_y, max_x, max_y = bounds
    
    # Get the number of columns and rows
    cols = int(np.ceil((max_x - min_x) / cell_size_m))
    rows = int(np.ceil((max_y - min_y) / cell_size_m))
    
    # List to store the grid cells
    grid_cells = []
    
    # Create the polygons
    for i in range(cols):
        for k in range(rows):
            x1 = min_x + i * cell_size_m
            x2 = x1 + cell_size_m
            y1 = min_y + k * cell_size_m
            y2 = y1 + cell_size_m
            grid_cells.append(box(x1, y1, x2, y2))
            
    # Create a GeoDataFrame
    # We assume 'bounds' is in a metric CRS (like UTM 36N)
    gdf = gpd.GeoDataFrame(geometry=grid_cells, crs="EPSG:32636")
    
    # Add a unique cell_id (for aggregation later)
    gdf['cell_id'] = range(len(gdf))
    
    return gdf

def join_points_to_grid(points_gdf: gpd.GeoDataFrame, grid_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    * Perform an optimized spatial join between points and grid cells.
    *
    * @param {gpd.GeoDataFrame} points_gdf - GeoDataFrame containing point data
    * @param {gpd.GeoDataFrame} grid_gdf - GeoDataFrame containing grid cell polygons
    * @returns {gpd.GeoDataFrame} Points with an added 'cell_id' column from the grid join
    """
    # points_gdf and grid_gdf MUST have the same CRS.
    if points_gdf.crs != grid_gdf.crs:
        points_gdf = points_gdf.to_crs(grid_gdf.crs)
        
    # Use sjoin for optimized spatial join
    joined = gpd.sjoin(points_gdf, grid_gdf[['geometry', 'cell_id']], how='inner', predicate='within')
    
    return joined
