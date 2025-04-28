# FastMCP Web Interface

Une interface web intuitive pour FastMCP, permettant aux utilisateurs novices d'utiliser FastMCP sans complexité technique.

## État du projet

**État actuel :** Version 1.0 - Déployée en production
**Dernière mise à jour :** 28 avril 2025

Le projet est actuellement opérationnel via une interface web simplifiée. Certains défis d'encodage ont été identifiés et seront résolus dans les prochaines versions.

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

# Construire et démarrer les conteneurs
docker-compose up -d
```

## Défis connus et solutions

### Problèmes d'encodage

Certains fichiers Python contiennent des caractères accentués qui peuvent causer des problèmes d'encodage. Solution temporaire :

1. Ajouter `# -*- coding: utf-8 -*-` au début de chaque fichier Python
2. Remplacer les caractères accentués par leurs équivalents non accentués

### Communication entre conteneurs Docker

Si vous rencontrez des problèmes de communication entre les conteneurs FastMCP et FastAPI, vérifiez les points suivants :

1. Les services sont sur le même réseau Docker
2. Les noms d'hôtes sont correctement référencés dans les configurations
3. Les ports sont correctement exposés

## Développements futurs

### Version 1.1 (Court terme)

- **Correction des problèmes d'encodage** : Standardiser tous les fichiers avec l'encodage UTF-8
- **Amélioration de la robustesse** : Gestion plus avancée des erreurs
- **Documentation intégrée** : Ajouter une page de documentation accessible depuis l'interface

### Version 1.2 (Moyen terme)

- **Chargement dynamique des outils** : Permettre à l'API de découvrir automatiquement les outils disponibles
- **Interface utilisateur améliorée** : Ajouter des composants interactifs et un design responsive
- **Authentification légère** : Ajouter une couche d'authentification simple pour sécuriser l'accès

### Version 2.0 (Long terme)

- **Gestionnaire de workflows** : Permettre de chaîner plusieurs outils dans un workflow
- **Intégration de WebSockets** : Communication en temps réel pour les tâches longues
- **Stockage persistant** : Sauvegarder les résultats des outils pour référence ultérieure
- **Interface multi-langue** : Support pour plusieurs langues dans l'interface
- **Mode hors ligne** : Possibilité d'utiliser certaines fonctionnalités sans connexion permanente

### Vision technique

- **Microservices** : Diviser l'application en microservices spécialisés
- **API Gateway** : Ajouter une couche d'abstraction pour unifier l'accès aux différentes fonctionnalités
- **Tests automatisés** : Développer une suite de tests complète pour garantir la qualité
- **CI/CD** : Mettre en place un pipeline d'intégration et déploiement continus
- **Monitoring** : Ajouter des outils de surveillance et d'alerte

## Contribution

Les contributions sont les bienvenues ! Pour contribuer :

1. Forkez le projet
2. Créez une branche pour votre fonctionnalité (`git checkout -b feature/amazing-feature`)
3. Committez vos changements (`git commit -m 'Add some amazing feature'`)
4. Poussez vers la branche (`git push origin feature/amazing-feature`)
5. Ouvrez une Pull Request

## Principes d'intégrité

Ce projet adhère aux principes d'intégrité systémique suivants :

- **Authenticité** : Les interactions entre les couches sont transparentes et vérifiables
- **Traçabilité** : Les erreurs sont correctement propagées et documentées
- **Vérifiabilité** : Le code est commenté et structuré pour faciliter la compréhension
- **Transparence** : L'architecture est clairement définie et documentée
- **Intégrité** : La gestion des erreurs assure que les données incorrectes sont rejetées

## Licence

MIT