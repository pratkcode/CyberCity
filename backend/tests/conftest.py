import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client() -> TestClient:
    # A fresh app per test keeps in-memory simulation state isolated.
    return TestClient(create_app())
