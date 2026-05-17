"""
Infrastructure layer for data loading.
Provides functions to load and project spatial data from CSV files.
"""

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point


def load_project_data(csv_path: str) -> gpd.GeoDataFrame:
    df = pd.read_csv(csv_path)

    # Debug outputs
    print("Columns in dataset:", df.columns)
    print("Label distribution:\n", df["label"].value_counts())

    # Create geometries
    geometry = [Point(xy) for xy in zip(df.X, df.Y)]
    gdf = gpd.GeoDataFrame(df, crs="EPSG:4326", geometry=geometry)

    # Project to metric CRS
    gdf = gdf.to_crs("EPSG:32636")

# AI-2 CHECK (IMPORTANT)
    X = gdf[["X", "Y", "place_type", "category", "text_des"]]
    y = gdf["label"]

    print("X shape:", X.shape)
    print("y distribution:\n", y.value_counts())



    return gdf


#  RUN SECTION (IMPORTANT FIXED PATH)
if __name__ == "__main__":
    csv_path = r"C:\Users\YOUSIF\Desktop\MLLM_Geo_Ai-fresh-start\MLLM_Geo_Ai-fresh-start\data\raw\project.csv"

    gdf = load_project_data(csv_path)

    print("\n✔ GeoDataFrame created successfully")
    print(gdf.head())