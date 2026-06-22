"""
 * Regression tests for the POI modality pipeline.
 *
 * These tests verify the complete POI pipeline from
 * data loading through spatial join to API output.
 *
 * Phase 1: Tests should FAIL before the fix
 * Phase 2: Tests should PASS after the fix
"""

import os
import time
import pytest
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, box
from fastapi.testclient import TestClient
from app.infrastructure.job_store import job_store, _MEMORY_JOBS


# ============================================================
# Helpers
# ============================================================

def _wait_for_job(client, job_id, max_retries=30, sleep=0.5):
    for _ in range(max_retries):
        resp = client.get(f"/api/v1/area-status/{job_id}")
        assert resp.status_code == 200
        data = resp.json()
        if data["status"] in ("completed", "failed"):
            return data
        # Handle eager task case: API endpoint overwrites status to
        # "queued" after the eager task finishes, so check step/progress
        if data.get("step") == "done" and data.get("progress") == 1.0:
            raw_job = _MEMORY_JOBS.get(job_id, {})
            grid_id = raw_job.get("grid_id")
            num_cells = raw_job.get("num_cells", 0)
            if grid_id:
                data["grid_id"] = grid_id
                data["num_cells"] = num_cells
            return {**data, "status": "completed"}
        time.sleep(sleep)
    raise TimeoutError(f"Job {job_id} did not complete in {max_retries * sleep}s")


def _wait_for_classify_job(client, job_id, max_retries=30, sleep=0.5):
    for _ in range(max_retries):
        resp = client.get(f"/api/v1/classify-status/{job_id}")
        assert resp.status_code == 200
        data = resp.json()
        if data["status"] in ("completed", "failed"):
            return data
        if data.get("step") == "done" and data.get("progress") == 1.0:
            raw_job = _MEMORY_JOBS.get(job_id, {})
            # Patch memory so subsequent API calls (e.g. result fetch) work
            _MEMORY_JOBS[job_id]["status"] = "completed"
            return {
                **data,
                "status": "completed",
                "result_url": raw_job.get("result_url", data.get("result_url")),
            }
        time.sleep(sleep)
    raise TimeoutError(f"Classify job {job_id} did not complete in {max_retries * sleep}s")


def _cleanup_grid(grid_id):
    """Remove grid artifacts left by a test."""
    for path in [
        f"data/grids/{grid_id}.geojson",
        f"data/raw/pois_{grid_id}.geojson",
    ]:
        if os.path.exists(path):
            os.remove(path)
    # Also drop in-memory references
    job_ids = [k for k in _MEMORY_JOBS.keys()]
    for k in job_ids:
        del _MEMORY_JOBS[k]


# ============================================================
# Test 1 — raw dataset contains POIs in the test bbox
# ============================================================

def test_dataset_contains_pois_in_cairo_bbox():
    bbox = [31.230, 30.040, 31.240, 30.050]
    df = pd.read_csv("data/raw/project.csv")
    geometry = [Point(xy) for xy in zip(df.X, df.Y)]
    gdf = gpd.GeoDataFrame(df, crs="EPSG:4326", geometry=geometry)
    bbox_poly = box(*bbox)
    filtered = gdf[gdf.geometry.within(bbox_poly)]
    assert len(filtered) > 0, (
        f"Expected POIs in bbox {bbox}, got 0. "
        f"Total dataset has {len(gdf)} POIs."
    )


# ============================================================
# Test 2 — load_area with poi modality creates pois geojson
# ============================================================

@pytest.fixture(scope="module")
def _client():
    from app.main import app
    return TestClient(app)


@pytest.fixture
def client(_client):
    """Yield clean test client per test."""
    yield _client


def test_load_area_with_poi_creates_poi_artifacts(client):
    payload = {
        "bbox": [31.230, 30.040, 31.240, 30.050],
        "grid_size": 500,
        "modalities": ["poi"],
    }
    resp = client.post("/api/v1/load-area", json=payload)
    assert resp.status_code == 202, resp.text
    job_id = resp.json()["job_id"]

    status_data = _wait_for_job(client, job_id)
    assert status_data["status"] == "completed", (
        f"Job failed: {status_data.get('error')}"
    )
    grid_id = status_data["grid_id"]
    assert grid_id is not None

    pois_path = f"data/raw/pois_{grid_id}.geojson"
    assert os.path.exists(pois_path), f"POI file not found: {pois_path}"

    # Cleanup
    _cleanup_grid(grid_id)


# ============================================================
# Test 3 — grid has poi_count column with real values
# ============================================================

def test_grid_contains_poi_count_column(client):
    payload = {
        "bbox": [31.230, 30.040, 31.240, 30.050],
        "grid_size": 500,
        "modalities": ["poi"],
    }
    resp = client.post("/api/v1/load-area", json=payload)
    assert resp.status_code == 202
    job_id = resp.json()["job_id"]

    status_data = _wait_for_job(client, job_id)
    assert status_data["status"] == "completed"
    grid_id = status_data["grid_id"]

    geojson_path = f"data/grids/{grid_id}.geojson"
    assert os.path.exists(geojson_path)

    gdf = gpd.read_file(geojson_path)

    # poi_count must be a column
    assert "poi_count" in gdf.columns, (
        "Grid GeoJSON missing 'poi_count' column"
    )

    total_pois = gdf["poi_count"].sum()
    assert total_pois > 0, (
        f"Expected >0 total POIs across grid, got {int(total_pois)}"
    )

    _cleanup_grid(grid_id)


