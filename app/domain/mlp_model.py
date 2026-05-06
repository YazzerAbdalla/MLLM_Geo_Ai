"""
 * Multi-Layer Perceptron (MLP) Model for Urban Classification.
 """
import torch
import torch.nn as nn
from app.config import FUSION_DIM

class UrbanMLP(nn.Module):
    """
     * Simple MLP classifier for multi-modal features.
     """
    def __init__(self, input_dim=FUSION_DIM, hidden_dim=128, output_dim=3):
        """
         * Initialize the MLP.
         * @param {int} input_dim - Dimension of fused input features
         * @param {int} hidden_dim - Hidden layer size
         * @param {int} output_dim - Number of output classes
         """
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, output_dim),
            nn.Softmax(dim=1)
        )

    def forward(self, x):
        """
         * Forward pass of the MLP.
         * @param {torch.Tensor} x - Input tensor of shape (batch_size, input_dim)
         * @returns {torch.Tensor} Output probabilities
         """
        return self.net(x)
