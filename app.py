from fastapi import FastAPI, HTTPException, Depends, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import timedelta
import time
import asyncio
import uvicorn

# Imports des fonctionnalites avancées
from server import execute_tool, get_available_tools, health_check as fastmcp_health_check
from config import config
from auth import authenticate_user, get_current_active_user, create_access_token, Token, User, users_db
from logging_config import logger, setup_logger
from monitoring import PrometheusMiddleware, start_monitoring, get_health_status
from cache import start_cache_cleanup, get_cache_stats, tool_cache_manager
from resilience import CircuitBreakerError, get_all_circuit_breakers_state, reset_circuit_breaker

# Durée de validité du token (30 minutes)
ACCESS_TOKEN_EXPIRE_MINUTES = config.security.access_token_expire_minutes

# Création de l'application FastAPI
app = FastAPI(
    title="Interface Web FastMCP",
    description="Une interface web intuitive pour FastMCP, permettant aux utilisateurs novices d'utiliser FastMCP sans complexité technique.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    root_path=config.api.root_path
)

# Ajout des middlewares
app.add_middleware(GZipMiddleware, minimum_size=1000)  # Compression Gzip pour les réponses > 1KB

# Configuration CORS pour permettre les requêtes depuis le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.security.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ajout du middleware Prometheus pour les métriques
app.add_middleware(PrometheusMiddleware)

# Middleware pour la limitation de débit (rate limiting)
if config.security.rate_limiting_enabled:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from slowapi.util import get_remote_address
    
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Modeles de données
class ToolRequest(BaseModel):
    tool_name: str
    params: Dict[str, Any]

class ToolParameter(BaseModel):
    name: str
    type: str
    description: str
    required: bool = True

class Tool(BaseModel):
    name: str
    description: str
    parameters: List[ToolParameter]
    cachable: bool = False
    cache_ttl: Optional[int] = None

class CircuitBreakerState(BaseModel):
    name: str
    state: str
    failure_count: int
    failure_threshold: int
    recovery_timeout: int
    last_failure: Optional[float] = None
    last_success: float
    seconds_since_last_failure: Optional[float] = None
    seconds_since_last_success: float

# Middleware pour mesurer la durée des requêtes
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"Erreur lors du traitement de la requête {request.url.path}: {str(e)}")
        raise

