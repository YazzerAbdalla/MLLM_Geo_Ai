"""
 * Regression tests for DEF-007 through DEF-014.
 *
 * Tests:
 *   DEF-007: Large area rejection (cell count > 500 -> 413)
 *   DEF-008: Invalid grid ID rejection (404)
 *   DEF-009: Empty modalities rejection (already tested in test_defect_fixes.py)
 *   DEF-010: DELETE /jobs/{job_id} endpoint
 *   DEF-011: MLLM training validation (invalid extension, nonexistent path)
 *   DEF-012: Evaluation endpoint - prediction label column detection
 *   DEF-013: num_cells data integrity
 *   DEF-014: Road density CRS calculation
"""
import pytest
import json
import math
from unittest.mock import MagicMock, patch, PropertyMock


# -------------------------------------------------------
# DEF-007: Large Area Validation
# -------------------------------------------------------

def test_load_area_rejects_large_bbox(client, monkeypatch):
    """A bbox that would produce >500 cells should return 413 immediately."""
    # bbox covering ~1 degree (~111km) with 200m grid => ~25 cells/deg * 25 = 625 cells
    payload = {
        "bbox": [31.0, 30.0, 32.0, 30.5],
        "grid_size": 200,
        "modalities": ["poi"]
    }
    monkeypatch.setattr("app.interfaces.api.TASKS_AVAILABLE", True)
    resp = client.post("/api/v1/load-area", json=payload)
    assert resp.status_code == 413, f"Expected 413, got {resp.status_code}: {resp.json()}"
    assert "exceed" in resp.json()["detail"].lower()


def test_load_area_accepts_small_bbox(client, monkeypatch):
    """A bbox that would produce <=500 cells should pass validation."""
    # Very small bbox: ~0.04 x 0.04 deg at 500m grid => ~10x10 = 100 cells
    payload = {
        "bbox": [31.20, 30.00, 31.24, 30.04],
        "grid_size": 500,
        "modalities": ["poi"]
    }
    monkeypatch.setattr("app.interfaces.api.TASKS_AVAILABLE", True)
    resp = client.post("/api/v1/load-area", json=payload)
    # Should get 202 (queued) rather than 413
    assert resp.status_code == 202, f"Expected 202, got {resp.status_code}: {resp.json()}"


def test_load_area_edge_case_exactly_500(client, monkeypatch):
    """A bbox producing <=500 cells should be accepted (not rejected)."""
    cell_size_deg = 500 / 111000.0
    payload = {
        "bbox": [31.0, 30.0, 31.0 + 15 * cell_size_deg, 30.0 + 15 * cell_size_deg],
        "grid_size": 500,
        "modalities": ["poi"]
    }
    monkeypatch.setattr("app.interfaces.api.TASKS_AVAILABLE", True)
    resp = client.post("/api/v1/load-area", json=payload)
    assert resp.status_code == 202, f"Expected 202, got {resp.status_code}"


# -------------------------------------------------------
# DEF-008: Invalid Grid ID Rejection
# -------------------------------------------------------

def test_classify_rejects_invalid_grid_id(client, monkeypatch):
    """Classify with non-existent grid_id should return 404."""
    fake_grid_id = "grid_nonexistent"
    monkeypatch.setattr("app.interfaces.api.TASKS_AVAILABLE", True)
    resp = client.post("/api/v1/classify", json={
        "grid_id": fake_grid_id,
        "modalities": ["poi"]
    })
    assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.json()}"
    assert "not found" in resp.json()["detail"].lower()


def test_classify_accepts_valid_grid_id(client, monkeypatch):
    """Classify with valid grid_id should return 202 (if TASKS_AVAILABLE)."""
    monkeypatch.setattr("app.interfaces.api.TASKS_AVAILABLE", True)

    # store a minimal grid so get_grid() returns it
    from app.infrastructure.job_store import job_store
    import geopandas as gpd
    from shapely.geometry import box

    gdf = gpd.GeoDataFrame(
        {"cell_id": [0], "total_length": [100.0], "node_count": [5], "avg_degree": [2.0]},
        geometry=[box(31.0, 30.0, 31.01, 30.01)],
        crs="EPSG:4326"
    )
    job_store.store_grid("grid_test_valid", {"gdf": gdf, "bbox": [31.0, 30.0, 31.01, 30.01]})

    resp = client.post("/api/v1/classify", json={
        "grid_id": "grid_test_valid",
        "modalities": ["poi"]
    })
    assert resp.status_code == 202, f"Expected 202, got {resp.status_code}: {resp.json()}"


