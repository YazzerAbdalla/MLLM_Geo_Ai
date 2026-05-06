"""
 * Tests for the Road Network integration.
 """
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from shapely.geometry import Polygon
from app.infrastructure.road_network import RoadNetworkLoader
from app.config import GRAPH_DIM

@patch('app.infrastructure.road_network.ox')
def test_road_network_loader(mock_ox):
    # Setup mock graphs and GeoDataFrames
    mock_G = MagicMock()
    mock_ox.graph_from_bbox.return_value = mock_G
    
    mock_nodes_gdf = MagicMock()
    mock_edges_gdf = MagicMock()
    mock_ox.graph_to_gdfs.return_value = (mock_nodes_gdf, mock_edges_gdf)
    
    loader = RoadNetworkLoader(bbox=(30.1, 29.9, 31.3, 31.1))
    G = loader.load()
    
    assert G == mock_G
    mock_ox.graph_from_bbox.assert_called_once_with(30.1, 29.9, 31.3, 31.1, network_type='drive')
    mock_ox.graph_to_gdfs.assert_called_once_with(mock_G)
    
    # Test feature extraction
    # Mock clip to return something
    mock_clipped_nodes = MagicMock()
    mock_clipped_nodes.__len__.return_value = 10
    mock_clipped_nodes['street_count'].mean.return_value = 2.5
    mock_clipped_nodes.empty = False
    
    mock_clipped_edges = MagicMock()
    mock_clipped_edges['length'].sum.return_value = 1500.0
    mock_clipped_edges.empty = False
    
    mock_nodes_gdf.clip.return_value = mock_clipped_nodes
    mock_edges_gdf.clip.return_value = mock_clipped_edges
    
    # Create a dummy geometry
    poly = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    
    features = loader.get_graph_features_for_geometry(poly)
    
    assert isinstance(features, np.ndarray)
    assert features.shape == (GRAPH_DIM,)
    assert features[0] == 10  # node count
    assert features[1] == 1500.0  # length
    assert features[2] == 2.5  # avg degree
