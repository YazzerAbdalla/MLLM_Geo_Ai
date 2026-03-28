"""
 * Infrastructure layer for data loading.
 * Provides functions to load and project spatial data from CSV files.
 """
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

def load_project_data(csv_path: str) -> gpd.GeoDataFrame:
    """
    * Load project.csv data into a GeoDataFrame and project to a metric CRS.
    *
    * @param {str} csv_path - Path to the project CSV data file
    * @returns {gpd.GeoDataFrame} A GeoDataFrame with points projected to EPSG:32636
    """
    df = pd.read_csv(csv_path)
    # Convert points to geometries. Cairo is in UTM 36N (EPSG:32636) for metrics.
    # We load in WGS84 first (EPSG:4326) and then project to 32636.
    geometry = [Point(xy) for xy in zip(df.X, df.Y)]
    gdf = gpd.GeoDataFrame(df, crs="EPSG:4326", geometry=geometry)
    
    # Project to metric CRS for spatial calculations (500m grids)
    gdf = gdf.to_crs("EPSG:32636")
    return gdf
