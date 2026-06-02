import torch
from app.infrastructure.gnn_model import UrbanGNN

model = UrbanGNN()

x = torch.randn(10, 643)

edge_index = torch.tensor(
    [
        [0,1,2,3,4,5,6,7,8],
        [1,2,3,4,5,6,7,8,9]
    ],
    dtype=torch.long
)

out = model(x, edge_index)

print(out.shape)