import time
import asyncio
import functools
from enum import Enum
from typing import Callable, Dict, Any, Optional, Type, List, Union
from logging_config import logger
from config import config

class CircuitState(Enum):
    CLOSED = "CLOSED"       # Circuit fermé, tout fonctionne normalement
    OPEN = "OPEN"          # Circuit ouvert, aucun appel n'est fait
    HALF_OPEN = "HALF_OPEN" # Circuit en test de récupération

class CircuitBreaker:
    """Implémentation du pattern Circuit Breaker pour prévenir les cascades de pannes."""
    
    def __init__(self, name: str, failure_threshold: int = 5, recovery_timeout: int = 30):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        self.last_success_time = time.time()
    
    def record_success(self):
        """Enregistre un appel réussi."""
        self.failure_count = 0
        self.last_success_time = time.time()
        if self.state == CircuitState.HALF_OPEN:
            logger.info(f"Circuit {self.name} rétabli après succès en mode half-open")
            self.state = CircuitState.CLOSED
    
    def record_failure(self):
        """Enregistre un échec d'appel."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.CLOSED and self.failure_count >= self.failure_threshold:
            logger.warning(f"Circuit {self.name} ouvert après {self.failure_count} échecs consécutifs")
            self.state = CircuitState.OPEN
        elif self.state == CircuitState.HALF_OPEN:
            logger.warning(f"Circuit {self.name} reste ouvert après échec en mode half-open")
            self.state = CircuitState.OPEN
    
    def allow_request(self) -> bool:
        """Détermine si une requête doit être autorisée selon l'état du circuit."""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN and time.time() - self.last_failure_time >= self.recovery_timeout:
            logger.info(f"Circuit {self.name} passe en mode half-open après {self.recovery_timeout}s")
            self.state = CircuitState.HALF_OPEN
            return True
        
        return self.state == CircuitState.HALF_OPEN
    
    def get_state(self) -> Dict[str, Any]:
        """Renvoie l'état actuel du circuit breaker."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "last_failure": self.last_failure_time,
            "last_success": self.last_success_time,
            "seconds_since_last_failure": time.time() - self.last_failure_time if self.last_failure_time > 0 else None,
            "seconds_since_last_success": time.time() - self.last_success_time
        }

# Registre global des circuit breakers
circuit_breakers: Dict[str, CircuitBreaker] = {}

def get_circuit_breaker(name: str) -> CircuitBreaker:
    """Récupère un circuit breaker existant ou en crée un nouveau."""
    if name not in circuit_breakers:
        circuit_breakers[name] = CircuitBreaker(
            name=name,
            failure_threshold=config.resilience.failure_threshold,
            recovery_timeout=config.resilience.recovery_timeout
        )
    return circuit_breakers[name]

class RetryConfig:
    """Configuration des stratégies de retry."""
    def __init__(self, max_retries: int = 3, delay: float = 1.0, backoff_factor: float = 2.0, 
                  exceptions_to_retry: Optional[List[Type[Exception]]] = None):
        self.max_retries = max_retries
        self.delay = delay
        self.backoff_factor = backoff_factor
        self.exceptions_to_retry = exceptions_to_retry or [Exception]

class CircuitBreakerError(Exception):
    """Exception levée lorsqu'un circuit breaker est ouvert."""
    pass

def circuit_breaker(name: str = None, failure_threshold: int = None, recovery_timeout: int = None):
    """Décorateur pour appliquer le pattern Circuit Breaker sur une fonction asynchrone."""
    def decorator(func):
        nonlocal name, failure_threshold, recovery_timeout
        
        # Utiliser le nom de la fonction si non spécifié
        if name is None:
            name = func.__name__
        
        # Utiliser les paramètres de config si non spécifiés
        if failure_threshold is None:
            failure_threshold = config.resilience.failure_threshold
        if recovery_timeout is None:
            recovery_timeout = config.resilience.recovery_timeout
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Vérifier si la résilience est activée
            if not config.resilience.circuit_breaker_enabled:
                return await func(*args, **kwargs)
                
            cb = get_circuit_breaker(name)
            
            if not cb.allow_request():
                logger.warning(f"Circuit {name} ouvert, requête bloquée")
                raise CircuitBreakerError(f"Circuit {name} ouvert, service indisponible temporairement")
            
            try:
                result = await func(*args, **kwargs)
                cb.record_success()
                return result
            except Exception as e:
                cb.record_failure()
                raise
                
        return wrapper
    return decorator