# Endpoint d'authentification
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Endpoint pour obtenir un token d'accès."""
    user = authenticate_user(users_db, form_data.username, form_data.password)
    if not user:
        logger.warning(f"Tentative de connexion échouée pour l'utilisateur {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nom d'utilisateur ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    logger.info(f"Utilisateur {user.username} connecté avec succès")
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Endpoint pour récupérer les informations de l'utilisateur connecté."""
    return current_user

# Dépendance conditionnelle pour l'authentification
def get_auth_dependency():
    """Retourne la dépendance d'authentification si elle est activée, sinon None."""
    if config.security.auth_enabled:
        return Depends(get_current_active_user)
    return None

# Récupérer la dépendance d'authentification
auth_dependency = get_auth_dependency()

# Endpoint pour appeler un outil - avec rate limiting si activé
if config.security.rate_limiting_enabled:
    @app.post("/call_tool/")
    @limiter.limit(f"{config.security.rate_limit_requests}/{config.security.rate_limit_window}s")
    async def call_tool_endpoint(request: Request, tool_req: ToolRequest, current_user: Optional[User] = auth_dependency):
        return await _call_tool(tool_req)
else:
    @app.post("/call_tool/")
    async def call_tool_endpoint(tool_req: ToolRequest, current_user: Optional[User] = auth_dependency):
        return await _call_tool(tool_req)

# Fonction interne pour traiter l'appel d'outil
async def _call_tool(tool_req: ToolRequest):
    """Traitement de l'appel d'outil."""
    logger.info(f"Appel de l'outil {tool_req.tool_name} avec les paramètres {tool_req.params}")
    try:
        result = await execute_tool(tool_req.tool_name, tool_req.params)
        logger.info(f"Résultat de l'outil {tool_req.tool_name}: {result}")
        return {"result": result}
    except CircuitBreakerError as e:
        logger.error(f"Circuit ouvert pour l'outil {tool_req.tool_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail=f"Service temporairement indisponible: {str(e)}",
            headers={"Retry-After": str(config.resilience.recovery_timeout)}
        )
    except ValueError as e:
        logger.error(f"Erreur de validation pour l'outil {tool_req.tool_name}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Erreur lors de l'appel de l'outil {tool_req.tool_name}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.get("/list_tools/", response_model=Dict[str, List[Tool]])
async def list_tools_endpoint(current_user: Optional[User] = auth_dependency):
    """Endpoint pour lister tous les outils disponibles."""
    logger.info("Liste des outils demandée")
    try:
        tools = await get_available_tools()
        return {"tools": tools}
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des outils: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Endpoint d'administration - accessibles uniquement si authenticated
@app.get("/admin/health", response_model=Dict[str, Any])
async def admin_health_check(current_user: User = Depends(get_current_active_user)):
    """Vérifie l'état de santé détaillé de l'application."""
    fastmcp_status = await fastmcp_health_check()
    system_status = get_health_status()
    
    return {
        "status": "ok" if fastmcp_status["status"] == "healthy" and system_status["status"] == "ok" else "degraded",
        "fastmcp": fastmcp_status,
        "system": system_status,
        "config": {
            "auth_enabled": config.security.auth_enabled,
            "cache_enabled": config.cache.enabled,
            "monitoring_enabled": config.monitoring.enabled,
            "rate_limiting_enabled": config.security.rate_limiting_enabled,
            "resilience_enabled": {
                "circuit_breaker": config.resilience.circuit_breaker_enabled,
                "retry": config.resilience.retry_enabled
            }
        }
    }

@app.get("/admin/cache", response_model=Dict[str, Any])
async def admin_cache_stats(current_user: User = Depends(get_current_active_user)):
    """Récupère les statistiques du cache."""
    return await get_cache_stats()

@app.post("/admin/cache/invalidate")
async def admin_invalidate_cache(tool_name: Optional[str] = None, current_user: User = Depends(get_current_active_user)):
    """Invalide le cache pour un outil spécifique ou pour tous les outils."""
    result = await tool_cache_manager.invalidate_tool_cache(tool_name)
    return {"success": result, "message": f"Cache invalidé pour {'tous les outils' if tool_name is None else tool_name}"}

@app.get("/admin/circuit-breakers", response_model=Dict[str, CircuitBreakerState])
async def admin_circuit_breakers(current_user: User = Depends(get_current_active_user)):
    """Récupère l'état de tous les circuit breakers."""
    return get_all_circuit_breakers_state()

@app.post("/admin/circuit-breakers/reset/{name}")
async def admin_reset_circuit_breaker(name: str, current_user: User = Depends(get_current_active_user)):
    """Réinitialise un circuit breaker spécifique."""
    result = reset_circuit_breaker(name)
    return {"success": result, "message": f"Circuit breaker {name} {'réinitialisé' if result else 'non trouvé'}"}

# Vérification basique de l'état de santé (endpoint public)
@app.get("/health")
async def health_check():
    """Endpoint pour vérifier l'état de santé de l'API."""
    try:
        fastmcp_status = await fastmcp_health_check()
        if fastmcp_status["status"] == "healthy":
            return {"status": "ok"}
        else:
            return {"status": "degraded", "message": "FastMCP service is not healthy"}
    except Exception as e:
        logger.error(f"Erreur lors de la vérification de l'état de santé: {str(e)}")
        return {"status": "error", "message": str(e)}

# Version de l'API
@app.get("/version")
async def version():
    """Retourne la version de l'API."""
    return {"version": "1.0.0", "name": "FastMCP Web Interface"}

# Servir les fichiers statiques
app.mount("/static", StaticFiles(directory="static"), name="static")

# Servir le fichier index.html à la racine
@app.get("/")
async def read_index():
    logger.info("Page d'accueil demandée")
    return FileResponse('index.html')

@app.on_event("startup")
async def startup_event():
    """Actions à exécuter au démarrage de l'application."""
    # Configuration du logger
    logger.info("Démarrage de l'API FastMCP Web Interface")
    
    # Démarrage du monitoring si activé
    if config.monitoring.enabled:
        start_monitoring(port=config.monitoring.prometheus_port)
        logger.info(f"Monitoring activé sur le port {config.monitoring.prometheus_port}")
    
    # Démarrage du nettoyage du cache
    if config.cache.enabled:
        start_cache_cleanup()
        logger.info("Système de cache activé")
        
        # Enregistrement des outils cachables
        for tool_name, ttl in config.cache.tools_config.items():
            tool_cache_manager.register_tool(tool_name, ttl)
            logger.info(f"Outil '{tool_name}' enregistré comme cachable avec TTL={ttl}s")

@app.on_event("shutdown")
async def shutdown_event():
    """Actions à exécuter à l'arrêt de l'application."""
    logger.info("Arrêt de l'API FastMCP Web Interface")

if __name__ == "__main__":
    # Démarrer l'API web
    logger.info(f"Démarrage de l'API sur {config.api.host}:{config.api.port}")
    uvicorn.run(
        "app:app", 
        host=config.api.host, 
        port=config.api.port, 
        reload=config.api.reload,
        workers=config.api.workers,
        log_level=config.api.log_level
    )