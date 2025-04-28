# Guide de déploiement en production

Ce document détaille le processus de déploiement de FastMCP Web Interface dans un environnement de production.

## Prérequis

- Serveur Linux (recommandé : Ubuntu 20.04+)
- Docker et Docker Compose installés
- Accès SSH au serveur
- Noms de domaine configurés (facultatif, mais recommandé)
- Certificats SSL (pour HTTPS)

## Processus de déploiement manuel

### 1. Préparation du serveur

```bash
# Mise à jour du système
sudo apt update && sudo apt upgrade -y

# Installation de Docker (si non installé)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Installation de Docker Compose (si non installé)
sudo curl -L "https://github.com/docker/compose/releases/download/v2.18.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Création du répertoire pour l'application
mkdir -p ~/fastmcp-web-interface
cd ~/fastmcp-web-interface
```

### 2. Configuration de l'application

```bash
# Cloner le dépôt (ou transférer les fichiers)
git clone https://github.com/Casius999/fastmcp-web-interface.git .

# Créer le fichier de configuration
cp .env.example .env

# Éditer le fichier .env avec vos paramètres
nano .env
```

Modifiez les paramètres suivants dans le fichier `.env` :

```
# Sécurité
SECRET_KEY=votre_cle_secrete_complexe_generee_aleatoirement
AUTH_ENABLED=true
CORS_ALLOWED_ORIGINS=https://votre-domaine.com

# Configuration du logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/fastmcp-web-interface.log
```

### 3. Déploiement avec Docker Compose

```bash
# Démarrer les services
docker-compose up -d

# Vérifier que les services fonctionnent
docker-compose ps

# Consulter les logs
docker-compose logs -f
```

### 4. Configuration du proxy inverse (Nginx)

Installation de Nginx :

```bash
sudo apt install -y nginx
```

Création d'une configuration pour votre site :

```bash
sudo nano /etc/nginx/sites-available/fastmcp-web-interface
```

Contenu du fichier :

```nginx
server {
    listen 80;
    server_name votre-domaine.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Configuration pour les WebSockets (si nécessaire dans les futures versions)
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

Activation de la configuration :

```bash
sudo ln -s /etc/nginx/sites-available/fastmcp-web-interface /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 5. Configuration SSL avec Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d votre-domaine.com
```

## Déploiement automatique avec CI/CD

Pour utiliser le pipeline CI/CD GitHub Actions inclus dans le projet :

1. Forkez le dépôt sur GitHub
2. Configurez les secrets GitHub suivants :
   - `DOCKERHUB_USERNAME` : Votre nom d'utilisateur Docker Hub
   - `DOCKERHUB_TOKEN` : Votre token d'accès Docker Hub
   - `SSH_PRIVATE_KEY` : Votre clé SSH privée pour le déploiement
   - `SERVER_IP` : L'adresse IP de votre serveur
   - `SERVER_USER` : Votre nom d'utilisateur SSH

3. Préparez votre serveur :

```bash
# Créer le répertoire pour l'application
mkdir -p ~/fastmcp-web-interface

# Copier l'exemple de configuration pour le premier déploiement
cp .env.example .env
```

4. Poussez vos modifications vers la branche `main` et le pipeline se déclenchera automatiquement.

## Maintenance

### Mise à jour de l'application

```bash
# Avec déploiement manuel
cd ~/fastmcp-web-interface
git pull
docker-compose down
docker-compose up -d

# Avec CI/CD
# Il suffit de pousser les nouvelles modifications vers GitHub
```

### Sauvegarde de la configuration

```bash
# Sauvegarde du fichier .env
cp ~/fastmcp-web-interface/.env ~/backups/fastmcp-web-interface-$(date +%Y%m%d).env
```

### Surveillance et logs

```bash
# Consulter les logs en temps réel
docker-compose logs -f

# Consulter les logs d'un service spécifique
docker-compose logs -f fastmcp-web

# Vérifier l'état des services
docker-compose ps
```

## Problèmes courants et solutions

### Les services ne démarrent pas

Vérifiez les logs :

```bash
docker-compose logs
```

Assurez-vous que le fichier `.env` est correctement configuré :

```bash
cat .env
```

### Problèmes de permissions

Si vous rencontrez des problèmes de permissions avec le volume de logs :

```bash
# Créer le répertoire logs avec les bonnes permissions
mkdir -p logs
chmod 777 logs
```

### L'API n'est pas accessible via Nginx

Vérifiez la configuration Nginx :

```bash
sudo nginx -t
```

Vérifiez que les ports sont correctement ouverts :

```bash
sudo ufw status
```

Si nécessaire, ouvrez les ports :

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```