import logging
import sys
from logging.handlers import RotatingFileHandler
from config import config

# Configuration du format de log
log_format = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

def setup_logger(name):
    """Configure et retourne un logger avec le nom spécifié."""
    logger = logging.getLogger(name)
    
    # Définir le niveau de log
    level = getattr(logging, config.logging.level.upper(), logging.INFO)
    logger.setLevel(level)
    
    # Handler pour la console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)
    
    # Handler pour le fichier si spécifié
    if config.logging.file:
        file_handler = RotatingFileHandler(
            config.logging.file,
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(log_format)
        logger.addHandler(file_handler)
    
    return logger

# Logger principal de l'application
logger = setup_logger("fastmcp_web_interface")