from fastmcp import FastMCP, Client
import inspect
import asyncio
from typing import Dict, Any, List, Optional

# Imports des fonctionnalités avancées
from logging_config import logger
from config import config
from resilience import resilient, CircuitBreakerError
from cache import tool_cache_manager
from monitoring import track_tool_execution, set_fastmcp_client_pool_size

# Instanciation du serveur FastMCP
mcp = FastMCP(config.server.name)

# Configuration des outils cachables
tool_cache_manager.register_tool("greet", config.cache.tools_config.get("greet", 86400))  # 24h par défaut
tool_cache_manager.register_tool("calculate", config.cache.tools_config.get("calculate", 3600))  # 1h par défaut

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

# Pool de clients FastMCP
class ClientPool:
    def __init__(self, server: FastMCP, max_size: int = 10):
        self.server = server
        self.max_size = max_size
        self.clients: List[Client] = []
        self.available_clients: asyncio.Queue = asyncio.Queue()
        self.lock = asyncio.Lock()  # Verrou pour la création de nouveaux clients
        
        # Initialiser le pool avec quelques clients
        for _ in range(min(3, max_size)):
            client = Client(server)
            self.clients.append(client)
            self.available_clients.put_nowait(client)
        
        # Mettre à jour la métrique
        set_fastmcp_client_pool_size(len(self.clients))
    
    async def get_client(self) -> Client:
        """Obtient un client du pool, ou en crée un nouveau si nécessaire."""
        try:
            # Essayer d'obtenir un client disponible
            return await asyncio.wait_for(self.available_clients.get(), timeout=1.0)
        except asyncio.TimeoutError:
            # Si timeout, vérifier si on peut créer un nouveau client
            async with self.lock:
                if len(self.clients) < self.max_size:
                    logger.info(f"Création d'un nouveau client FastMCP (total: {len(self.clients) + 1})")
                    client = Client(self.server)
                    self.clients.append(client)
                    # Mettre à jour la métrique
                    set_fastmcp_client_pool_size(len(self.clients))
                    return client
                else:
                    logger.warning(f"Taille maximale du pool de clients atteinte ({self.max_size})")
                    # Si on ne peut pas créer de nouveau client, attendre qu'un client se libère
                    return await self.available_clients.get()
    
    def release_client(self, client: Client):
        """Libère un client et le remet dans le pool."""
        self.available_clients.put_nowait(client)

# Création du pool de clients
client_pool = ClientPool(mcp, max_size=config.server.max_connections)

@resilient(circuit_name="fastmcp_execute_tool")
@track_tool_execution
async def execute_tool(tool_name: str, params: dict):
    """
    Exécute un outil via le client FastMCP.
    
    Args:
        tool_name (str): Nom de l'outil à exécuter
        params (dict): Paramètres à passer à l'outil
        
    Returns:
        Le résultat de l'exécution de l'outil
    """
    # Vérifier si le résultat est dans le cache
    if config.cache.enabled:
        cached_result = await tool_cache_manager.get_cached_result(tool_name, params)
        if cached_result is not None:
            logger.info(f"Résultat trouvé dans le cache pour l'outil {tool_name}")
            return cached_result
    
    # Exécuter l'outil si pas dans le cache
    client = await client_pool.get_client()
    try:
        async with client:
            logger.debug(f"Exécution de l'outil {tool_name} avec params {params}")
            result = await client.call_tool(tool_name, params)
            logger.debug(f"Résultat de l'outil {tool_name}: {result}")
            
            # Mettre en cache le résultat si applicable
            if config.cache.enabled:
                await tool_cache_manager.cache_tool_result(tool_name, params, result)
                
            return result
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution de l'outil {tool_name}: {str(e)}")
        raise
    finally:
        # Remettre le client dans le pool
        client_pool.release_client(client)

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
            
            # Trouver la description du paramètre dans la docstring si possible
            param_description = f"Paramètre {param_name}"
            
            # Ajouter le paramètre à la liste
            parameters.append({
                "name": param_name,
                "type": param_type,
                "description": param_description,
                "required": required
            })
        
        # Ajouter l'outil à la liste avec cachable state
        is_cachable = tool_cache_manager.is_tool_cacheable(tool_name)
        cache_ttl = tool_cache_manager.get_tool_ttl(tool_name) if is_cachable else None
        
        tools.append({
            "name": tool_name,
            "description": description.strip(),
            "parameters": parameters,
            "cachable": is_cachable,
            "cache_ttl": cache_ttl
        })
    
    return tools

async def health_check() -> Dict[str, Any]:
    """Vérifie l'état de santé du serveur FastMCP."""
    try:
        client = await client_pool.get_client()
        try:
            async with client:
                # Test simple d'appel d'outil
                result = await client.call_tool("greet", {"name": "HealthCheck"})
                return {
                    "status": "healthy",
                    "server_name": config.server.name,
                    "tools_count": len(mcp.tools),
                    "clients_pool_size": len(client_pool.clients),
                    "available_clients": client_pool.available_clients.qsize()
                }
        except Exception as e:
            logger.error(f"Erreur lors du health check: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
        finally:
            client_pool.release_client(client)
    except Exception as e:
        logger.error(f"Impossible d'obtenir un client pour le health check: {str(e)}")
        return {
            "status": "unhealthy",
            "error": f"Pas de client disponible: {str(e)}"
        }

if __name__ == "__main__":
    # Démarrer le serveur en mode standalone
    logger.info(f"Démarrage du serveur FastMCP {config.server.name} sur {config.server.host}:{config.server.port}")
    mcp.run()