def retry(max_retries: int = None, delay: float = None, backoff_factor: float = 2.0, 
           exceptions_to_retry: Optional[List[Type[Exception]]] = None):
    """Décorateur pour réessayer une fonction asynchrone en cas d'échec."""
    def decorator(func):
        nonlocal max_retries, delay
        
        # Utiliser les paramètres de config si non spécifiés
        if max_retries is None:
            max_retries = config.resilience.max_retries
        if delay is None:
            delay = config.resilience.retry_delay
            
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Vérifier si les retries sont activés
            if not config.resilience.retry_enabled:
                return await func(*args, **kwargs)
                
            exceptions = exceptions_to_retry or [Exception]
            
            # Exclure CircuitBreakerError des exceptions à réessayer
            if CircuitBreakerError in exceptions:
                exceptions.remove(CircuitBreakerError)
            
            retry_count = 0
            current_delay = delay
            
            while True:
                try:
                    return await func(*args, **kwargs)
                except tuple(exceptions) as e:
                    retry_count += 1
                    if retry_count > max_retries:
                        logger.warning(f"Nombre maximum de tentatives atteint ({max_retries}) pour {func.__name__}")
                        raise
                    
                    logger.info(f"Tentative {retry_count}/{max_retries} échouée pour {func.__name__}, nouvelle tentative dans {current_delay}s")
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff_factor
                except Exception as e:
                    # Ne pas réessayer les autres exceptions
                    raise
        
        return wrapper
    return decorator

async def timeout_handler(coro, seconds):
    """Gère le timeout d'une coroutine."""
    try:
        return await asyncio.wait_for(coro, timeout=seconds)
    except asyncio.TimeoutError:
        raise TimeoutError(f"Opération a dépassé le délai de {seconds} secondes")

def with_timeout(seconds: int = None):
    """Décorateur pour ajouter un timeout à une fonction asynchrone."""
    def decorator(func):
        nonlocal seconds
        
        # Utiliser le paramètre de config si non spécifié
        if seconds is None:
            seconds = config.resilience.timeout
            
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await timeout_handler(func(*args, **kwargs), seconds)
        
        return wrapper
    return decorator

def resilient(circuit_name: str = None, max_retries: int = None, timeout: int = None):
    """Décorateur combiné pour une résilience complète (timeout + retry + circuit breaker)."""
    def decorator(func):
        # Appliquer les décorateurs dans le bon ordre: timeout -> retry -> circuit breaker
        # Le timeout est vérifié en premier, puis les retries, et enfin le circuit breaker
        
        # Utiliser le nom de la fonction si non spécifié
        cb_name = circuit_name or func.__name__
        
        # Décorateur composé
        @with_timeout(timeout)
        @retry(max_retries=max_retries)
        @circuit_breaker(name=cb_name)
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

# Fonction pour obtenir l'état de tous les circuit breakers
def get_all_circuit_breakers_state() -> Dict[str, Dict[str, Any]]:
    """Récupère l'état de tous les circuit breakers."""
    return {name: cb.get_state() for name, cb in circuit_breakers.items()}

# Réinitialiser un circuit breaker spécifique
def reset_circuit_breaker(name: str) -> bool:
    """Réinitialise un circuit breaker à son état initial."""
    if name in circuit_breakers:
        cb = circuit_breakers[name]
        cb.state = CircuitState.CLOSED
        cb.failure_count = 0
        cb.last_success_time = time.time()
        logger.info(f"Circuit breaker {name} réinitialisé")
        return True
    return False