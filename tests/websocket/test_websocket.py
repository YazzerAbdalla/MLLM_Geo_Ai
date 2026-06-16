import pytest
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect
from app.main import app
from app.infrastructure.job_store import job_store

client = TestClient(app)

def test_websocket_connection_test(monkeypatch):
    monkeypatch.setattr(job_store, "get_job", lambda x: {"id": x, "status": "running"})
    with client.websocket_connect("/api/v1/ws/progress/abc12345") as websocket:
        pass

def test_websocket_invalid_job_test():
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect("/api/v1/ws/progress/invalid-job-id") as websocket:
            websocket.receive_text()
    assert exc_info.value.code == 4004

@pytest.mark.skip(reason="TODO: needs Redis running for pub/sub progress events")
def test_websocket_progress_event_test():
    pass

@pytest.mark.skip(reason="TODO: needs Redis running for pub/sub completion events")
def test_websocket_completion_event_test():
    pass

@pytest.mark.skip(reason="TODO: needs Redis running for pub/sub disconnect cleanup")
def test_websocket_disconnect_test():
    pass
