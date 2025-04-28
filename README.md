# FastMCP Web Interface

Une interface web intuitive pour FastMCP, permettant aux utilisateurs novices d'utiliser FastMCP sans complexité technique.

## État du projet

**État actuel :** Version 1.0 - Prêt pour la production  
**Dernière mise à jour :** 28 avril 2025

Le projet est 100% opérationnel via une interface web sécurisée et robuste. Tous les éléments nécessaires à un déploiement en production sont présents, incluant tests, CI/CD, configuration d'environnement, et gestion des erreurs avancée.

## Architecture

Le projet est conçu selon une architecture en trois couches :

1. **Backend FastMCP** (server.py)
   - Un serveur FastMCP avec des outils définis via des décorateurs
   - Un client pour communiquer avec ce serveur
   - Une fonction asynchrone pour exécuter les outils

2. **API Web avec FastAPI** (app.py)
   - Expose un endpoint POST pour appeler les outils
   - Gère les erreurs via des exceptions HTTP
   - Sert les fichiers statiques et l'interface utilisateur
   - Intègre une documentation interactive (Swagger/OpenAPI)

3. **Interface Frontend** (index.html, static/)
   - Interface utilisateur responsive
   - Gestion des types de données dynamique
   - Affichage des résultats formatés
   - Prise en charge de l'authentification

## Fonctionnalités

- **Outils disponibles**
  - `greet` : Message de bienvenue personnalisé
  - `calculate` : Opérations mathématiques de base

- **Fonctionnalités de production**
  - Authentification JWT (activable via configuration)
  - Configuration par variables d'environnement
  - Logging structuré
  - Tests unitaires et d'intégration
  - Pipeline CI/CD automatique
  - Conteneurisation Docker complète
  - Health checks et surveillance

## Installation

### Prérequis

