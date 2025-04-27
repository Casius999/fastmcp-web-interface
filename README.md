# FastMCP Web Interface

Une interface web intuitive pour FastMCP, permettant aux utilisateurs novices d'utiliser FastMCP sans complexité technique.

## Architecture

Le projet est composé de trois couches principales :

1. **Backend FastMCP** (server.py)
   - Un serveur FastMCP avec des outils définis via des décorateurs
   - Un client pour communiquer avec ce serveur
   - Une fonction asynchrone pour exécuter les outils

2. **API Web avec FastAPI** (app.py)
   - Expose un endpoint POST pour appeler les outils
   - Gère les erreurs via des exceptions HTTP
   - Sert les fichiers statiques et l'interface utilisateur

3. **Interface Frontend** (index.html)
   - Interface utilisateur simple permettant d'interagir avec les outils
   - Présente un formulaire adapté à l'outil sélectionné
   - Affiche les résultats ou les erreurs de manière conviviale

## Installation

### Méthode 1 : Installation locale

```bash
# Cloner le dépôt
git clone https://github.com/Casius999/fastmcp-web-interface.git
cd fastmcp-web-interface

# Installer les dépendances
pip install -r requirements.txt
```

### Méthode 2 : Utilisation de Docker

```bash
# Cloner le dépôt
git clone https://github.com/Casius999/fastmcp-web-interface.git
cd fastmcp-web-interface

# Construire et démarrer les conteneurs
docker-compose up -d
```

## Utilisation

### Démarrage avec installation locale

1. Démarrer le serveur FastMCP (dans un terminal) :
```bash
python server.py
```

2. Démarrer l'API Web (dans un autre terminal) :
```bash
uvicorn app:app --reload
```

3. Ouvrir votre navigateur à l'adresse http://localhost:8000

### Démarrage avec Docker

Après avoir exécuté `docker-compose up -d`, ouvrez simplement votre navigateur à l'adresse http://localhost:8000

## Fonctionnalités

- Interface utilisateur intuitive pour les utilisateurs novices
- Architecture en trois couches pour une séparation claire des responsabilités
- Gestion robuste des erreurs pour une expérience utilisateur optimale
- Possibilité d'ajouter facilement de nouveaux outils

## Ajout de nouveaux outils

Pour ajouter un nouvel outil au serveur FastMCP :

1. Ouvrir le fichier `server.py`
2. Ajouter un nouveau décorateur `@mcp.tool()` avec la fonction correspondante
3. Mettre à jour l'API et l'interface utilisateur si nécessaire

Exemple d'ajout d'un nouvel outil de calcul :

```python
@mcp.tool()
def calculate(operation: str, a: float, b: float) -> float:
    """Effectue une opération mathématique simple."""
    if operation == "add":
        return a + b
    elif operation == "subtract":
        return a - b
    elif operation == "multiply":
        return a * b
    elif operation == "divide":
        if b == 0:
            raise ValueError("Division par zéro impossible")
        return a / b
    else:
        raise ValueError(f"Opération non reconnue : {operation}")
```

## Extensions futures

- Chargement dynamique des outils disponibles sur le serveur FastMCP
- Génération automatique des formulaires en fonction des paramètres des outils
- Authentification et autorisation pour sécuriser l'accès
- Communication en temps réel via WebSockets
- Journalisation des appels d'outils pour le suivi et le débogage

## Principes d'intégrité

Ce projet adhère aux principes d'intégrité systémique suivants :

- **Authenticité** : Les interactions entre les couches sont transparentes et vérifiables
- **Traçabilité** : Les erreurs sont correctement propagées et documentées
- **Vérifiabilité** : Le code est commenté et structuré pour faciliter la compréhension
- **Transparence** : L'architecture est clairement définie et documentée
- **Intégrité** : La gestion des erreurs assure que les données incorrectes sont rejetées

## API Reference

### Endpoints

- `POST /call_tool/` : Exécute un outil FastMCP
  - Body: `{ "tool_name": string, "params": object }`
  - Response: `{ "result": any }`

- `GET /list_tools/` : Liste les outils disponibles
  - Response: `{ "tools": array }`

## Licence

MIT
