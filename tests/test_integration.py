import pytest
import requests
import subprocess
import time
import os
import signal

@pytest.fixture(scope="module")
def server_process():
    """Fixture pour démarrer et arrêter les serveurs pour les tests d'intégration."""
    # Démarre le serveur FastMCP en arrière-plan
    mcp_process = subprocess.Popen(["python", "server.py"])
    # Démarre l'API web en arrière-plan
    api_process = subprocess.Popen(["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"])
    
    # Attendre que les serveurs démarrent
    time.sleep(5)
    
    yield
    
    # Arrêter les serveurs
    os.kill(api_process.pid, signal.SIGTERM)
    os.kill(mcp_process.pid, signal.SIGTERM)
    api_process.wait()
    mcp_process.wait()

@pytest.mark.integration
def test_end_to_end(server_process):
    """Test d'intégration de bout en bout."""
    # Tester l'appel à l'API
    response = requests.post(
        "http://localhost:8000/call_tool/",
        json={"tool_name": "greet", "params": {"name": "IntegrationTest"}}
    )
    assert response.status_code == 200
    assert "result" in response.json()
    assert response.json()["result"] == "Bonjour, IntegrationTest!"