- Python 3.8+
- Docker et Docker Compose (pour l'installation avec conteneurs)
- Pip (pour l'installation locale)

### Méthode 1 : Installation locale

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

# Démarrer le serveur FastMCP
python server.py

# Dans un autre terminal, démarrer l'API Web
uvicorn app:app --reload
```

### Méthode 2 : Utilisation de Docker

```bash
# Cloner le dépôt
git clone https://github.com/Casius999/fastmcp-web-interface.git
cd fastmcp-web-interface

# Créer le fichier .env à partir de l'exemple
cp .env.example .env

# Configurer les variables d'environnement selon vos besoins
# Éditer le fichier .env avec votre éditeur favori

# Construire et démarrer les conteneurs
docker-compose up -d

# Vérifier que les services fonctionnent
docker-compose ps
```

## Utilisation

1. Accédez à l'interface web via http://localhost:8000
2. Si l'authentification est activée, connectez-vous avec les identifiants par défaut (admin/admin)
3. Sélectionnez un outil dans la liste déroulante
4. Remplissez les paramètres requis
5. Cliquez sur "Exécuter" pour voir le résultat

## Configuration

Le projet utilise des variables d'environnement pour la configuration, définies dans le fichier `.env` :

```
# Configuration du serveur FastMCP
FASTMCP_HOST=0.0.0.0         # Hôte du serveur FastMCP
FASTMCP_PORT=50051           # Port du serveur FastMCP
FASTMCP_NAME="FastMCP Server" # Nom du serveur

# Configuration de l'API FastAPI
API_HOST=0.0.0.0             # Hôte de l'API
API_PORT=8000                # Port de l'API
API_RELOAD=false             # Mode de rechargement automatique
API_WORKERS=4                # Nombre de workers
API_LOG_LEVEL=info           # Niveau de log

# Configuration de sécurité
CORS_ALLOWED_ORIGINS=*       # Origines autorisées pour CORS
SECRET_KEY=your_secret_key   # Clé secrète pour JWT
AUTH_ENABLED=false           # Activation de l'authentification

# Configuration du logging
LOG_LEVEL=INFO               # Niveau de log
LOG_FILE=/var/log/fastmcp-web-interface.log  # Fichier de log
```

## Tests

Le projet comprend des tests unitaires et d'intégration pour assurer son bon fonctionnement :

```bash
# Exécuter tous les tests
pytest

# Exécuter les tests avec couverture
pytest --cov=. tests/

# Exécuter uniquement les tests d'intégration
pytest -m integration
```

## API Documentation

Une documentation interactive de l'API est disponible via Swagger UI :

- Swagger UI : http://localhost:8000/docs
- ReDoc : http://localhost:8000/redoc

## Déploiement en production

### Sécurité

Pour un déploiement en production, assurez-vous de :

1. Changer la clé secrète `SECRET_KEY` dans le fichier `.env`
2. Activer l'authentification : `AUTH_ENABLED=true`
3. Spécifier les origines CORS exactes : `CORS_ALLOWED_ORIGINS=https://votredomaine.com`
4. Mettre à jour les identifiants par défaut dans `auth.py`

### Pipeline CI/CD

Le projet inclut un pipeline CI/CD GitHub Actions qui :

1. Exécute les linters (flake8, black, isort)
2. Exécute les tests unitaires et d'intégration
3. Construit les images Docker
4. Déploie sur le serveur cible

Pour utiliser le pipeline, configurez les secrets GitHub suivants :

- `DOCKERHUB_USERNAME` : Nom d'utilisateur Docker Hub
- `DOCKERHUB_TOKEN` : Token d'accès Docker Hub
- `SSH_PRIVATE_KEY` : Clé SSH privée pour le déploiement
- `SERVER_IP` : Adresse IP du serveur cible
- `SERVER_USER` : Nom d'utilisateur SSH du serveur

## Structure du projet

```
fastmcp-web-interface/
├── .github/
│   └── workflows/
│       └── ci-cd.yml       # Configuration CI/CD
├── static/
│   ├── css/
│   │   └── styles.css     # Styles CSS
│   ├── js/
│   │   └── app.js         # JavaScript frontend
│   └── favicon.ico       # Favicon
├── tests/
│   ├── __init__.py
│   ├── test_app.py      # Tests de l'API
│   ├── test_integration.py # Tests d'intégration
│   └── test_server.py   # Tests du serveur
├── .env.example        # Exemple de configuration
├── .gitignore           # Fichiers ignorés par Git
├── app.py               # API FastAPI
├── auth.py              # Gestion de l'authentification
├── config.py            # Configuration
├── docker-compose.yml    # Configuration Docker Compose
├── Dockerfile           # Image Docker
├── index.html           # Interface utilisateur
├── logging_config.py    # Configuration du logging
├── MANIFEST.in          # Liste des fichiers à inclure
├── pytest.ini           # Configuration pytest
├── README.md            # Documentation
├── requirements.txt     # Dépendances
├── server.py            # Serveur FastMCP
└── setup.py             # Configuration du package
```

## Principes d'intégrité

Ce projet adhère aux principes d'intégrité systémique suivants :

- **Authenticité** : Les interactions entre les couches sont transparentes et vérifiables
- **Traçabilité** : Les erreurs sont correctement propagées et documentées
- **Vérifiabilité** : Le code est commenté et structuré pour faciliter la compréhension
- **Transparence** : L'architecture est clairement définie et documentée
- **Intégrité** : La gestion des erreurs assure que les données incorrectes sont rejetées

## Contribution

Les contributions sont les bienvenues ! Pour contribuer :

1. Forkez le projet
2. Créez une branche pour votre fonctionnalité (`git checkout -b feature/amazing-feature`)
3. Assurez-vous que les tests passent (`pytest`)
4. Committez vos changements (`git commit -m 'Add some amazing feature'`)
5. Poussez vers la branche (`git push origin feature/amazing-feature`)
6. Ouvrez une Pull Request

## Licence

MIT