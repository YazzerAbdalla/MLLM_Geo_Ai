"""
Regression tests for trained model checkpoint.
Verifies checkpoint existence, loading, inference quality, and dimensions.
"""
import os
import pytest
import torch
import numpy as np
from app.domain.mlp_model import UrbanMLP
from app.config import FUSION_DIM

CHECKPOINT_PATH = "models/urban_mlp.pt"


def test_checkpoint_exists():
    assert os.path.exists(CHECKPOINT_PATH), f"Checkpoint not found: {CHECKPOINT_PATH}"


def test_checkpoint_loads_successfully():
    ckpt = torch.load(CHECKPOINT_PATH, map_location="cpu")
    assert isinstance(ckpt, dict)
    if "state_dict" in ckpt:
        sd = ckpt["state_dict"]
    else:
        sd = ckpt
    assert any(k.startswith("net.") for k in sd), "Checkpoint missing net.* keys"
    assert sd["net.0.weight"].shape[0] == 256, "Expected hidden_dim=256"
    assert sd["net.3.weight"].shape[0] == 3, "Expected output_dim=3"


def test_checkpoint_matches_architecture():
    ckpt = torch.load(CHECKPOINT_PATH, map_location="cpu")
    if "state_dict" in ckpt:
        sd = ckpt["state_dict"]
    else:
        sd = ckpt

    model = UrbanMLP(input_dim=FUSION_DIM, hidden_dim=256, output_dim=3)
    try:
        model.load_state_dict(sd, strict=True)
        loaded_ok = True
    except Exception as e:
        loaded_ok = False
        pytest.fail(f"State dict mismatch: {e}")
    assert loaded_ok, "Checkpoint cannot be loaded into UrbanMLP"


def test_inference_returns_non_uniform_probs():
    ckpt = torch.load(CHECKPOINT_PATH, map_location="cpu")
    if "state_dict" in ckpt:
        sd = ckpt["state_dict"]
    else:
        sd = ckpt

    model = UrbanMLP(input_dim=FUSION_DIM, hidden_dim=256, output_dim=3)
    model.load_state_dict(sd, strict=True)
    model.eval()

    X = torch.randn((10, FUSION_DIM), dtype=torch.float32)
    with torch.no_grad():
        probs = model(X).numpy()

    assert probs.shape == (10, 3), f"Expected (10, 3), got {probs.shape}"

    # Check all rows sum to ~1.0
    sums = probs.sum(axis=1)
    assert np.allclose(sums, np.ones(10), atol=1e-5), "Probabilities don't sum to 1"

    # Check that not all rows are uniform (max - min > threshold)
    for i in range(10):
        prob_range = probs[i].max() - probs[i].min()
        assert prob_range > 0.01, f"Sample {i} has near-uniform probs: {probs[i]}"


def test_inference_output_dimensions_match_classes():
    ckpt = torch.load(CHECKPOINT_PATH, map_location="cpu")
    if "state_dict" in ckpt:
        sd = ckpt["state_dict"]
    else:
        sd = ckpt

    # Verify output layer dimension
    output_weight = sd["net.3.weight"]
    assert output_weight.shape[0] == 3, f"Expected 3 classes, got {output_weight.shape[0]}"

    model = UrbanMLP(input_dim=FUSION_DIM, hidden_dim=256, output_dim=3)
    model.load_state_dict(sd, strict=True)
    model.eval()

    # Single sample
    X = torch.zeros((1, FUSION_DIM))
    with torch.no_grad():
        out = model(X)
    assert out.shape == (1, 3), f"Expected (1, 3), got {out.shape}"

    # Batch
    X_batch = torch.zeros((32, FUSION_DIM))
    with torch.no_grad():
        out_batch = model(X_batch)
    assert out_batch.shape == (32, 3), f"Expected (32, 3), got {out_batch.shape}"
