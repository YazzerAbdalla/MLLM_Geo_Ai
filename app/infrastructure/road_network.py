"""
 * Road Network Integration using OSMnx.
 """
import osmnx as ox
import geopandas as gpd
import numpy as np
from app.config import GRAPH_DIM

class RoadNetworkLoader:
    """
     * Loader for OpenStreetMap road networks.
     """
    def __init__(self, bbox=None, place_name=None):
        """
         * Initialize the loader.
         * @param {tuple} bbox - (north, south, east, west)
         * @param {str} place_name - Name of the place to load
         """
        self.bbox = bbox
        self.place_name = place_name
        self.G = None
        self.nodes_gdf = None
        self.edges_gdf = None

    def load(self):
        """
         * Load the road network graph from OSM.
         * @returns {networkx.MultiDiGraph} The loaded graph
         """
        if self.bbox:
            north, south, east, west = self.bbox
            self.G = ox.graph_from_bbox(north, south, east, west, network_type='drive')
        elif self.place_name:
            self.G = ox.graph_from_place(self.place_name, network_type='drive')
        else:
            raise ValueError("Must provide either bbox or place_name")
            
        self.nodes_gdf, self.edges_gdf = ox.graph_to_gdfs(self.G)
        return self.G

    def get_graph_features_for_geometry(self, geometry) -> np.ndarray:
        """
         * Extract graph features (node count, total length, average degree) for a single geometry.
         * @param {shapely.geometry.Polygon} geometry - The geometry to extract features for
         * @returns {np.ndarray} A 1D array of shape (GRAPH_DIM,) containing the features
         """
        if self.nodes_gdf is None or self.edges_gdf is None:
            raise ValueError("Graph not loaded. Call load() first.")
            
        # Clip the global graph to this specific cell's geometry
        cell_edges = self.edges_gdf.clip(geometry)
        cell_nodes = self.nodes_gdf.clip(geometry)
        
        node_count = len(cell_nodes)
        total_length = cell_edges['length'].sum() if not cell_edges.empty else 0.0
        avg_degree = cell_nodes['street_count'].mean() if not cell_nodes.empty else 0.0
        
        # Ensure it matches GRAPH_DIM
        features = np.array([node_count, total_length, avg_degree], dtype=np.float32)
        return features

    def get_graph_features_for_grid(self, grid_gdf) -> np.ndarray:
        """
         * Primary public method - extracts features for all grid cells.
         """
        return self.get_graph_features_for_geometry(grid_gdf)
