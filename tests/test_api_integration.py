"""
 * Integration Tests for the API endpoints.
 """
import pytest
from fastapi.testclient import TestClient
from app.main import app
import time

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "app": "MLLM-Geo-AI-App"}

def test_load_area_and_classify_flow():
    # 1. Start load-area job
    payload = {
        "bbox": [31.1, 30.0, 31.15, 30.05],  # Smaller area for test (< 500 cells)
        "grid_size": 1000,
        "modalities": []  # Empty for test to avoid real downloads
    }
    response = client.post("/api/v1/load-area", json=payload)
    assert response.status_code == 202
    data = response.json()
    job_id = data["job_id"]
    
    # 2. Poll until completed (since modalities=[], it's fast)
    max_retries = 20
    status_data = {}
    for _ in range(max_retries):
        status_res = client.get(f"/api/v1/area-status/{job_id}")
        assert status_res.status_code == 200
        status_data = status_res.json()
        if status_data["status"] in ["completed", "failed"]:
            break
        time.sleep(0.5)
        
    assert status_data["status"] == "completed"
    grid_id = status_data["grid_id"]
    
    # 3. Start classify job
    classify_payload = {
        "grid_id": grid_id,
        "modalities": []
    }
    class_res = client.post("/api/v1/classify", json=classify_payload)
    assert class_res.status_code == 202
    class_job_id = class_res.json()["job_id"]
    
    # 4. Poll classify status (since mock, it's fast)
    c_status_data = {}
    for _ in range(max_retries):
        c_status_res = client.get(f"/api/v1/classify-status/{class_job_id}")
        assert c_status_res.status_code == 200
        c_status_data = c_status_res.json()
        if c_status_data["status"] in ["completed", "failed"]:
            break
        time.sleep(0.5)
        
    assert c_status_data["status"] == "completed"
    
    # 5. Fetch result
    res_url = client.get(f"/api/v1/classification-result/{class_job_id}")
    assert res_url.status_code == 200
    assert "FeatureCollection" == res_url.json()["type"]
