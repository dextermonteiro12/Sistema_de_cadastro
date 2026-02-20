# api-gateway/tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def client():
    """Fixture para TestClient"""
    return TestClient(app)

@pytest.fixture
def test_config_key():
    """Config key para testes"""
    return "test-config-key"

@pytest.fixture
def valid_headers(test_config_key):
    """Headers válidos para testes"""
    return {"X-Config-Key": test_config_key}