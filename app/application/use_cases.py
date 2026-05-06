"""
 * Application layer use cases for the MLLM-Geo-AI pipeline.
 * Contains the orchestration logic for loading data, generating grids, and running classification.
 """
import os
import pandas as pd
import geopandas as gpd
import numpy as np
from app.infrastructure.data_loader import load_project_data
from app.domain.spatial_service import generate_grid, join_points_to_grid
from app.infrastructure.ai_model import Embedder, aggregate_cell_embeddings

def run_classification_pipeline(csv_path: str):
    """
    * Orchestrates the Geo-AI pipeline:
    * 1. Load Points (project.csv)
    * 2. Define bounds and Generate 500m Grid
    * 3. Spatial Join Points with Grid
    * 4. Embed Descriptions
    * 5. Aggregate Embeddings (Cell Story)
    * 6. Classification (Mock/Simple Logic)
    *
    * @param {str} csv_path - Path to the project CSV data file
    * @returns {list} List of classification results per grid cell
    """
    # 1. Load Points
    points_gdf = load_project_data(csv_path)
    
    # 2. Get bounds of points and generate 500m grid
    # Bounds are in metric (EPSG:32636)
    minx, miny, maxx, maxy = points_gdf.total_bounds
    grid_gdf = generate_grid((minx, miny, maxx, maxy), cell_size_m=500)
    
    # 3. Spatial Join
    joined_gdf = join_points_to_grid(points_gdf, grid_gdf)
    
    # 4. Embed Descriptions ('text_des')
    embedder = Embedder()
    joined_gdf['embedding'] = list(embedder.embed_texts(joined_gdf['text_des'].tolist()))
    
    # 5. Aggregate (Cell Story)
    cell_stories = aggregate_cell_embeddings(joined_gdf)
    
    # 6. Classification (Mock Logic for demo)
    # We map 'category' counts per cell for a simple output or use embeddings.
    # To keep it production-ready and modular, we'll return a distribution.
    
    # Let's count categories in joined_gdf per cell_id for simple label matching
    category_counts = joined_gdf.groupby(['cell_id', 'category']).size().unstack(fill_value=0)
    
    results = []
    # Merge category counts into cell story (though for now we just return them)
    # Classify: Residential, Commercial, Industrial 
    # Mocking for demonstration based on descriptions or counts
    for idx, row in category_counts.iterrows():
        # Map original 'category' to our targets
        residential = float(row.get('Health', 0) + row.get('Education', 0)) # Mock: Health/Edu -> residential area signifier
        commercial = float(row.get('Shop', 0) + row.get('Amenity', 0))
        industrial = float(row.get('Craft', 0))
        
        # Softmax-ish normalization
        # Adding some noise to show embedding influence if needed
        total = residential + commercial + industrial + 1e-6
        results.append({
            "cell_id": int(idx),
            "residential": residential / total,
            "commercial": commercial / total,
            "industrial": industrial / total,
            "dominant_class": ["Residential", "Commercial", "Industrial"][np.argmax([residential, commercial, industrial])]
        })
        
    return results
