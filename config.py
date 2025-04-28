import os
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

class ServerConfig(BaseModel):
    """Configuration du serveur FastMCP."""
    host: str = os.getenv("FASTMCP_HOST", "0.0.0.0")
    port: int = int(os.getenv("FASTMCP_PORT", "50051"))
    name: str = os.getenv("FASTMCP_NAME", "FastMCP Server")

class APIConfig(BaseModel):
    """Configuration de l'API FastAPI."""
    host: str = os.getenv("API_HOST", "0.0.0.0")
    port: int = int(os.getenv("API_PORT", "8000"))
    reload: bool = os.getenv("API_RELOAD", "false").lower() == "true"
    workers: int = int(os.getenv("API_WORKERS", "1"))
    log_level: str = os.getenv("API_LOG_LEVEL", "info")

class SecurityConfig(BaseModel):
    """Configuration de sécurité."""
    cors_allowed_origins: List[str] = os.getenv("CORS_ALLOWED_ORIGINS", "*").split(",")
    secret_key: str = os.getenv("SECRET_KEY", "insecure_dev_key")
    auth_enabled: bool = os.getenv("AUTH_ENABLED", "false").lower() == "true"

class LoggingConfig(BaseModel):
    """Configuration du logging."""
    level: str = os.getenv("LOG_LEVEL", "INFO")
    file: Optional[str] = os.getenv("LOG_FILE")

class Config(BaseModel):
    """Configuration globale de l'application."""
    server: ServerConfig = ServerConfig()
    api: APIConfig = APIConfig()
    security: SecurityConfig = SecurityConfig()
    logging: LoggingConfig = LoggingConfig()

# Instance de configuration unique
config = Config()