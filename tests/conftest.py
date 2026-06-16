import sys
from unittest.mock import MagicMock
sys.modules['ee'] = MagicMock()

import platform
platform.uname = MagicMock(return_value=MagicMock(system='Windows'))
platform.system = MagicMock(return_value='Windows')

import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)
