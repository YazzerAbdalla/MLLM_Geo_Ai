import pytest

def test_train_start(client, monkeypatch):
    response = client.post("/api/v1/mllm/train", json={
        "model_name": "tiny-llm",
        "dataset_path": "data/dataset.csv"
    })
    # If TASKS_AVAILABLE is False, it might return 501
    assert response.status_code in [202, 501]
    if response.status_code == 202:
        data = response.json()
        assert "job_id" in data

def test_train_status(client, monkeypatch):
    from app.infrastructure.job_store import job_store
    monkeypatch.setattr(job_store, "get_job", lambda x: {"id": x, "status": "running", "step": "training", "progress": 0.5, "error": None})
    response = client.get("/api/v1/mllm/train-status/job_123")
    assert response.status_code == 200
    assert response.json()["status"] == "running"

def test_train_cancel(client, monkeypatch):
    # This hits /jobs/{job_id} DELETE
    from app.infrastructure.job_store import job_store
    monkeypatch.setattr(job_store, "get_job", lambda x: {"id": x, "celery_task_id": "task_123"})
    monkeypatch.setattr(job_store, "update_job", lambda *a, **k: None)
    response = client.delete("/api/v1/jobs/job_123")
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"

def test_train_complete(client, monkeypatch):
    from app.infrastructure.job_store import job_store
    monkeypatch.setattr(job_store, "get_job", lambda x: {"id": x, "status": "completed", "step": "done", "progress": 1.0, "error": None, "result_url": "/some/url"})
    response = client.get("/api/v1/mllm/train-status/job_123")
    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert "result_url" in response.json()
