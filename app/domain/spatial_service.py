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
    * @param {tuple} bounds - (min_x, min_y, max_x, max_y) in degrees (WGS84) or meters (UTM)
    * @param {float} cell_size_m - Dimensions of each side of the square cell in meters
    * @returns {gpd.GeoDataFrame} A GeoDataFrame containing the generated grid cells
    """
    min_x, min_y, max_x, max_y = bounds
    
    # Detect if coordinates are in degrees (small values < 180) or meters (> 180)
    max_range = max(max_x - min_x, max_y - min_y)
    
    if max_range < 180:
        # Assume WGS84 (degrees), convert meters to degrees
        # 1 degree ≈ 111km at equator
        cell_size_deg = cell_size_m / 111000.0
        cols = int(np.ceil((max_x - min_x) / cell_size_deg))
        rows = int(np.ceil((max_y - min_y) / cell_size_deg))
        
        grid_cells = []
        for i in range(cols):
            for k in range(rows):
                x1 = min_x + i * cell_size_deg
                x2 = x1 + cell_size_deg
                y1 = min_y + k * cell_size_deg
                y2 = y1 + cell_size_deg
                grid_cells.append(box(x1, y1, x2, y2))
        
        gdf = gpd.GeoDataFrame(geometry=grid_cells, crs="EPSG:4326")
    else:
        # Assume metric CRS (like UTM 36N)
        cols = int(np.ceil((max_x - min_x) / cell_size_m))
        rows = int(np.ceil((max_y - min_y) / cell_size_m))
        
        grid_cells = []
        for i in range(cols):
            for k in range(rows):
                x1 = min_x + i * cell_size_m
                x2 = x1 + cell_size_m
                y1 = min_y + k * cell_size_m
                y2 = y1 + cell_size_m
                grid_cells.append(box(x1, y1, x2, y2))
        
        gdf = gpd.GeoDataFrame(geometry=grid_cells, crs="EPSG:32636")
    
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

def create_multimodal_feature(poi_embedding: np.ndarray,
                               image_embedding: np.ndarray,
                               graph_features: np.ndarray) -> np.ndarray:
    """
     * Concatenate different modality embeddings into a single feature vector.
     *
     * @param {np.ndarray} poi_embedding - POI Text Embedding
     * @param {np.ndarray} image_embedding - Image CNN Embedding
     * @param {np.ndarray} graph_features - Road Network Features
     * @returns {np.ndarray} Fused feature vector
     """
    return np.concatenate([poi_embedding, image_embedding, graph_features])
