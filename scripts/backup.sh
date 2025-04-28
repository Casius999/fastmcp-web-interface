#!/bin/bash
# Script de sauvegarde pour FastMCP Web Interface

set -e

# Configuration
APP_DIR="/opt/fastmcp-web-interface"
BACKUP_DIR="/opt/backups/fastmcp-web-interface"
MAX_BACKUPS=10

# Couleurs pour la sortie console
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
NC="\033[0m" # No Color

echo -e "${GREEN}=== Démarrage de la sauvegarde de FastMCP Web Interface ===${NC}"

# Vérifier si le script est exécuté en tant que root
if [ "$(id -u)" != "0" ]; then
   echo -e "${RED}Ce script doit être exécuté en tant que root${NC}" 
   exit 1
fi

# Créer le répertoire de sauvegarde s'il n'existe pas
mkdir -p $BACKUP_DIR

# Générer le nom du fichier de sauvegarde avec la date
BACKUP_DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/fastmcp_backup_$BACKUP_DATE.tar.gz"

# Sauvegarde du fichier .env et des logs
cd $APP_DIR

echo -e "${YELLOW}Création de l'archive de sauvegarde...${NC}"
tar -czf $BACKUP_FILE .env logs/ 2>/dev/null || {
    echo -e "${YELLOW}Avertissement : Certains fichiers n'ont pas pu être inclus dans l'archive${NC}"
}

# Vérifier que la sauvegarde a été créée
if [ -f "$BACKUP_FILE" ]; then
    echo -e "${GREEN}Sauvegarde créée avec succès: $BACKUP_FILE${NC}"
    # Supprimer les anciennes sauvegardes si le nombre dépasse MAX_BACKUPS
    NUM_BACKUPS=$(ls -1 $BACKUP_DIR/fastmcp_backup_* 2>/dev/null | wc -l)
    if [ "$NUM_BACKUPS" -gt "$MAX_BACKUPS" ]; then
        echo -e "${YELLOW}Suppression des sauvegardes excédentaires...${NC}"
        ls -1t $BACKUP_DIR/fastmcp_backup_* | tail -n +$((MAX_BACKUPS+1)) | xargs rm -f
        echo -e "${GREEN}Anciennes sauvegardes supprimées. Il reste $MAX_BACKUPS sauvegardes.${NC}"
    fi
else
    echo -e "${RED}Erreur: La sauvegarde n'a pas été créée${NC}"
    exit 1
fi

echo -e "${GREEN}=== Sauvegarde terminée avec succès! ===${NC}"
