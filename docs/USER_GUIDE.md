# Guide utilisateur - FastMCP Web Interface

Ce guide vous explique comment utiliser l'interface web FastMCP pour exécuter des outils FastMCP sans avoir besoin de compétences techniques.

## Table des matières

1. [Accès à l'interface](#accès-à-linterface)
2. [Connexion](#connexion)
3. [Exécution d'un outil](#exécution-dun-outil)
4. [Comprendre les résultats](#comprendre-les-résultats)
5. [Erreurs courantes](#erreurs-courantes)
6. [Déconnexion](#déconnexion)

## Accès à l'interface

Pour accéder à l'interface web FastMCP, ouvrez votre navigateur et entrez l'URL fournie par votre administrateur. Par défaut, si l'application est installée localement, l'URL est :

```
http://localhost:8000
```

L'interface se présente comme suit :

![Interface principale](interface_principale.png)

## Connexion

Si l'authentification est activée, vous verrez d'abord un écran de connexion :

1. Entrez votre nom d'utilisateur dans le champ "Nom d'utilisateur"
2. Entrez votre mot de passe dans le champ "Mot de passe"
3. Cliquez sur le bouton "Se connecter"

Si les informations sont correctes, vous serez redirigé vers l'interface principale.

> **Note** : Si vous ne connaissez pas vos identifiants, contactez votre administrateur. Par défaut, le nom d'utilisateur est "admin" et le mot de passe est "admin".

## Exécution d'un outil

L'interface permet d'exécuter facilement les outils FastMCP disponibles :

1. Sélectionnez un outil dans le menu déroulant "Outil"
   - Une description de l'outil s'affiche sous le menu
   - Les champs de paramètres se mettent à jour automatiquement en fonction de l'outil sélectionné

2. Remplissez les paramètres requis (marqués d'un astérisque *)

3. Cliquez sur le bouton "Exécuter"

4. Attendez que le résultat s'affiche dans la section "Résultat"

### Exemple : Utilisation de l'outil "greet"

1. Sélectionnez "greet" dans le menu déroulant
2. Dans le champ "name", entrez votre nom
3. Cliquez sur "Exécuter"
4. Le résultat affichera un message de bienvenue personnalisé

### Exemple : Utilisation de l'outil "calculate"

1. Sélectionnez "calculate" dans le menu déroulant
2. Choisissez une opération dans le champ "operation" (add, subtract, multiply ou divide)
3. Entrez le premier nombre dans le champ "a"
4. Entrez le deuxième nombre dans le champ "b"
5. Cliquez sur "Exécuter"
6. Le résultat affichera le résultat de l'opération mathématique

## Comprendre les résultats

Après l'exécution d'un outil, les résultats s'affichent dans la section "Résultat" :

- Les résultats réussis sont affichés avec une bordure verte
- Les erreurs sont affichées avec une bordure rouge
- Les résultats complexes (objets JSON) sont formatés pour une meilleure lisibilité

## Erreurs courantes

Voici quelques erreurs courantes que vous pourriez rencontrer :

### Erreurs d'authentification

- **"Nom d'utilisateur ou mot de passe incorrect"** : Vérifiez vos identifiants de connexion
- **"Token invalide"** : Votre session a expiré, reconnectez-vous

### Erreurs d'exécution d'outil

- **"Paramètre manquant"** : Vous n'avez pas fourni un paramètre requis
- **"Type de paramètre invalide"** : Le format du paramètre est incorrect
- **"Opération non reconnue"** : Pour l'outil "calculate", vous avez spécifié une opération inconnue
- **"Division par zéro impossible"** : Pour l'outil "calculate", vous avez essayé de diviser par zéro

### Erreurs de connexion

- **"Erreur de connexion au serveur"** : Le serveur est inaccessible ou hors ligne

## Déconnexion

Pour vous déconnecter de l'interface (si l'authentification est activée) :

1. Cliquez sur le bouton "Déconnexion" situé en haut à droite de l'interface
2. Vous serez redirigé vers l'écran de connexion

## Assistance

Si vous rencontrez des problèmes lors de l'utilisation de l'interface, contactez votre administrateur système ou consultez la documentation complète du projet.