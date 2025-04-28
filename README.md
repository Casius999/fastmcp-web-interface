# FastMCP Web Interface

Une interface web intuitive pour FastMCP, permettant aux utilisateurs novices d'utiliser FastMCP sans complexité technique. Solution complète, robuste et prête pour la production.

## État du projet

**État actuel :** Version 1.0 - Prêt pour la production  
**Dernière mise à jour :** 28 avril 2025

Le projet est 100% opérationnel via une interface web sécurisée et robuste. Tous les éléments nécessaires à un déploiement en production sont présents, incluant tests, CI/CD, monitoring, résilience, cache, et gestion des erreurs avancée.

## Architecture

Le projet est conçu selon une architecture en trois couches :

1. **Backend FastMCP** (server.py)
   - Un serveur FastMCP avec des outils définis via des décorateurs
   - Un pool de clients pour communiquer avec ce serveur
   - Fonction asynchrone résiliente pour exécuter les outils
   - Circuit breaker et retry pour la stabilité

2. **API Web avec FastAPI** (app.py)
   - Expose des endpoints REST pour appeler les outils
   - Gère les erreurs via des exceptions HTTP
   - Sert les fichiers statiques et l'interface utilisateur
   - Intègre une documentation interactive (Swagger/OpenAPI)
   - Monitoring Prometheus et health checks

3. **Interface Frontend** (index.html, static/)
   - Interface utilisateur responsive et intuitive
   - Gestion des types de données dynamique
   - Affichage des résultats formatés
   - Prise en charge de l'authentification
   - Formulaires adaptatifs en fonction des outils disponibles

## Fonctionnalités avancées

- **Sécurité**
  - Authentification JWT complète
  - Configuration CORS sécurisée
  - Protection contre les attaques courantes

- **Résilience**
  - Circuit breaker pour la protection contre les cascades de pannes
  - Retry avec backoff exponentiel
  - Timeouts configurable pour toutes les opérations
  - Healthchecks complets pour tous les services

- **Performance**
  - Cache Redis avec fallback en mémoire
  - Mise en cache configurable par outil
  - Pool de clients FastMCP pour l'optimisation des ressources
  - Compression gzip des réponses

- **Monitoring**
  - Intégration Prometheus complète
  - Métriques système et applicatives
  - Logging structuré et configurable
  - Tableau de bord administrateur

- **Maintenance**
  - Scripts de déploiement et maintenance
  - Sauvegardes et restaurations automatiques
  - Monitoring automatique avec alerting
  - Gestion de configuration avancée

## Outils disponibles

- **greet**: Message de bienvenue personnalisé
- **calculate**: Opérations mathématiques de base (addition, soustraction, multiplication, division)
- *Extensible pour plus d'outils personnalisés*

## Installation

### Prérequis

