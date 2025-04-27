from fastmcp import FastMCP, Client

# Instanciation du serveur FastMCP
mcp = FastMCP("Mon Serveur MCP")

@mcp.tool()
def greet(name: str) -> str:
    """Renvoie un message de bienvenue personnalisé."""
    return f"Bonjour, {name}!"

# Création du client permettant d'appeler les outils du serveur
client = Client(mcp)

async def execute_tool(tool_name: str, params: dict):
    """
    Exécute un outil via le client FastMCP.
    
    Args:
        tool_name (str): Nom de l'outil à exécuter
        params (dict): Paramètres à passer à l'outil
        
    Returns:
        Le résultat de l'exécution de l'outil
    """
    async with client:
        result = await client.call_tool(tool_name, params)
        return result

if __name__ == "__main__":
    # Démarrer le serveur en mode standalone
    mcp.run()