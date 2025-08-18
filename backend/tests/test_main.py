# Placeholder for test_main.py
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_network_status():
    response = client.get("/network/status")
    assert response.status_code == 200
    assert "ok" in response.json()
