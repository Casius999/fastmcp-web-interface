import time
import asyncio
import hashlib
import json
from typing import Any, Dict, Optional, Tuple, Callable, Union, List
from functools import wraps
from redis import asyncio as aioredis
from logging_config import logger
from config import config

# Configuration du client Redis
redis_client = None

# Tentative de connexion à Redis, mais fallback sur un cache en mémoire si indisponible
try:
    redis_url = config.cache.redis_url if hasattr(config, 'cache') and hasattr(config.cache, 'redis_url') else None
    USE_REDIS = redis_url is not None
    
    if USE_REDIS:
        redis_client = aioredis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        logger.info(f"Cache Redis configuré sur {redis_url}")
    else:
        logger.info("Redis non configuré, utilisation du cache en mémoire")
        
except Exception as e:
    USE_REDIS = False
    logger.warning(f"Impossible de se connecter à Redis: {str(e)}. Utilisation du cache en mémoire.")

# Cache en mémoire (fallback si Redis n'est pas disponible)
MEMORY_CACHE: Dict[str, Tuple[Any, float]] = {}

async def get_from_cache(key: str) -> Optional[Any]:
    """Récupère une valeur du cache."""
    if USE_REDIS and redis_client:
        try:
            # Tenter de récupérer du cache Redis
            data = await redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du cache Redis: {str(e)}")
            return None
    else:
        # Utiliser le cache en mémoire
        if key in MEMORY_CACHE:
            value, expiry = MEMORY_CACHE[key]
            if expiry == 0 or expiry > time.time():
                return value
            # Supprimer les entrées expirées
            del MEMORY_CACHE[key]
        return None

async def set_in_cache(key: str, value: Any, ttl: int = 3600) -> bool:
    """Stocke une valeur dans le cache avec une durée de vie (TTL) en secondes."""
    try:
        serialized_value = json.dumps(value)
        
        if USE_REDIS and redis_client:
            await redis_client.set(key, serialized_value, ex=ttl if ttl > 0 else None)
        else:
            # Calculer l'expiration pour le cache en mémoire
            expiry = time.time() + ttl if ttl > 0 else 0
            MEMORY_CACHE[key] = (value, expiry)
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la mise en cache: {str(e)}")
        return False

async def delete_from_cache(key: str) -> bool:
    """Supprime une valeur du cache."""
    try:
        if USE_REDIS and redis_client:
            await redis_client.delete(key)
        elif key in MEMORY_CACHE:
            del MEMORY_CACHE[key]
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la suppression du cache: {str(e)}")
        return False

async def clear_cache() -> bool:
    """Vide entièrement le cache."""
    try:
        if USE_REDIS and redis_client:
            await redis_client.flushdb()
        else:
            MEMORY_CACHE.clear()
        return True
    except Exception as e:
        logger.error(f"Erreur lors du vidage du cache: {str(e)}")
        return False

def generate_cache_key(func_name: str, args: Tuple, kwargs: Dict) -> str:
    """Génère une clé de cache basée sur le nom de la fonction et ses arguments."""
    # Créer une représentation JSON des arguments
    args_str = json.dumps(args, sort_keys=True)
    kwargs_str = json.dumps(kwargs, sort_keys=True)
    
    # Générer un hash de la combinaison
    key_base = f"{func_name}:{args_str}:{kwargs_str}"
    return hashlib.md5(key_base.encode()).hexdigest()

