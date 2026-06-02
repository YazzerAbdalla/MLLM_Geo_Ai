"""
Graph Neural Network Model (AI-12)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

from torch_geometric.nn import SAGEConv

from app.config import (
    POI_DIM,
    IMG_DIM,
    GRAPH_DIM
)


class UrbanGNN(nn.Module):

    def __init__(
        self,
        hidden_dim=128,
        embedding_dim=64
    ):
        super().__init__()

        input_dim = (
            POI_DIM +
            IMG_DIM +
            GRAPH_DIM
        )

        self.conv1 = SAGEConv(
            input_dim,
            hidden_dim
        )

        self.conv2 = SAGEConv(
            hidden_dim,
            embedding_dim
        )

    def forward(
        self,
        x,
        edge_index
    ):
        x = self.conv1(
            x,
            edge_index
        )

        x = F.relu(x)

        x = self.conv2(
            x,
            edge_index
        )

        return x