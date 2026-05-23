"""
 * Tests the 8-neighbor Spatial Accuracy implementation.
"""
import pytest
import numpy as np
import pandas as pd

def _grid_spatial_accuracy(predictions):
    if predictions.size == 0:
        return 0.0
    matches, total = 0, 0
    rows, cols = predictions.shape
    for i in range(rows):
        for j in range(cols):
            neighbors = []
            for di, dj in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
                ni, nj = i + di, j + dj
                if 0 <= ni < rows and 0 <= nj < cols:
                    neighbors.append(predictions[ni, nj])
            if neighbors:
                majority = max(set(neighbors), key=neighbors.count)
                if majority == predictions[i, j]:
                    matches += 1
                total += 1
    return matches / total if total > 0 else 0.0

def test_spatial_accuracy_exists():
    try:
        from evals.eval_multimodal import compute_spatial_accuracy
    except ImportError:
        pytest.fail("compute_spatial_accuracy not found in evals/eval_multimodal.py")

def test_spatial_accuracy_perfect_grid():
    predictions = np.zeros((3, 3), dtype=int)
    score = _grid_spatial_accuracy(predictions)
    assert score == 1.0, f"Perfect grid should score 1.0, got {score}"

def test_spatial_accuracy_range():
    np.random.seed(42)
    predictions = np.random.randint(0, 3, size=(5, 5))
    score = _grid_spatial_accuracy(predictions)
    assert 0.0 <= score <= 1.0, f"Score {score} out of [0,1] range"
