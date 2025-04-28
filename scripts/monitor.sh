#!/bin/bash
# Script de surveillance pour FastMCP Web Interface

# Configuration
APP_DIR="/opt/fastmcp-web-interface"
LOG_FILE="/var/log/fastmcp-monitor.log"
HEALTH_ENDPOINT="http://localhost:8000/health"
NOTIFY_EMAIL="" # Laisser vide pour désactiver les notifications par e-mail

# Couleurs pour la sortie console
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
NC="\033[0m" # No Color

# Fonction de journalisation
log() {
    local message="$(date +'%Y-%m-%d %H:%M:%S') - $1"
    echo -e "$message" >> "$LOG_FILE"
    echo -e "$message"
}

# Vérifier si curl est installé
if ! command -v curl &> /dev/null; then
    log "${RED}curl n'est pas installé. Installation...${NC}"
    apt-get update && apt-get install -y curl
fi

# Créer le fichier de log s'il n'existe pas
touch "$LOG_FILE"

# Vérifier si le service est actif
health_check() {
    log "${YELLOW}Vérification de l'état du service...${NC}"
    health_output=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_ENDPOINT")
    
    if [ "$health_output" -eq 200 ]; then
        log "${GREEN}Le service est opérationnel (HTTP 200)${NC}"
        return 0
    else
        log "${RED}Le service est indisponible (HTTP $health_output)${NC}"
        return 1
    fi
}

# Vérifier l'utilisation des ressources
check_resources() {
    log "${YELLOW}Vérification des ressources...${NC}"
    
    # Vérification CPU
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2 + $4}')
    if (( $(echo "$cpu_usage > 90" | bc -l) )); then
        log "${RED}Alerte: Utilisation CPU élevée: $cpu_usage%${NC}"
        return 1
    fi
    
    # Vérification mémoire
    mem_usage=$(free | grep Mem | awk '{print $3/$2 * 100.0}')
    if (( $(echo "$mem_usage > 90" | bc -l) )); then
        log "${RED}Alerte: Utilisation mémoire élevée: $mem_usage%${NC}"
        return 1
    fi
    
    # Vérification disque
    disk_usage=$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')
    if [ "$disk_usage" -gt 90 ]; then
        log "${RED}Alerte: Espace disque faible: $disk_usage%${NC}"
        return 1
    fi
    
    log "${GREEN}Ressources OK: CPU: $cpu_usage%, Mémoire: $mem_usage%, Disque: $disk_usage%${NC}"
    return 0
}

# Vérifier les conteneurs Docker
check_containers() {
    cd "$APP_DIR"
    
    log "${YELLOW}Vérification des conteneurs Docker...${NC}"
    
    # Compter les conteneurs en cours d'exécution
    running_containers=$(docker-compose ps --services --filter "status=running" | wc -l)
    expected_containers=$(docker-compose ps --services | wc -l)
    
    if [ "$running_containers" -ne "$expected_containers" ]; then
        log "${RED}Alerte: Certains conteneurs ne sont pas en cours d'exécution ($running_containers/$expected_containers)${NC}"
        return 1
    fi
    
    log "${GREEN}Tous les conteneurs sont en cours d'exécution ($running_containers/$expected_containers)${NC}"
    return 0
}

# Fonction de redémarrage
restart_service() {
    log "${RED}Redémarrage des services...${NC}"
    
    cd "$APP_DIR"
    docker-compose down
    docker-compose up -d
    
    sleep 10
    
    if health_check; then
        log "${GREEN}Redémarrage réussi!${NC}"
        return 0
    else
        log "${RED}Le redémarrage a échoué!${NC}"
        return 1
    fi
}

# Envoyer une notification par e-mail
send_notification() {
    local subject="$1"
    local message="$2"
    
    if [ -n "$NOTIFY_EMAIL" ]; then
        log "${YELLOW}Envoi d'une notification à $NOTIFY_EMAIL${NC}"
        echo "$message" | mail -s "$subject" "$NOTIFY_EMAIL"
    fi
}

# Programme principal
log "${GREEN}=== Démarrage de la surveillance de FastMCP Web Interface ===${NC}"

# Vérification de santé
if ! health_check; then
    # En cas d'échec, vérifier les conteneurs
    check_containers
    
    # Tentative de redémarrage
    if restart_service; then
        send_notification "[FastMCP] Service redémarré avec succès" "Le service FastMCP Web Interface a été redémarré automatiquement après une détection d'indisponibilité."
    else
        send_notification "[ALERTE FastMCP] Service indisponible" "Le service FastMCP Web Interface est indisponible et n'a pas pu être redémarré automatiquement. Une intervention manuelle est nécessaire."
    fi
fi

# Vérification des ressources
check_resources

log "${GREEN}=== Surveillance terminée ===${NC}"
