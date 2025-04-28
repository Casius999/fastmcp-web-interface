#!/bin/bash
# Script de restauration pour FastMCP Web Interface

set -e

# Configuration
APP_DIR="/opt/fastmcp-web-interface"
BACKUP_DIR="/opt/backups/fastmcp-web-interface"

# Couleurs pour la sortie console
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
NC="\033[0m" # No Color

echo -e "${GREEN}=== Restauration de FastMCP Web Interface ===${NC}"

# Vérifier si le script est exécuté en tant que root
if [ "$(id -u)" != "0" ]; then
   echo -e "${RED}Ce script doit être exécuté en tant que root${NC}" 
   exit 1
fi

# Vérifier que le répertoire de sauvegarde existe
if [ ! -d "$BACKUP_DIR" ]; then
    echo -e "${RED}Erreur: Le répertoire de sauvegarde $BACKUP_DIR n'existe pas${NC}"
    exit 1
fi

# Lister les sauvegardes disponibles
echo -e "${YELLOW}Sauvegardes disponibles:${NC}"
LISTED_BACKUPS=($(ls -1t $BACKUP_DIR/fastmcp_backup_* 2>/dev/null))

if [ ${#LISTED_BACKUPS[@]} -eq 0 ]; then
    echo -e "${RED}Aucune sauvegarde disponible${NC}"
    exit 1
fi

for i in "${!LISTED_BACKUPS[@]}"; do
    echo "$((i+1)). ${LISTED_BACKUPS[$i]##*/} ($(stat -c %y ${LISTED_BACKUPS[$i]} | cut -d' ' -f1,2))" 

done

# Demander quelle sauvegarde restaurer
echo -e "${YELLOW}Quelle sauvegarde souhaitez-vous restaurer? (1-${#LISTED_BACKUPS[@]}) ou 'q' pour quitter${NC}"
read -r choice

if [[ "$choice" == "q" ]]; then
    echo -e "${YELLOW}Restauration annulée${NC}"
    exit 0
fi

if ! [[ "$choice" =~ ^[0-9]+$ ]] || [ "$choice" -lt 1 ] || [ "$choice" -gt "${#LISTED_BACKUPS[@]}" ]; then
    echo -e "${RED}Choix invalide${NC}"
    exit 1
fi

SELECTED_BACKUP=${LISTED_BACKUPS[$((choice-1))]}

echo -e "${YELLOW}Vous allez restaurer: ${SELECTED_BACKUP##*/}${NC}"
echo -e "${RED}ATTENTION: Cette opération remplacera votre configuration actuelle!${NC}"
echo -e "${YELLOW}Êtes-vous sûr de vouloir continuer? (y/n)${NC}"
read -r confirm

if [[ "$confirm" != "y" ]]; then
    echo -e "${YELLOW}Restauration annulée${NC}"
    exit 0
fi

# Arrêter les services avant la restauration
echo -e "${YELLOW}Arrêt des services...${NC}"
cd $APP_DIR
docker-compose down

# Extraire les fichiers de configuration de la sauvegarde
echo -e "${YELLOW}Extraction des fichiers de sauvegarde...${NC}"
temp_dir=$(mktemp -d)
tar -xzf "$SELECTED_BACKUP" -C "$temp_dir"

# Restaurer les fichiers
if [ -f "$temp_dir/.env" ]; then
    echo -e "${YELLOW}Restauration du fichier .env...${NC}"
    cp "$temp_dir/.env" "$APP_DIR/.env"
fi

# Restaurer les logs
if [ -d "$temp_dir/logs" ]; then
    echo -e "${YELLOW}Restauration des logs...${NC}"
    mkdir -p "$APP_DIR/logs"
    cp -r "$temp_dir/logs"/* "$APP_DIR/logs/"
fi

# Nettoyer le répertoire temporaire
rm -rf "$temp_dir"

# Redémarrer les services
echo -e "${YELLOW}Redémarrage des services...${NC}"
docker-compose up -d

# Vérifier que les services sont bien démarrés
echo -e "${YELLOW}Vérification de l'état des services...${NC}"
sleep 5
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}Les services ont démarré avec succès!${NC}"
else
    echo -e "${RED}Erreur: Les services n'ont pas démarré correctement${NC}"
    docker-compose logs
    exit 1
fi

echo -e "${GREEN}=== Restauration terminée avec succès! ===${NC}"
