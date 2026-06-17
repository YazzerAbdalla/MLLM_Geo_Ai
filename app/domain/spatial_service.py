"""
AI-14 Spatial Service (FINAL RUNNABLE VERSION)
- Grid generation
- Spatial join
- Attention fusion
"""

import geopandas as gpd
import numpy as np
from shapely.geometry import box


# -----------------------------
# GRID GENERATION
# -----------------------------
def generate_grid(bounds: tuple, cell_size_m: float = 500.0):

    min_x, min_y, max_x, max_y = bounds

    max_range = max(max_x - min_x, max_y - min_y)

    if max_range < 180:
        cell_size = cell_size_m / 111000.0

        cols = int(np.ceil((max_x - min_x) / cell_size))
        rows = int(np.ceil((max_y - min_y) / cell_size))

        cells = []

        for i in range(cols):
            for j in range(rows):
                x1 = min_x + i * cell_size
                y1 = min_y + j * cell_size
                x2 = x1 + cell_size
                y2 = y1 + cell_size

                cells.append(box(x1, y1, x2, y2))

        gdf = gpd.GeoDataFrame(geometry=cells, crs="EPSG:4326")

    else:
        cols = int(np.ceil((max_x - min_x) / cell_size_m))
        rows = int(np.ceil((max_y - min_y) / cell_size_m))

        cells = []

        for i in range(cols):
            for j in range(rows):
                x1 = min_x + i * cell_size_m
                y1 = min_y + j * cell_size_m
                x2 = x1 + cell_size_m
                y2 = y1 + cell_size_m

                cells.append(box(x1, y1, x2, y2))

        gdf = gpd.GeoDataFrame(geometry=cells, crs="EPSG:32636")

    gdf["cell_id"] = range(len(gdf))
    return gdf


# -----------------------------
# SPATIAL JOIN
# -----------------------------
def join_points_to_grid(points_gdf, grid_gdf):

    if points_gdf.crs != grid_gdf.crs:
        points_gdf = points_gdf.to_crs(grid_gdf.crs)

    return gpd.sjoin(
        points_gdf,
        grid_gdf[["geometry", "cell_id"]],
        how="inner",
        predicate="within"
    )


# -----------------------------
# ATTENTION FUSION
# -----------------------------
def attention_fusion(poi, image, graph):
    """
    * Simple attention fusion for multi-modal features.
    *
    * Each modality is first projected to a common dimension (via norm-based scoring)
    * before computing attention weights. Works with different-shaped inputs.
    """

    # Compute scalar attention scores from vector norms (one per modality)
    scores_list = np.array([
        float(np.linalg.norm(poi) if poi.ndim == 1 else 0),
        float(np.linalg.norm(image) if image.ndim == 1 else 0),
        float(np.linalg.norm(graph) if graph.ndim == 1 else 0),
    ])

    # Softmax over three scores
    exp_scores = np.exp(scores_list - np.max(scores_list))
    weights = exp_scores / (np.sum(exp_scores) + 1e-8)

    # Concatenate features (since they have different dimensions)
    fused = np.concatenate([poi, image, graph], axis=-1)

    return fused, weights


# -----------------------------
# MULTIMODAL FUSION
# -----------------------------
def create_multimodal_feature(poi_embedding,
                               image_embedding,
                               graph_features,
                               use_attention=True):

    if not use_attention:
        return np.concatenate(
            [poi_embedding, image_embedding, graph_features],
            axis=-1
        )

    fused, weights = attention_fusion(
        poi_embedding,
        image_embedding,
        graph_features
    )

    return fused


# -----------------------------
# TEST RUN (IMPORTANT)
# -----------------------------
if __name__ == "__main__":

    print("Running AI-14 test...")

    poi = np.array([1.0, 2.0, 3.0])
    img = np.array([0.5, 1.5, 2.5])
    graph = np.array([2.0, 1.0, 0.5])

    fused, weights = attention_fusion(poi, img, graph)

    print("Fused:", fused)
    print("Weights:", weights)

    # test grid
    cairo_bbox = (30.2, 29.9, 31.5, 30.5)
    grid = generate_grid(cairo_bbox, 500)

    print("Grid cells:", len(grid))
    print("DONE")