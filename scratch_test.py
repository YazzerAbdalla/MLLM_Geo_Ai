print("Starting test")
from fastapi.testclient import TestClient
print("Imported TestClient")
from app.main import app

print("Imported app")
try:
    client = TestClient(app)
    print("Created TestClient")
    with client.websocket_connect("/api/v1/ws/progress/abc12345") as websocket:
        print("Connected to websocket")
except Exception as e:
    print(f"Error: {e}")
print("Done")
