#!/bin/bash
# Script d'initialisation pour FastMCP Web Interface

set -e

# Configuration
APP_NAME="FastMCP Web Interface"
DEFAULT_PORT=8000
DEFAULT_ADMIN_USER="admin"
DEFAULT_ADMIN_PASSWORD="admin"

# Couleurs pour la sortie console
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
BLUE="\033[0;34m"
NC="\033[0m" # No Color

echo -e "${BLUE}=============================================${NC}"
echo -e "${BLUE}    Configuration de $APP_NAME    ${NC}"
echo -e "${BLUE}=============================================${NC}"

# Vérifier si c'est une première installation
if [ -f ".env" ]; then
    echo -e "${YELLOW}Un fichier .env existe déjà. Voulez-vous le reconfigurer? (y/n)${NC}"
    read -r reconfigure
    if [[ "$reconfigure" != "y" ]]; then
        echo -e "${GREEN}Configuration annulée. Utilisation du fichier .env existant.${NC}"
        exit 0
    fi
fi

# Copier le fichier .env.example s'il n'existe pas
if [ ! -f ".env.example" ]; then
    echo -e "${RED}Erreur: Le fichier .env.example n'existe pas${NC}"
    exit 1
fi

cp .env.example .env

# Configuration interactive
echo -e "\n${YELLOW}=== Configuration générale ===${NC}"

# Port de l'API
echo -ne "${GREEN}Port de l'API [${DEFAULT_PORT}]: ${NC}"
read -r api_port
api_port=${api_port:-$DEFAULT_PORT}
sed -i "s/^API_PORT=.*/API_PORT=$api_port/" .env

# Activer l'authentification
echo -ne "${GREEN}Activer l'authentification? (y/n) [y]: ${NC}"
read -r auth_enabled
auth_enabled=${auth_enabled:-"y"}
if [[ "$auth_enabled" == "y" ]]; then
    sed -i "s/^AUTH_ENABLED=.*/AUTH_ENABLED=true/" .env
    
    # Nom d'utilisateur admin
    echo -ne "${GREEN}Nom d'utilisateur administrateur [${DEFAULT_ADMIN_USER}]: ${NC}"
    read -r admin_user
    admin_user=${admin_user:-$DEFAULT_ADMIN_USER}
    
    # Mot de passe admin
    echo -ne "${GREEN}Mot de passe administrateur [${DEFAULT_ADMIN_PASSWORD}]: ${NC}"
    read -r admin_password
    admin_password=${admin_password:-$DEFAULT_ADMIN_PASSWORD}
    
    # Génération d'une clé secrète aléatoire pour JWT
    secret_key=$(openssl rand -hex 32)
    sed -i "s/^SECRET_KEY=.*/SECRET_KEY=$secret_key/" .env
    
    echo -e "${YELLOW}Informations d'authentification configurées. Vous devrez mettre à jour le fichier auth.py avec le nouveau mot de passe haché.${NC}"
else
    sed -i "s/^AUTH_ENABLED=.*/AUTH_ENABLED=false/" .env
fi

# Configuration CORS
echo -ne "${GREEN}Domaines autorisés pour CORS (séparés par des virgules) [*]: ${NC}"
read -r cors_origins
cors_origins=${cors_origins:-"*"}
sed -i "s/^CORS_ALLOWED_ORIGINS=.*/CORS_ALLOWED_ORIGINS=$cors_origins/" .env

# Configuration du cache
echo -ne "${GREEN}Activer le cache? (y/n) [y]: ${NC}"
read -r cache_enabled
cache_enabled=${cache_enabled:-"y"}
if [[ "$cache_enabled" == "y" ]]; then
    sed -i "s/^CACHE_ENABLED=.*/CACHE_ENABLED=true/" .env
    
    echo -ne "${GREEN}URL Redis (laisser vide pour utiliser le cache en mémoire): ${NC}"
    read -r redis_url
    if [[ -n "$redis_url" ]]; then
        sed -i "s|^REDIS_URL=.*|REDIS_URL=$redis_url|" .env
    else
        sed -i "s/^REDIS_URL=.*/REDIS_URL=/" .env
    fi
else
    sed -i "s/^CACHE_ENABLED=.*/CACHE_ENABLED=false/" .env
fi

# Configuration du monitoring
echo -ne "${GREEN}Activer le monitoring Prometheus? (y/n) [y]: ${NC}"
read -r monitoring_enabled
monitoring_enabled=${monitoring_enabled:-"y"}
if [[ "$monitoring_enabled" == "y" ]]; then
    sed -i "s/^MONITORING_ENABLED=.*/MONITORING_ENABLED=true/" .env
    
    echo -ne "${GREEN}Port Prometheus [8001]: ${NC}"
    read -r prometheus_port
    prometheus_port=${prometheus_port:-8001}
    sed -i "s/^PROMETHEUS_PORT=.*/PROMETHEUS_PORT=$prometheus_port/" .env
else
    sed -i "s/^MONITORING_ENABLED=.*/MONITORING_ENABLED=false/" .env
fi

# Configuration des logs
echo -ne "${GREEN}Chemin du fichier de log [/var/log/fastmcp-web-interface.log]: ${NC}"
read -r log_file
log_file=${log_file:-"/var/log/fastmcp-web-interface.log"}
sed -i "s|^LOG_FILE=.*|LOG_FILE=$log_file|" .env

echo -ne "${GREEN}Niveau de log [INFO]: ${NC}"
read -r log_level
log_level=${log_level:-"INFO"}
sed -i "s/^LOG_LEVEL=.*/LOG_LEVEL=$log_level/" .env

echo -e "\n${GREEN}Configuration terminée avec succès!${NC}"
echo -e "${YELLOW}Vous pouvez maintenant démarrer l'application avec 'docker-compose up -d'${NC}"
