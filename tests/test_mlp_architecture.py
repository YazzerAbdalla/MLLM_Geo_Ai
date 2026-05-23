"""
 * Tests that the MLP architecture hidden dimension is exactly 128.
"""
import pytest
import torch
from app.domain.mlp_model import UrbanMLP
from app.config import FUSION_DIM

def test_mlp_hidden_dim():
    """
     * Test that the first linear layer in the network outputs to a dimension of 128.
    """
    model = UrbanMLP()
    # // Retrieve the first layer in the sequential container
    first_layer = model.net[0]
    
    # // Verify that it is a linear layer
    assert isinstance(first_layer, torch.nn.Linear)
    
    # // Verify the output dimension is exactly 128
    assert first_layer.out_features == 128, f"Expected hidden_dim=128, got {first_layer.out_features}"
