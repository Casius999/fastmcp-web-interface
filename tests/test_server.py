import pytest
from fastmcp import FastMCP, Client
import asyncio
from server import execute_tool, mcp

@pytest.mark.asyncio
async def test_execute_tool():
    """Test pour vérifier que la fonction execute_tool fonctionne correctement."""
    result = await execute_tool("greet", {"name": "Test"})
    assert result == "Bonjour, Test!"
    
@pytest.mark.asyncio
async def test_greet_tool():
    """Test pour vérifier que l'outil greet fonctionne correctement."""
    # Créer un client de test
    client = Client(mcp)
    async with client:
        result = await client.call_tool("greet", {"name": "TestUser"})
        assert result == "Bonjour, TestUser!"
