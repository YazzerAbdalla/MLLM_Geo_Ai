import pytest

def test_query_success(client, monkeypatch):
    from app.infrastructure.job_store import job_store
    monkeypatch.setattr(job_store, "get_grid", lambda x: {"gdf": []})
    
    response = client.post("/api/v1/query", json={"question": "Show commercial hotspots", "grid_id": "grid_1"})
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] is not None
    assert data["query_type"] == "general"
    assert data["confidence"] == 0.85

def test_query_empty_question(client):
    response = client.post("/api/v1/query", json={"question": "   ", "grid_id": "grid_1"})
    assert response.status_code == 400

def test_query_invalid_grid(client, monkeypatch):
    from app.infrastructure.job_store import job_store
    monkeypatch.setattr(job_store, "get_grid", lambda x: None)
    
    response = client.post("/api/v1/query", json={"question": "Show commercial hotspots", "grid_id": "invalid_grid"})
    assert response.status_code == 404
