from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional
from server import execute_tool, get_available_tools
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from datetime import timedelta

# Imports pour la sécurité et la configuration
from config import config
from auth import authenticate_user, get_current_active_user, create_access_token, Token, User
from logging_config import logger

# Durée de validité du token (30 minutes)
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Création de l'application FastAPI
app = FastAPI(
    title="Interface Web FastMCP",
    description="Une interface web intuitive pour FastMCP, permettant aux utilisateurs novices d'utiliser FastMCP sans complexité technique.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configuration CORS pour permettre les requêtes depuis le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.security.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modele de données pour la requête du frontend
class ToolRequest(BaseModel):
    tool_name: str
    params: dict

# Modèle pour représenter un paramètre d'outil
class ToolParameter(BaseModel):
    name: str
    type: str
    description: str
    required: bool = True

# Modèle pour représenter un outil disponible
class Tool(BaseModel):
    name: str
    description: str
    parameters: List[ToolParameter]

# Endpoint d'authentification
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Endpoint pour obtenir un token d'accès."""
    user = authenticate_user(users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nom d'utilisateur ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
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

@app.post("/call_tool/")
async def call_tool_endpoint(request: ToolRequest, current_user: Optional[User] = auth_dependency):
    """Endpoint pour appeler un outil FastMCP."""
    logger.info(f"Appel de l'outil {request.tool_name} avec les paramètres {request.params}")
    try:
        result = await execute_tool(request.tool_name, request.params)
        logger.info(f"Résultat de l'outil {request.tool_name}: {result}")
        return {"result": result}
    except Exception as e:
        logger.error(f"Erreur lors de l'appel de l'outil {request.tool_name}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/list_tools/", response_model=dict)
async def list_tools_endpoint(current_user: Optional[User] = auth_dependency):
    """Endpoint pour lister tous les outils disponibles."""
    logger.info("Liste des outils demandée")
    try:
        tools = await get_available_tools()
        return {"tools": tools}
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des outils: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Servir les fichiers statiques
app.mount("/static", StaticFiles(directory="static"), name="static")

# Servir le fichier index.html à la racine
@app.get("/")
async def read_index():
    logger.info("Page d'accueil demandée")
    return FileResponse('index.html')

# Vérification de l'état de santé de l'API
@app.get("/health")
async def health_check():
    """Endpoint pour vérifier l'état de santé de l'API."""
    return {"status": "ok"}

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