def cached(ttl: int = 3600, key_prefix: str = ""):
    """Décorateur pour mettre en cache le résultat d'une fonction asynchrone."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Générer la clé de cache
            cache_key = f"{key_prefix}:{generate_cache_key(func.__name__, args, kwargs)}"
            
            # Vérifier si le résultat est dans le cache
            cached_result = await get_from_cache(cache_key)
            if cached_result is not None:
                logger.debug(f"Résultat récupéré du cache pour {func.__name__}")
                return cached_result
            
            # Exécuter la fonction et mettre en cache le résultat
            result = await func(*args, **kwargs)
            await set_in_cache(cache_key, result, ttl)
            return result
        return wrapper
    return decorator

# Classe pour gérer le cache des outils FastMCP
class ToolCacheManager:
    def __init__(self, default_ttl: int = 3600):
        self.default_ttl = default_ttl
        self.cacheable_tools: Dict[str, int] = {}
    
    def register_tool(self, tool_name: str, ttl: int = None):
        """Enregistre un outil comme étant cacheable avec un TTL spécifique."""
        self.cacheable_tools[tool_name] = ttl if ttl is not None else self.default_ttl
    
    def is_tool_cacheable(self, tool_name: str) -> bool:
        """Vérifie si un outil est cacheable."""
        return tool_name in self.cacheable_tools
    
    def get_tool_ttl(self, tool_name: str) -> int:
        """Récupère le TTL pour un outil."""
        return self.cacheable_tools.get(tool_name, self.default_ttl)
    
    async def get_cached_result(self, tool_name: str, params: Dict) -> Optional[Any]:
        """Récupère le résultat mis en cache pour un outil avec des paramètres spécifiques."""
        if not self.is_tool_cacheable(tool_name):
            return None
        
        cache_key = f"tool:{tool_name}:{generate_cache_key('', (), params)}"
        return await get_from_cache(cache_key)
    
    async def cache_tool_result(self, tool_name: str, params: Dict, result: Any) -> bool:
        """Met en cache le résultat d'un outil."""
        if not self.is_tool_cacheable(tool_name):
            return False
        
        cache_key = f"tool:{tool_name}:{generate_cache_key('', (), params)}"
        ttl = self.get_tool_ttl(tool_name)
        return await set_in_cache(cache_key, result, ttl)
    
    async def invalidate_tool_cache(self, tool_name: str = None) -> bool:
        """Invalide le cache pour un outil spécifique ou pour tous les outils."""
        try:
            if tool_name:
                if USE_REDIS and redis_client:
                    # Utiliser les motifs de clés Redis
                    cursor = 0
                    pattern = f"tool:{tool_name}:*"
                    while True:
                        cursor, keys = await redis_client.scan(cursor, match=pattern)
                        if keys:
                            await redis_client.delete(*keys)
                        if cursor == 0:
                            break
                else:
                    # Pour le cache en mémoire, trouver et supprimer les clés correspondantes
                    pattern = f"tool:{tool_name}:"
                    keys_to_delete = [k for k in MEMORY_CACHE.keys() if k.startswith(pattern)]
                    for k in keys_to_delete:
                        del MEMORY_CACHE[k]
            else:
                # Invalider tous les caches d'outils
                if USE_REDIS and redis_client:
                    cursor = 0
                    pattern = "tool:*"
                    while True:
                        cursor, keys = await redis_client.scan(cursor, match=pattern)
                        if keys:
                            await redis_client.delete(*keys)
                        if cursor == 0:
                            break
                else:
                    # Pour le cache en mémoire
                    pattern = "tool:"
                    keys_to_delete = [k for k in MEMORY_CACHE.keys() if k.startswith(pattern)]
                    for k in keys_to_delete:
                        del MEMORY_CACHE[k]
            
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'invalidation du cache d'outil: {str(e)}")
            return False

# Nettoyage périodique du cache en mémoire
async def cleanup_memory_cache():
    """Nettoie périodiquement les entrées expirées du cache en mémoire."""
    while True:
        try:
            now = time.time()
            keys_to_delete = []
            
            for key, (_, expiry) in MEMORY_CACHE.items():
                if expiry != 0 and expiry < now:
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                del MEMORY_CACHE[key]
            
            # Nettoyer toutes les 10 minutes
            await asyncio.sleep(600)
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage du cache en mémoire: {str(e)}")
            await asyncio.sleep(600)

# Créer une instance du gestionnaire de cache d'outils
tool_cache_manager = ToolCacheManager()

# Fonction pour démarrer le nettoyage du cache en arrière-plan
def start_cache_cleanup():
    """Démarre la tâche de nettoyage du cache en arrière-plan."""
    if not USE_REDIS:
        asyncio.create_task(cleanup_memory_cache())

# Fonction pour vérifier l'état du cache
async def get_cache_stats() -> Dict[str, Any]:
    """Récupère des statistiques sur l'état du cache."""
    try:
        if USE_REDIS and redis_client:
            info = await redis_client.info()
            keys = await redis_client.dbsize()
            return {
                "type": "redis",
                "connected": True,
                "keys": keys,
                "memory_used": info.get("used_memory_human", "N/A"),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "cacheable_tools": list(tool_cache_manager.cacheable_tools.keys())
            }
        else:
            return {
                "type": "memory",
                "connected": True,
                "keys": len(MEMORY_CACHE),
                "memory_estimate": f"{len(str(MEMORY_CACHE)) / 1024:.2f} KB",
                "cacheable_tools": list(tool_cache_manager.cacheable_tools.keys())
            }
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des statistiques du cache: {str(e)}")
        return {
            "type": "unknown",
            "connected": False,
            "error": str(e)
        }