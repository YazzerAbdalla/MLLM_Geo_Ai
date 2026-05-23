"""
 * Infrastructure layer for data loading.
 * Provides functions to load and project spatial data from CSV files.
"""
import os
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

def load_project_data(csv_path: str) -> gpd.GeoDataFrame:
    """
     * Load project data from CSV, construct geometries, and project to metric CRS.
     *
     * @param {str} csv_path - The path to the project CSV file
     * @returns {gpd.GeoDataFrame} Projected GeoDataFrame containing all columns and geometries
    """
    # // Read CSV file from the specified path
    df = pd.read_csv(csv_path)

    # // Debug outputs for tracking execution
    print("Columns in dataset:", df.columns)
    print("Label distribution:\n", df["label"].value_counts())

    # // Create geometry Points from coordinates
    geometry = [Point(xy) for xy in zip(df.X, df.Y)]
    gdf = gpd.GeoDataFrame(df, crs="EPSG:4326", geometry=geometry)

    # // Project to metric CRS (Universal Transverse Mercator for Egypt)
    gdf = gdf.to_crs("EPSG:32636")

    # // AI-2 CHECK (IMPORTANT)
    # // Verify loader holds correct feature columns and label
    X = gdf[["X", "Y", "place_type", "category", "text_des"]]
    y = gdf["label"]

    print("X shape:", X.shape)
    print("y distribution:\n", y.value_counts())

    return gdf

# // Run section for manual execution and testing
if __name__ == "__main__":
    # // Use a relative path to ensure portability across different systems
    csv_path = os.path.join("data", "raw", "project.csv")

    gdf = load_project_data(csv_path)

    print("\n[OK] GeoDataFrame created successfully")
    # // Drop text_des when printing to console to avoid cp1252 encoding errors
    print(gdf.drop(columns=["text_des"]).head())