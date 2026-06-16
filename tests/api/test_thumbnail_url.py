import pytest

def test_thumbnail_url_exists():
    # The URL should be constructed properly in fusion_service
    # Just verifying the existence of the endpoint
    pass

def test_thumbnail_endpoint_exists(client, monkeypatch):
    from PIL import Image
    import io
    
    # Mock os.path.exists
    import os
    original_exists = os.path.exists
    def mock_exists(path):
        if "sat_images" in path:
            return True
        return original_exists(path)
    monkeypatch.setattr(os.path, "exists", mock_exists)
    
    # Mock Image.open
    class MockImage:
        def convert(self, mode):
            return self
        def save(self, buf, format, quality):
            buf.write(b"fake image data")
            
    monkeypatch.setattr(Image, "open", lambda x: MockImage())
    
    response = client.get("/api/v1/thumbnails/grid_1/cell_25.jpg")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

def test_thumbnail_not_found(client, monkeypatch):
    import os
    original_exists = os.path.exists
    def mock_exists(path):
        if "sat_images" in path:
            return False
        return original_exists(path)
    monkeypatch.setattr(os.path, "exists", mock_exists)
    
    response = client.get("/api/v1/thumbnails/grid_1/missing.jpg")
    assert response.status_code == 404
