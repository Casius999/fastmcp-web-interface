from fastapi.testclient import TestClient
import pytest
from app import app

client = TestClient(app)

def test_read_index():
    """Test pour vérifier que la page d'accueil est correctement servie."""
    response = client.get("/")
    assert response.status_code == 200
    assert "<!DOCTYPE html>" in response.text
    assert "Interface FastMCP" in response.text

def test_call_tool_endpoint_success():
    """Test pour vérifier que l'endpoint call_tool fonctionne correctement."""
    response = client.post(
        "/call_tool/",
        json={"tool_name": "greet", "params": {"name": "TestUser"}}
    )
    assert response.status_code == 200
    assert "result" in response.json()
    assert "Bonjour, TestUser!" in response.json()["result"]

def test_call_tool_endpoint_error():
    """Test pour vérifier que les erreurs sont correctement gérées."""
    response = client.post(
        "/call_tool/",
        json={"tool_name": "non_existent_tool", "params": {}}
    )
    assert response.status_code == 400
    assert "detail" in response.json()

def test_list_tools_endpoint():
    """Test pour vérifier que l'endpoint list_tools fonctionne correctement."""
    response = client.get("/list_tools/")
    assert response.status_code == 200
    assert "tools" in response.json()
    assert len(response.json()["tools"]) > 0
    assert response.json()["tools"][0]["name"] == "greet"