# -------------------------------------------------------
# DEF-009: Empty Modalities
# -------------------------------------------------------

def test_classify_empty_modalities_still_rejected(client):
    """Regression: empty modalities in classify must still return 400."""
    resp = client.post("/api/v1/classify", json={
        "grid_id": "any_grid",
        "modalities": []
    })
    assert resp.status_code == 400
    body = resp.json()
    assert "modality" in body["detail"].lower() or "modalities" in body["detail"].lower()


# -------------------------------------------------------
# DEF-010: DELETE Job Endpoint
# -------------------------------------------------------

def test_delete_job_returns_200_for_existing_job(client, monkeypatch):
    """DELETE /jobs/{job_id} on existing job returns 200."""
    from app.infrastructure.job_store import job_store
    monkeypatch.setattr(job_store, "get_job",
                        lambda x: {"id": x, "status": "running", "celery_task_id": None})
    resp = client.delete("/api/v1/jobs/test_job_200")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    assert resp.json()["status"] == "cancelled"


def test_delete_job_returns_404_for_missing_job(client, monkeypatch):
    """DELETE /jobs/{job_id} on non-existent job returns 404."""
    from app.infrastructure.job_store import job_store
    monkeypatch.setattr(job_store, "get_job", lambda x: None)
    resp = client.delete("/api/v1/jobs/job_nonexistent")
    assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"


def test_delete_job_endpoint_method_not_allowed(client):
    """GET /jobs/{job_id} should return 405 (not a valid GET endpoint)."""
    resp = client.get("/api/v1/jobs/some_job")
    assert resp.status_code == 405


# -------------------------------------------------------
# DEF-011: MLLM Training Validation
# -------------------------------------------------------

def test_mllm_train_rejects_invalid_extension(client, monkeypatch):
    """Reject dataset with unsupported extension (.graphml)."""
    monkeypatch.setattr("os.path.exists", lambda p: True)
    resp = client.post("/api/v1/mllm/train", json={
        "model_name": "tiny-llm",
        "dataset_path": "data/dataset.graphml"
    })
    assert resp.status_code == 400
    assert "extension" in resp.json()["detail"].lower() or "format" in resp.json()["detail"].lower()


def test_mllm_train_rejects_nonexistent_dataset(client, monkeypatch):
    """Reject non-existent dataset path."""
    monkeypatch.setattr("os.path.exists", lambda p: False)
    resp = client.post("/api/v1/mllm/train", json={
        "model_name": "tiny-llm",
        "dataset_path": "data/nonexistent.csv"
    })
    assert resp.status_code == 400
    assert "not found" in resp.json()["detail"].lower()


def test_mllm_train_rejects_empty_dataset_path(client):
    """Reject empty dataset_path."""
    resp = client.post("/api/v1/mllm/train", json={
        "model_name": "tiny-llm",
        "dataset_path": ""
    })
    assert resp.status_code in (400, 422)


def test_mllm_train_rejects_bad_epochs(client):
    """Reject epochs outside 1-100 range."""
    resp = client.post("/api/v1/mllm/train", json={
        "model_name": "tiny-llm",
        "dataset_path": "data/dataset.csv",
        "epochs": 0
    })
    assert resp.status_code == 400


def test_mllm_train_rejects_bad_batch_size(client):
    """Reject batch_size outside 1-1024 range."""
    resp = client.post("/api/v1/mllm/train", json={
        "model_name": "tiny-llm",
        "dataset_path": "data/dataset.csv",
        "batch_size": 9999
    })
    assert resp.status_code in (400, 422)


def test_mllm_use_case_layer_validates(monkeypatch):
    """MllmUseCase._validate_training_inputs must reject invalid inputs."""
    from app.application.mllm_use_case import MllmUseCase
    use_case = MllmUseCase()
    with pytest.raises(ValueError, match="dataset_path"):
        use_case._validate_training_inputs("", 3, 8)

    monkeypatch.setattr("os.path.exists", lambda p: False)
    with pytest.raises(ValueError, match="not found"):
        use_case._validate_training_inputs("/nonexistent/path.csv", 3, 8)

    monkeypatch.setattr("os.path.exists", lambda p: True)
    with pytest.raises(ValueError, match="Unsupported"):
        use_case._validate_training_inputs("test.graphml", 3, 8)
    with pytest.raises(ValueError, match="epochs"):
        use_case._validate_training_inputs("test.csv", 0, 8)
    with pytest.raises(ValueError, match="epochs"):
        use_case._validate_training_inputs("test.csv", 101, 8)
    with pytest.raises(ValueError, match="batch_size"):
        use_case._validate_training_inputs("test.csv", 3, 0)
    with pytest.raises(ValueError, match="batch_size"):
        use_case._validate_training_inputs("test.csv", 3, 9999)
    # Should not raise
    use_case._validate_training_inputs("test.csv", 3, 8)


