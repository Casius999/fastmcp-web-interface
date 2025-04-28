#!/bin/bash
# Script de déploiement pour FastMCP Web Interface

set -e

# Configuration
APP_DIR="/opt/fastmcp-web-interface"
BACKUP_DIR="/opt/backups/fastmcp-web-interface"
GIT_REPO="https://github.com/Casius999/fastmcp-web-interface.git"
BRANCH="main"

# Couleurs pour la sortie console
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
NC="\033[0m" # No Color

echo -e "${GREEN}=== Démarrage du déploiement de FastMCP Web Interface ===${NC}"

# Vérifier si le script est exécuté en tant que root
if [ "$(id -u)" != "0" ]; then
   echo -e "${RED}Ce script doit être exécuté en tant que root${NC}" 
   exit 1
fi

# Créer les répertoires nécessaires
mkdir -p $APP_DIR
mkdir -p $BACKUP_DIR

# Sauvegarder la configuration existante
echo -e "${YELLOW}Sauvegarde de la configuration existante...${NC}"
if [ -f "$APP_DIR/.env" ]; then
    BACKUP_DATE=$(date +"%Y%m%d_%H%M%S")
    cp $APP_DIR/.env $BACKUP_DIR/.env.$BACKUP_DATE
    echo -e "${GREEN}Configuration sauvegardée dans $BACKUP_DIR/.env.$BACKUP_DATE${NC}"
fi

# Cloner le dépôt si c'est une nouvelle installation, sinon mettre à jour
if [ ! -d "$APP_DIR/.git" ]; then
    echo -e "${YELLOW}Première installation, clonage du dépôt...${NC}"
    rm -rf $APP_DIR/*
    git clone -b $BRANCH $GIT_REPO $APP_DIR
else
    echo -e "${YELLOW}Mise à jour du dépôt existant...${NC}"
    cd $APP_DIR
    git fetch --all
    git reset --hard origin/$BRANCH
fi

cd $APP_DIR

# Créer le fichier .env s'il n'existe pas
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Création du fichier de configuration .env...${NC}"
    cp .env.example .env
    echo -e "${GREEN}Fichier .env créé à partir de .env.example${NC}"
    echo -e "${YELLOW}N'oubliez pas de mettre à jour le fichier .env avec vos paramètres${NC}"
fi

# Ajouter les droits d'exécution aux scripts
chmod +x scripts/*.sh

# Vérifier si Docker et Docker Compose sont installés
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker n'est pas installé. Installation...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose n'est pas installé. Installation...${NC}"
    curl -L "https://github.com/docker/compose/releases/download/v2.18.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Création du répertoire de logs s'il n'existe pas
mkdir -p logs
chmod 777 logs

# Construire et démarrer les conteneurs
echo -e "${YELLOW}Construction et démarrage des conteneurs Docker...${NC}"
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Vérifier que les services sont bien démarrés
echo -e "${YELLOW}Vérification de l'état des services...${NC}"
sleep 5
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}Les services ont démarré avec succès!${NC}"
    echo -e "${GREEN}FastMCP Web Interface est accessible à l'adresse: http://localhost:8000${NC}"
else
    echo -e "${RED}Erreur: Les services n'ont pas démarré correctement${NC}"
    docker-compose logs
    exit 1
fi

# Ajouter une entrée crontab pour la surveillance
echo -e "${YELLOW}Configuration de la surveillance automatique...${NC}"
(crontab -l 2>/dev/null || echo "") | grep -v "$APP_DIR/scripts/monitor.sh" | { cat; echo "*/5 * * * * $APP_DIR/scripts/monitor.sh > /dev/null 2>&1"; } | crontab -

echo -e "${GREEN}=== Déploiement terminé avec succès! ===${NC}"
