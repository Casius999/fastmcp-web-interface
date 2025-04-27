from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from server import execute_tool
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Création de l'application FastAPI
app = FastAPI(title="Interface Web FastMCP")

# Configuration CORS pour permettre les requêtes depuis le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifiez les origines autorisées
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modèle de données pour la requête du frontend
class ToolRequest(BaseModel):
    tool_name: str
    params: dict

@app.post("/call_tool/")
async def call_tool_endpoint(request: ToolRequest):
    """
    Endpoint pour appeler un outil FastMCP.
    
    Args:
        request (ToolRequest): Requête contenant le nom de l'outil et ses paramètres
        
    Returns:
        dict: Résultat de l'exécution de l'outil
        
    Raises:
        HTTPException: En cas d'erreur lors de l'exécution de l'outil
    """
    try:
        result = await execute_tool(request.tool_name, request.params)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Endpoint pour lister les outils disponibles (extension future)
@app.get("/list_tools/")
async def list_tools_endpoint():
    """
    Endpoint pour lister tous les outils disponibles.
    Extension future: Implémentation dynamique pour récupérer les outils du serveur MCP.
    
    Returns:
        dict: Liste des outils disponibles avec leurs descriptions
    """
    # Pour l'instant, nous retournons une liste statique
    # À terme, cela pourrait être remplacé par une consultation dynamique des outils disponibles
    tools = [
        {
            "name": "greet",
            "description": "Renvoie un message de bienvenue personnalisé",
            "parameters": [{"name": "name", "type": "string", "description": "Nom de la personne à saluer"}]
        }
    ]
    return {"tools": tools}

# Servir les fichiers statiques
app.mount("/static", StaticFiles(directory="static"), name="static")

# Servir le fichier index.html à la racine
@app.get("/")
async def read_index():
    return FileResponse('index.html')

if __name__ == "__main__":
    # Démarrer l'API web
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)