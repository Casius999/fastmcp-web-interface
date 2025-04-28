import time
import os
import psutil
import socket
import threading
from prometheus_client import start_http_server, Counter, Gauge, Histogram, Summary
from logging_config import logger
from config import config

# Métriques Prometheus
REQUEST_COUNT = Counter('fastmcp_request_total', 'Total des requêtes', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('fastmcp_request_latency_seconds', 'Latence des requêtes', ['method', 'endpoint'])
TOOL_EXECUTION_COUNT = Counter('fastmcp_tool_execution_total', 'Total des exécutions d\'outils', ['tool_name', 'status'])
TOOL_EXECUTION_TIME = Histogram('fastmcp_tool_execution_time_seconds', 'Temps d\'exécution des outils', ['tool_name'])

# Métriques système
CPU_USAGE = Gauge('fastmcp_cpu_usage_percent', 'Utilisation CPU en pourcentage')
MEMORY_USAGE = Gauge('fastmcp_memory_usage_bytes', 'Utilisation de la mémoire en bytes')
AVAILABLE_MEMORY = Gauge('fastmcp_available_memory_bytes', 'Mémoire disponible en bytes')
OPEN_FILE_DESCRIPTORS = Gauge('fastmcp_open_file_descriptors', 'Nombre de descripteurs de fichiers ouverts')
ACTIVE_CONNECTIONS = Gauge('fastmcp_active_connections', 'Nombre de connexions actives')

# Métriques FastMCP
FASTMCP_CLIENT_POOL = Gauge('fastmcp_client_pool_size', 'Taille du pool de clients FastMCP')
FASTMCP_CLIENT_ERRORS = Counter('fastmcp_client_errors_total', 'Erreurs de client FastMCP', ['error_type'])

def start_monitoring(port=8001):
    """Démarre le serveur de métriques Prometheus et la collecte des métriques système."""
    # Démarrer le serveur HTTP pour exposer les métriques Prometheus
    start_http_server(port)
    logger.info(f"Serveur de métriques Prometheus démarré sur le port {port}")
    
    # Démarrer la collecte des métriques système en arrière-plan
    thread = threading.Thread(target=collect_system_metrics, daemon=True)
    thread.start()
    
    return thread

def collect_system_metrics():
    """Collecte périodiquement les métriques système."""
    while True:
        try:
            # Métriques CPU
            CPU_USAGE.set(psutil.cpu_percent(interval=1))
            
            # Métriques mémoire
            memory = psutil.virtual_memory()
            MEMORY_USAGE.set(memory.used)
            AVAILABLE_MEMORY.set(memory.available)
            
            # Descripteurs de fichiers ouverts
            if os.name == 'posix':  # Linux/Unix seulement
                OPEN_FILE_DESCRIPTORS.set(psutil.Process().num_fds())
            
            # Connexions réseau actives
            connections = len(psutil.net_connections())
            ACTIVE_CONNECTIONS.set(connections)
            
            time.sleep(15)  # Collecter toutes les 15 secondes
        except Exception as e:
            logger.error(f"Erreur lors de la collecte des métriques système: {str(e)}")
            time.sleep(30)  # Attendre un peu plus longtemps en cas d'erreur

class PrometheusMiddleware:
    """Middleware FastAPI pour collecter des métriques de requêtes."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        
        start_time = time.time()
        
        # Wrap send pour intercepter le code de statut
        original_send = send
        send_wrapper = self.create_send_wrapper(original_send, start_time, scope)
        
        await self.app(scope, receive, send_wrapper)
    
    def create_send_wrapper(self, original_send, start_time, scope):
        method = scope.get("method", "")
        path = scope.get("path", "")
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_code = message["status"]
                duration = time.time() - start_time
                REQUEST_COUNT.labels(method=method, endpoint=path, status=status_code).inc()
                REQUEST_LATENCY.labels(method=method, endpoint=path).observe(duration)
            
            await original_send(message)
        
        return send_wrapper

# Fonction décorateur pour mesurer l'exécution des outils
def track_tool_execution(func):
    """Décorateur pour suivre l'exécution des outils."""
    async def wrapper(tool_name, params):
        start_time = time.time()
        try:
            result = await func(tool_name, params)
            duration = time.time() - start_time
            TOOL_EXECUTION_COUNT.labels(tool_name=tool_name, status="success").inc()
            TOOL_EXECUTION_TIME.labels(tool_name=tool_name).observe(duration)
            return result
        except Exception as e:
            duration = time.time() - start_time
            TOOL_EXECUTION_COUNT.labels(tool_name=tool_name, status="error").inc()
            TOOL_EXECUTION_TIME.labels(tool_name=tool_name).observe(duration)
            # Propager l'exception après avoir collecté les métriques
            raise
    
    return wrapper

# Fonction utilitaire pour les healthchecks
def get_health_status():
    """Récupère l'état de santé détaillé du système."""
    try:
        # Vérifier si le serveur FastMCP est accessible
        fastmcp_available = False
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            s.connect((config.server.host, config.server.port))
            s.close()
            fastmcp_available = True
        except:
            pass
        
        # Récupérer les métriques système
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Calculer l'état général
        overall_status = "ok"
        if cpu_percent > 90 or memory.percent > 90 or disk.percent > 90 or not fastmcp_available:
            overall_status = "warning"
        if cpu_percent > 95 or memory.percent > 95 or disk.percent > 95:
            overall_status = "critical"
        
        return {
            "status": overall_status,
            "details": {
                "fastmcp_server": "available" if fastmcp_available else "unavailable",
                "cpu_usage_percent": cpu_percent,
                "memory_usage_percent": memory.percent,
                "disk_usage_percent": disk.percent,
                "uptime_seconds": time.time() - psutil.boot_time()
            }
        }
    except Exception as e:
        logger.error(f"Erreur lors de la vérification de l'état de santé: {str(e)}")
        return {
            "status": "error",
            "details": {
                "error": str(e)
            }
        }

# Initialisation des métriques client FastMCP
def set_fastmcp_client_pool_size(size):
    """Met à jour la taille du pool de clients FastMCP."""
    FASTMCP_CLIENT_POOL.set(size)

def increment_fastmcp_client_error(error_type):
    """Incrémente le compteur d'erreurs client FastMCP."""
    FASTMCP_CLIENT_ERRORS.labels(error_type=error_type).inc()