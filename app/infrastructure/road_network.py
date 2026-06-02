"""
AI-13 Road Network Loader (FINAL FIXED)
Compatible with OSMnx v2+
"""

import osmnx as ox
import geopandas as gpd
import numpy as np

import app.config as config


class RoadNetworkLoader:

    def __init__(self, bbox=None, place_name=None):
        self.bbox = bbox
        self.place_name = place_name

        self.G = None
        self.nodes_gdf = None
        self.edges_gdf = None

    # -------------------------
    # Load graph
    # -------------------------
    def load(self):

        print("Loading road network...")

        if self.bbox:
            north, south, east, west = self.bbox

            # ✅ FIXED FOR OSMNX v2
            self.G = ox.graph_from_bbox(
                bbox=(north, south, east, west),
                network_type='drive'
            )

        elif self.place_name:
            self.G = ox.graph_from_place(
                self.place_name,
                network_type='drive'
            )

        else:
            raise ValueError("Provide bbox or place_name")

        self.nodes_gdf, self.edges_gdf = ox.graph_to_gdfs(self.G)

        print("✔ Graph loaded")
        print("Nodes:", len(self.nodes_gdf))
        print("Edges:", len(self.edges_gdf))

        return self.G

    # -------------------------
    # Features per geometry
    # -------------------------
    def get_graph_features_for_geometry(self, geometry):

        cell_edges = self.edges_gdf.clip(geometry)
        cell_nodes = self.nodes_gdf.clip(geometry)

        node_count = len(cell_nodes)

        total_length = (
            cell_edges["length"].sum()
            if not cell_edges.empty else 0.0
        )

        avg_degree = (
            cell_nodes["street_count"].mean()
            if not cell_nodes.empty else 0.0
        )

        return np.array([
            node_count,
            total_length,
            avg_degree
        ], dtype=np.float32)

    # -------------------------
    # Grid features
    # -------------------------
    def get_graph_features_for_grid(self, grid_gdf):

        return np.vstack([
            self.get_graph_features_for_geometry(geom)
            for geom in grid_gdf.geometry
        ])

    # -------------------------
    # FINAL FUSION (AI-12 INPUT)
    # -------------------------
    def build_final_features(self, grid_gdf, poi_features, img_features):

        graph_features = self.get_graph_features_for_grid(grid_gdf)

        x = np.concatenate([
            poi_features,
            img_features,
            graph_features
        ], axis=1)

        print("✔ Final feature shape:", x.shape)

        return x


# -------------------------
# MAIN TEST
# -------------------------
if __name__ == "__main__":

    cairo_bbox = (30.2, 29.9, 31.5, 30.5)

    loader = RoadNetworkLoader(bbox=cairo_bbox)
    loader.load()

    print("DONE")