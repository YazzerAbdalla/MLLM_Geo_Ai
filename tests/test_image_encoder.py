"""
 * Tests for the Image Encoder using ResNet.
 """
import pytest
import numpy as np
import torch
from unittest.mock import patch, MagicMock
from app.infrastructure.image_encoder import ImageEncoder
from app.config import IMG_DIM

@patch('app.infrastructure.image_encoder.Image.open')
def test_image_encoder(mock_open):
    from PIL import Image as PILImage
    import torch.nn as nn
    # Mock image with a real PIL Image so transforms don't fail
    real_img = PILImage.new('RGB', (256, 256), color='red')
    mock_open.return_value = real_img
    
    # Return a fake resnet to avoid downloads and mocking issues
    with patch('app.infrastructure.image_encoder.models.resnet18') as mock_resnet:
        class FakeResNet(nn.Module):
            def __init__(self):
                super().__init__()
                self.fc = nn.Linear(512, 1000)
            def forward(self, x):
                return torch.zeros((1, IMG_DIM))
        
        mock_resnet.return_value = FakeResNet()
        
        encoder = ImageEncoder()
        
        # Test encode
        emb = encoder.encode('dummy/path.png')
        
        assert isinstance(emb, np.ndarray)
        assert emb.shape == (IMG_DIM,)