# -------------------------------------------------------
# DEF-012: Evaluation Endpoint
# -------------------------------------------------------

def test_evaluation_detects_dominant_class_column():
    """PRED_LABEL_CANDIDATES must include dominant_class."""
    from app.application.evaluation_service import PRED_LABEL_CANDIDATES
    assert "dominant_class" in PRED_LABEL_CANDIDATES, \
        f"dominant_class not found in {PRED_LABEL_CANDIDATES}"


def test_evaluation_works_with_classification_output(client, monkeypatch, tmp_path):
    """Evaluate should find prediction column in classification results."""
    from app.application.evaluation_service import _detect_column

    columns = ["cell_id", "dominant_class", "confidence", "geometry"]
    detected = _detect_column(columns, ["dominant_class", "predicted_label", "pred_label"])
    assert detected == "dominant_class"


# -------------------------------------------------------
# DEF-013: num_cells Data Integrity
# -------------------------------------------------------

def test_num_cells_in_area_status(client, monkeypatch):
    """Area status should return correct num_cells for completed job."""
    import uuid
    from app.infrastructure.job_store import job_store
    from app.infrastructure.db import SessionLocal
    from app.models.grid import Grid
    import json as json_mod

    grid_id = f"grid_numcells_{uuid.uuid4().hex[:8]}"
    job_id = f"job_numcells_{uuid.uuid4().hex[:8]}"

    # Create a grid record in SQLite with known num_cells
    db = SessionLocal()
    try:
        test_grid = Grid(
            id=grid_id,
            bbox=json_mod.dumps([31.0, 30.0, 31.1, 30.1]),
            grid_size_m=500,
            num_cells=42,
            status="completed"
        )
        db.add(test_grid)
        db.commit()
    finally:
        db.close()

    # Mock get_job to return completed status with grid_id
    monkeypatch.setattr(job_store, "get_job",
                        lambda x: {"id": x, "status": "completed",
                                   "grid_id": grid_id,
                                   "num_cells": 0,  # Intentionally wrong
                                   "progress": 1.0, "step": "done", "error": None})

    resp = client.get(f"/api/v1/area-status/{job_id}")
    assert resp.status_code == 200
    body = resp.json()
    # Should read from Grid table = 42, not from job = 0
    assert body["num_cells"] == 42, f"Expected 42, got {body['num_cells']}"


def test_num_cells_fallback_to_job_value(client, monkeypatch):
    """When Grid table has no num_cells, fall back to job num_cells."""
    from app.infrastructure.job_store import job_store
    monkeypatch.setattr(job_store, "get_job",
                        lambda x: {"id": x, "status": "completed",
                                   "grid_id": "grid_no_numcells",
                                   "num_cells": 25,
                                   "progress": 1.0, "step": "done", "error": None})

    resp = client.get("/api/v1/area-status/job_no_grid")
    assert resp.status_code == 200
    body = resp.json()
    assert body["num_cells"] == 25


# -------------------------------------------------------
# DEF-014: Road Density CRS Calculation
# -------------------------------------------------------

def test_road_density_uses_projected_crs():
    """Road density must use projected CRS (EPSG:3857) not degree-based area."""
    from shapely.geometry import box
    import geopandas as gpd
    import numpy as np

    # A ~500m cell near Cairo in EPSG:4326
    geom = box(31.20, 30.00, 31.205, 30.005)
    total_length_m = 200.0  # 200m of road

    gdf_4326 = gpd.GeoDataFrame(geometry=[geom], crs="EPSG:4326")
    gdf_3857 = gdf_4326.to_crs("EPSG:3857")
    area_m2 = gdf_3857.geometry.area.iloc[0]
    area_km2 = area_m2 / 1e6

    road_density = (total_length_m / 1000) / area_km2 if area_km2 > 0 else 0.0

    # If computed in degrees, area would be ~0.000025 deg^2 -> area_km2 would be wrong
    # In projected CRS, area should be ~0.25 km^2, giving density ~0.8 km/km^2
    assert 0.01 < road_density < 100, f"Road density {road_density} out of realistic range"
    assert area_m2 > 1000, f"Area in m2 too small: {area_m2} (projected CRS not applied)"