- Docker et Docker Compose (recommandé)
- Python 3.8+ (pour l'installation locale)
- Redis (optionnel, pour la mise en cache optimale)

### Méthode 1: Installation avec Docker (recommandée)

```bash
# Cloner le dépôt
git clone https://github.com/Casius999/fastmcp-web-interface.git
cd fastmcp-web-interface

# Initialiser la configuration
chmod +x scripts/init.sh
./scripts/init.sh

# Démarrer les conteneurs
docker-compose up -d
```

### Méthode 2: Installation manuelle

```bash
# Cloner le dépôt
git clone https://github.com/Casius999/fastmcp-web-interface.git
cd fastmcp-web-interface

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Sur Windows : venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt

# Créer le fichier .env à partir de l'exemple
cp .env.example .env
# Modifier le fichier .env selon vos besoins

# Démarrer le serveur FastMCP
python server.py

# Dans un autre terminal, démarrer l'API Web
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

## Utilisation

1. Accédez à l'interface web via http://localhost:8000
2. Si l'authentification est activée, connectez-vous avec les identifiants configurés (par défaut: admin/admin)
3. Sélectionnez un outil dans la liste déroulante
4. Remplissez les paramètres requis
5. Cliquez sur "Exécuter" pour voir le résultat

## Configuration

Toutes les options de configuration sont dans le fichier `.env` (créé à partir de `.env.example`).

Principales sections de configuration :

1. **Serveur FastMCP**
   ```
   FASTMCP_HOST=0.0.0.0
   FASTMCP_PORT=50051
   FASTMCP_NAME="FastMCP Production Server"
   FASTMCP_MAX_CONNECTIONS=100
   ```

2. **API Web**
   ```
   API_HOST=0.0.0.0
   API_PORT=8000
   API_WORKERS=4
   API_LOG_LEVEL=info
   ```

3. **Sécurité**
   ```
   CORS_ALLOWED_ORIGINS=https://example.com
   SECRET_KEY=votre_cle_secrete
   AUTH_ENABLED=true
   ```

4. **Cache**
   ```
   CACHE_ENABLED=true
   REDIS_URL=redis://redis:6379/0
   CACHE_DEFAULT_TTL=3600
   CACHE_TOOL_GREET_TTL=86400
   ```

5. **Monitoring**
   ```
   MONITORING_ENABLED=true
   PROMETHEUS_PORT=8001
   ```

6. **Résilience**
   ```
   RESILIENCE_RETRY_ENABLED=true
   RESILIENCE_MAX_RETRIES=3
   RESILIENCE_CIRCUIT_BREAKER_ENABLED=true
   ```

## Scripts de maintenance

Plusieurs scripts sont fournis pour faciliter la maintenance :

```bash
# Initialisation de la configuration
./scripts/init.sh

# Déploiement complet
./scripts/deploy.sh

# Sauvegarde de la configuration
./scripts/backup.sh

# Restauration d'une sauvegarde
./scripts/restore.sh

# Surveillance automatique
./scripts/monitor.sh
```

## Tests

Pour exécuter les tests :

```bash
# Tous les tests
pytest

# Tests avec couverture
pytest --cov=. tests/

# Tests d'intégration uniquement
pytest -m integration
```

## API Documentation

Une documentation interactive de l'API est disponible via Swagger UI :

- Swagger UI : http://localhost:8000/docs
- ReDoc : http://localhost:8000/redoc

## Monitoring

Les métriques Prometheus sont exposées sur http://localhost:8001 par défaut.

Métriques principales :
- `fastmcp_request_total` - Nombre total de requêtes
- `fastmcp_request_latency_seconds` - Latence des requêtes
- `fastmcp_tool_execution_total` - Exécutions d'outils
- `fastmcp_tool_execution_time_seconds` - Temps d'exécution des outils

Métriques système :
- `fastmcp_cpu_usage_percent` - Utilisation CPU
- `fastmcp_memory_usage_bytes` - Utilisation mémoire
- `fastmcp_client_pool_size` - Taille du pool de clients

## Dashboard d'administration

Le dashboard d'administration est accessible à http://localhost:8000/admin/ (nécessite une authentification).

Fonctionnalités :
- État des circuit breakers
- Statistiques de cache
- Health check détaillé
- Invalidation sélective du cache

## Déploiement en production

Consultez la documentation complète dans le répertoire `docs/` pour les détails de déploiement en production.

Points importants :
1. Assurez-vous de changer les mots de passe par défaut
2. Configurez des origines CORS spécifiques
3. Générez une clé secrète forte pour JWT
4. Configurez un serveur Redis dédié pour le cache
5. Mettez en place un proxy inverse comme Nginx
6. Configurez SSL/TLS pour chiffrer les communications

## Principes d'intégrité

Ce projet adhère aux principes d'intégrité systémique suivants :

- **Authenticité** : Vérification des sources et suivi des interactions
- **Traçabilité** : Journalisation complète et propagation des erreurs
- **Vérifiabilité** : Tests compréhensifs et documentation détaillée
- **Transparence** : Architecture clairement définie et documentation complète
- **Intégrité** : Validation des données et résistance aux pannes

## Contribution

Les contributions sont les bienvenues ! Pour contribuer :

1. Forkez le projet
2. Créez une branche (`git checkout -b feature/amazing-feature`)
3. Assurez-vous que les tests passent (`pytest`)
4. Committez vos changements (`git commit -m 'Add amazing feature'`)
5. Poussez vers la branche (`git push origin feature/amazing-feature`)
6. Ouvrez une Pull Request

## Licence

MIT