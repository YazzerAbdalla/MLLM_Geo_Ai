"""
 * Tests for Multi-Modal Fusion and MLP Model.
 """
import pytest
import torch
import numpy as np
from app.domain.mlp_model import UrbanMLP
from app.domain.spatial_service import create_multimodal_feature
from app.config import POI_DIM, IMG_DIM, GRAPH_DIM, FUSION_DIM

def test_multimodal_feature_creation():
    poi_emb = np.ones(POI_DIM)
    img_emb = np.ones(IMG_DIM) * 2
    graph_feat = np.ones(GRAPH_DIM) * 3
    
    fused = create_multimodal_feature(poi_emb, img_emb, graph_feat)
    
    assert len(fused) == FUSION_DIM
    assert fused[0] == 1.0
    assert fused[POI_DIM] == 2.0
    assert fused[POI_DIM + IMG_DIM] == 3.0

def test_urban_mlp():
    model = UrbanMLP(input_dim=FUSION_DIM)
    
    # Batch size of 2
    x = torch.zeros((2, FUSION_DIM))
    output = model(x)
    
    assert output.shape == (2, 3)  # 3 classes: Residential, Commercial, Industrial
    # Check softmax (sums to 1 approx)
    assert torch.allclose(output.sum(dim=1), torch.tensor([1.0, 1.0]))
