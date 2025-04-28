import os
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

class ServerConfig(BaseModel):
    """Configuration du serveur FastMCP."""
    host: str = os.getenv("FASTMCP_HOST", "0.0.0.0")
    port: int = int(os.getenv("FASTMCP_PORT", "50051"))
    name: str = os.getenv("FASTMCP_NAME", "FastMCP Server")
    max_connections: int = int(os.getenv("FASTMCP_MAX_CONNECTIONS", "100"))
    connection_timeout: int = int(os.getenv("FASTMCP_CONNECTION_TIMEOUT", "30"))

class APIConfig(BaseModel):
    """Configuration de l'API FastAPI."""
    host: str = os.getenv("API_HOST", "0.0.0.0")
    port: int = int(os.getenv("API_PORT", "8000"))
    reload: bool = os.getenv("API_RELOAD", "false").lower() == "true"
    workers: int = int(os.getenv("API_WORKERS", "1"))
    log_level: str = os.getenv("API_LOG_LEVEL", "info")
    request_timeout: int = int(os.getenv("API_REQUEST_TIMEOUT", "60"))
    root_path: str = os.getenv("API_ROOT_PATH", "")

class SecurityConfig(BaseModel):
    """Configuration de sécurité."""
    cors_allowed_origins: List[str] = Field(default_factory=lambda: os.getenv("CORS_ALLOWED_ORIGINS", "*").split(","))
    secret_key: str = os.getenv("SECRET_KEY", "insecure_dev_key")
    auth_enabled: bool = os.getenv("AUTH_ENABLED", "false").lower() == "true"
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    password_min_length: int = int(os.getenv("PASSWORD_MIN_LENGTH", "8"))
    rate_limiting_enabled: bool = os.getenv("RATE_LIMITING_ENABLED", "false").lower() == "true"
    rate_limit_requests: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    rate_limit_window: int = int(os.getenv("RATE_LIMIT_WINDOW", "3600"))

class LoggingConfig(BaseModel):
    """Configuration du logging."""
    level: str = os.getenv("LOG_LEVEL", "INFO")
    file: Optional[str] = os.getenv("LOG_FILE")
    max_file_size: int = int(os.getenv("LOG_MAX_FILE_SIZE", "10485760"))  # 10MB
    backup_count: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))
    format: str = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    json_logs: bool = os.getenv("LOG_JSON", "false").lower() == "true"

class CacheConfig(BaseModel):
    """Configuration du cache."""
    enabled: bool = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    redis_url: Optional[str] = os.getenv("REDIS_URL")
    default_ttl: int = int(os.getenv("CACHE_DEFAULT_TTL", "3600"))  # 1 heure
    tools_config: Dict[str, int] = Field(default_factory=dict)
    max_memory_size: int = int(os.getenv("CACHE_MAX_MEMORY_SIZE", "104857600"))  # 100MB

class MonitoringConfig(BaseModel):
    """Configuration du monitoring."""
    enabled: bool = os.getenv("MONITORING_ENABLED", "true").lower() == "true"
    prometheus_port: int = int(os.getenv("PROMETHEUS_PORT", "8001"))
    collect_interval: int = int(os.getenv("MONITORING_COLLECT_INTERVAL", "15"))
    detailed_metrics: bool = os.getenv("MONITORING_DETAILED_METRICS", "true").lower() == "true"
    export_traces: bool = os.getenv("MONITORING_EXPORT_TRACES", "false").lower() == "true"
    trace_endpoint: Optional[str] = os.getenv("MONITORING_TRACE_ENDPOINT")

class ResilienceConfig(BaseModel):
    """Configuration de résilience."""
    retry_enabled: bool = os.getenv("RESILIENCE_RETRY_ENABLED", "true").lower() == "true"
    max_retries: int = int(os.getenv("RESILIENCE_MAX_RETRIES", "3"))
    retry_delay: float = float(os.getenv("RESILIENCE_RETRY_DELAY", "1.0"))
    circuit_breaker_enabled: bool = os.getenv("RESILIENCE_CIRCUIT_BREAKER_ENABLED", "true").lower() == "true"
    failure_threshold: int = int(os.getenv("RESILIENCE_FAILURE_THRESHOLD", "5"))
    recovery_timeout: int = int(os.getenv("RESILIENCE_RECOVERY_TIMEOUT", "30"))
    timeout: int = int(os.getenv("RESILIENCE_TIMEOUT", "10"))

class Config(BaseModel):
    """Configuration globale de l'application."""
    server: ServerConfig = ServerConfig()
    api: APIConfig = APIConfig()
    security: SecurityConfig = SecurityConfig()
    logging: LoggingConfig = LoggingConfig()
    cache: CacheConfig = CacheConfig()
    monitoring: MonitoringConfig = MonitoringConfig()
    resilience: ResilienceConfig = ResilienceConfig()
    
    # Analyser la configuration des outils cachables
    def __init__(self, **data: Any):
        super().__init__(**data)
        
        # Charger la configuration de cache des outils
        tool_cache_config = {}
        for key, value in os.environ.items():
            if key.startswith("CACHE_TOOL_") and key.endswith("_TTL"):
                tool_name = key[11:-4].lower()  # Extraire le nom de l'outil
                try:
                    ttl = int(value)
                    tool_cache_config[tool_name] = ttl
                except ValueError:
                    pass
        
        self.cache.tools_config = tool_cache_config

# Instance de configuration unique
config = Config()