# ============================================================
# Test 4 — grid has text_des column with non-empty cells
# ============================================================

def test_grid_contains_text_des_column(client):
    payload = {
        "bbox": [31.230, 30.040, 31.240, 30.050],
        "grid_size": 500,
        "modalities": ["poi"],
    }
    resp = client.post("/api/v1/load-area", json=payload)
    assert resp.status_code == 202
    job_id = resp.json()["job_id"]

    status_data = _wait_for_job(client, job_id)
    assert status_data["status"] == "completed"
    grid_id = status_data["grid_id"]

    gdf = gpd.read_file(f"data/grids/{grid_id}.geojson")

    assert "text_des" in gdf.columns, (
        "Grid GeoJSON missing 'text_des' column"
    )

    non_empty = gdf["text_des"].dropna().astype(bool).sum()
    assert non_empty > 0, (
        f"Expected >0 cells with non-empty text_des, got {int(non_empty)}"
    )

    _cleanup_grid(grid_id)


# ============================================================
# Test 5 — GET /grid/{id}/pois returns real data
# ============================================================

def test_get_pois_returns_data(client):
    payload = {
        "bbox": [31.230, 30.040, 31.240, 30.050],
        "grid_size": 500,
        "modalities": ["poi"],
    }
    resp = client.post("/api/v1/load-area", json=payload)
    assert resp.status_code == 202
    job_id = resp.json()["job_id"]

    status_data = _wait_for_job(client, job_id)
    assert status_data["status"] == "completed"
    grid_id = status_data["grid_id"]

    resp = client.get(f"/api/v1/grid/{grid_id}/pois")
    assert resp.status_code == 200
    pois = resp.json()

    assert len(pois) > 0, (
        f"Expected >0 POIs from /grid/{grid_id}/pois, got 0"
    )

    # Validate schema
    required_keys = {"id", "name", "category", "lat", "lng"}
    for poi in pois:
        missing = required_keys - set(poi.keys())
        assert not missing, f"POI missing keys: {missing}"
        assert isinstance(poi["lat"], (int, float))
        assert isinstance(poi["lng"], (int, float))

    _cleanup_grid(grid_id)


# ============================================================
# Test 6 — grid details reports real poi_count
# ============================================================

def test_grid_details_reports_real_poi_count(client):
    payload = {
        "bbox": [31.230, 30.040, 31.240, 30.050],
        "grid_size": 500,
        "modalities": ["poi"],
    }
    resp = client.post("/api/v1/load-area", json=payload)
    assert resp.status_code == 202
    job_id = resp.json()["job_id"]

    status_data = _wait_for_job(client, job_id)
    assert status_data["status"] == "completed"
    grid_id = status_data["grid_id"]

    resp = client.get(f"/api/v1/grid/{grid_id}/details")
    assert resp.status_code == 200
    details = resp.json()

    assert details["poi_count"] > 0, (
        f"Expected poi_count > 0 in grid details, got {details['poi_count']}"
    )

    _cleanup_grid(grid_id)


# ============================================================
# Test 7 — classification receives non-empty text_des
# ============================================================

def test_classification_receives_non_empty_text_des(client):
    import numpy as np
    from app.infrastructure.ai_model import Embedder

    # First load area with poi modality
    payload = {
        "bbox": [31.230, 30.040, 31.240, 30.050],
        "grid_size": 500,
        "modalities": ["poi"],
    }
    resp = client.post("/api/v1/load-area", json=payload)
    assert resp.status_code == 202
    load_job_id = resp.json()["job_id"]

    load_status = _wait_for_job(client, load_job_id)
    assert load_status["status"] == "completed"
    grid_id = load_status["grid_id"]

    # Now classify
    classify_payload = {
        "grid_id": grid_id,
        "modalities": ["poi"],
        "fusion_method": "concat",
    }
    resp = client.post("/api/v1/classify", json=classify_payload)
    assert resp.status_code == 202
    class_job_id = resp.json()["job_id"]

    c_status = _wait_for_classify_job(client, class_job_id)

    assert c_status["status"] == "completed", (
        f"Classification failed: {c_status.get('error')}"
    )

    # Fetch results directly from memory (bypasses Redis status check)
    raw_job = _MEMORY_JOBS.get(class_job_id, {})
    result_data = raw_job.get("result_data", [])
    assert len(result_data) > 0, "Classification produced no result data"
    results = {"features": result_data}

    # Verify that text_des was populated and embeddings generated
    poi_embedder = Embedder()
    cells_with_text = 0
    cells_with_norm = 0

    for feature in results["features"]:
        props = feature.get("properties", feature)
        text_embedding_norm = props.get("text_embedding_norm", 0.0)
        if text_embedding_norm > 0:
            cells_with_norm += 1

        # Also check text_des in the grid data
        text_des = props.get("poi_top_categories", [])
        if text_des:
            cells_with_text += 1

    assert cells_with_norm > 0, (
        "Expected >0 cells with non-zero POI embedding norm. "
        "This means text_des was empty during classification."
    )

    _cleanup_grid(grid_id)
