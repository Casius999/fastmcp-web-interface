from fastmcp import FastMCP, Client
import inspect
from logging_config import logger
from config import config

# Instanciation du serveur FastMCP
mcp = FastMCP(config.server.name)

@mcp.tool()
def greet(name: str) -> str:
    """Renvoie un message de bienvenue personnalisé."""
    logger.info(f"Outil greet appelé avec nom={name}")
    return f"Bonjour, {name}!"

@mcp.tool()
def calculate(operation: str, a: float, b: float) -> float:
    """Effectue une opération mathématique de base.
    
    Paramètres:
    - operation: Type d'opération (add, subtract, multiply, divide)
    - a: Premier nombre
    - b: Deuxième nombre
    """
    logger.info(f"Outil calculate appelé avec operation={operation}, a={a}, b={b}")
    
    if operation.lower() == "add":
        return a + b
    elif operation.lower() == "subtract":
        return a - b
    elif operation.lower() == "multiply":
        return a * b
    elif operation.lower() == "divide":
        if b == 0:
            raise ValueError("Division par zéro impossible")
        return a / b
    else:
        raise ValueError(f"Opération non reconnue: {operation}")

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
    logger.debug(f"Exécution de l'outil {tool_name} avec params {params}")
    async with client:
        try:
            result = await client.call_tool(tool_name, params)
            logger.debug(f"Résultat de l'outil {tool_name}: {result}")
            return result
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution de l'outil {tool_name}: {str(e)}")
            raise

async def get_available_tools():
    """
    Récupère la liste des outils disponibles avec leurs métadonnées.
    
    Returns:
        list: Liste des outils disponibles avec leurs descriptions et paramètres
    """
    tools = []
    # Parcourir les outils enregistrés dans le serveur MCP
    for tool_name, tool_func in mcp.tools.items():
        # Récupérer la signature de la fonction pour les paramètres
        sig = inspect.signature(tool_func)
        # Récupérer la docstring pour la description
        description = tool_func.__doc__ or f"Outil {tool_name}"
        
        parameters = []
        for param_name, param in sig.parameters.items():
            # Exclure le paramètre 'self' pour les méthodes de classe
            if param_name == 'self':
                continue
                
            # Déterminer le type de paramètre
            param_type = "any"
            if param.annotation != inspect.Parameter.empty:
                param_type = str(param.annotation).replace("<class '", "").replace("'>", "")
            
            # Vérifier si le paramètre est requis ou optionnel
            required = param.default == inspect.Parameter.empty
            
            # Ajouter le paramètre à la liste
            parameters.append({
                "name": param_name,
                "type": param_type,
                "description": f"Paramètre {param_name}",
                "required": required
            })
        
        # Ajouter l'outil à la liste
        tools.append({
            "name": tool_name,
            "description": description.strip(),
            "parameters": parameters
        })
    
    return tools

if __name__ == "__main__":
    # Démarrer le serveur en mode standalone
    logger.info(f"Démarrage du serveur FastMCP sur {config.server.host}:{config.server.port}")
    mcp.run()