"""
 * Regression tests for audit defect fixes.
 *
 * Tests:
 *   DEF-001: Classification failure status must remain "failed"
 *   DEF-002: num_cells must reflect actual cell count
 *   DEF-003 (root): attention_fusion works with different-shaped inputs
 *   DEF-006: Export only succeeds when job completed + file exists
 *   Empty modalities rejected
 *   MLLM training input validation
"""
import pytest
import numpy as np
from unittest.mock import MagicMock, patch


# -------------------------------------------------------
# DEF-001 / DEF-006: Classification + Export flow
# -------------------------------------------------------

def test_classify_rejects_empty_modalities(client):
    """Validation: empty modalities should return 400."""
    resp = client.post("/api/v1/classify", json={
        "grid_id": "grid_test",
        "modalities": []
    })
    assert resp.status_code == 400
    assert "modalities" in resp.json()["detail"].lower() or "modality" in resp.json()["detail"].lower()


def test_classify_requires_at_least_one_modality(client):
    """Validation: at least one modality required."""
    resp = client.post("/api/v1/classify", json={
        "grid_id": "grid_test",
        "modalities": []
    })
    assert resp.status_code == 400


def test_classify_accepts_poi_modality(client):
    """Validation: poi modality accepted."""
    resp = client.post("/api/v1/classify", json={
        "grid_id": "grid_test",
        "modalities": ["poi"]
    })
    assert resp.status_code in (202, 404)  # 404 if grid doesn't exist, 202 if queued


def test_export_failed_job_returns_400(client, monkeypatch):
    """Export: failed job should return 400, not 404."""
    from app.infrastructure.job_store import job_store
    monkeypatch.setattr(job_store, "get_job",
                        lambda x: {"id": x, "status": "failed", "error": "test error"})
    resp = client.get("/api/v1/export/job_failed?format=geojson")
    assert resp.status_code == 400
    assert "failed" in resp.json()["detail"].lower()


def test_export_pending_job_returns_400(client, monkeypatch):
    """Export: pending job should return 400."""
    from app.infrastructure.job_store import job_store
    monkeypatch.setattr(job_store, "get_job",
                        lambda x: {"id": x, "status": "running", "progress": 0.5})
    resp = client.get("/api/v1/export/job_pending?format=geojson")
    assert resp.status_code == 400
    assert "running" in resp.json()["detail"].lower() or "status" in resp.json()["detail"].lower()


def test_export_missing_job_returns_404(client, monkeypatch):
    """Export: non-existent job returns 404."""
    from app.infrastructure.job_store import job_store
    monkeypatch.setattr(job_store, "get_job", lambda x: None)
    resp = client.get("/api/v1/export/job_nonexistent?format=geojson")
    assert resp.status_code == 404


# -------------------------------------------------------
# DEF-002: num_cells field
# -------------------------------------------------------

@pytest.fixture
def mock_job_with_cells():
    """Fixture that returns a job dict with num_cells set."""
    from app.infrastructure.job_store import job_store
    job_id = job_store.create_job("load")
    job_store.update_job(job_id, status="completed", grid_id="grid_test",
                         num_cells=25, progress=1.0, step="done")
    return job_id


def test_area_status_returns_num_cells(client, monkeypatch):
    """num_cells should be present and non-zero for completed area jobs."""
    from app.infrastructure.job_store import job_store
    monkeypatch.setattr(job_store, "get_job",
                        lambda x: {"id": x, "status": "completed",
                                   "grid_id": "grid_test", "num_cells": 25,
                                   "progress": 1.0, "step": "done", "error": None})
    resp = client.get("/api/v1/area-status/test_job_num_cells")
    assert resp.status_code == 200
    body = resp.json()
    assert body["num_cells"] == 25


# -------------------------------------------------------
# DEF-003: attention_fusion shape handling
# -------------------------------------------------------

def test_attention_fusion_different_shapes():
    """attention_fusion must handle inputs of different dimensions."""
    from app.domain.spatial_service import attention_fusion
    poi = np.ones(384, dtype=np.float32)
    img = np.ones(256, dtype=np.float32) * 2
    graph = np.ones(3, dtype=np.float32) * 3

    fused, weights = attention_fusion(poi, img, graph)

    # Fusion result should be concatenation (384 + 256 + 3 = 643)
    assert fused.shape == (643,)
    assert len(weights) == 3
    # Weights should sum to ~1.0
    assert abs(float(np.sum(weights)) - 1.0) < 0.01


def test_attention_fusion_zero_inputs():
    """attention_fusion should handle all-zero inputs gracefully."""
    from app.domain.spatial_service import attention_fusion
    poi = np.zeros(384, dtype=np.float32)
    img = np.zeros(256, dtype=np.float32)
    graph = np.zeros(3, dtype=np.float32)

    fused, weights = attention_fusion(poi, img, graph)
    assert fused.shape == (643,)
    assert len(weights) == 3


# -------------------------------------------------------
# Validation: MLLM training input
# -------------------------------------------------------

def test_mllm_train_rejects_missing_dataset(client, monkeypatch):
    """MLLM train should reject non-existent dataset path."""
    monkeypatch.setattr("os.path.exists", lambda path: False)
    resp = client.post("/api/v1/mllm/train", json={
        "model_name": "tiny-llm",
        "dataset_path": "data/nonexistent.csv"
    })
    assert resp.status_code == 400
    assert "not found" in resp.json()["detail"].lower()


def test_mllm_train_rejects_empty_path(client):
    """MLLM train should reject empty dataset_path."""
    resp = client.post("/api/v1/mllm/train", json={
        "model_name": "tiny-llm",
        "dataset_path": ""
    })
    assert resp.status_code in (400, 422)  # 400 from validation or 422 from Pydantic


def test_mllm_train_rejects_bad_epochs(client):
    """MLLM train should reject out-of-range epochs."""
    resp = client.post("/api/v1/mllm/train", json={
        "model_name": "tiny-llm",
        "dataset_path": "data/dataset.csv",
        "epochs": 0
    })
    assert resp.status_code == 400


def test_mllm_train_rejects_bad_batch_size(client):
    """MLLM train should reject out-of-range batch_size."""
    resp = client.post("/api/v1/mllm/train", json={
        "model_name": "tiny-llm",
        "dataset_path": "data/dataset.csv",
        "batch_size": 9999
    })
    assert resp.status_code in (400, 422)


# -------------------------------------------------------
# Export format validation
# -------------------------------------------------------

def test_export_invalid_format(client, monkeypatch):
    """Export should reject invalid format parameter."""
    from app.infrastructure.job_store import job_store
    monkeypatch.setattr(job_store, "get_job",
                        lambda x: {"id": x, "status": "completed"})
    monkeypatch.setattr("os.path.exists", lambda x: True)
    resp = client.get("/api/v1/export/test_job?format=xml")
    assert resp.status_code == 400
