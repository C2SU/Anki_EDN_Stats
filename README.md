# EDN Progress - Statistiques pour Anki EDN

![Version](https://img.shields.io/badge/version-1.0.0-blue) ![Anki](https://img.shields.io/badge/Anki-23.10%2B-green) ![License](https://img.shields.io/badge/license-CC%20BY--SA%204.0-orange)

## 📊 Vue d'ensemble

**EDN Progress** est un addon conçu pour les utilisateurs du [**deck Anki EDN**](https://tools.c2su.org/Anki_EDN/book/) (gratuit et communautaire). Il offre une visualisation complète de votre progression et permet d'identfier vos difficultés.

## ✨ Fonctionnalités

### Graphiques Interactifs
- 📈 **Visualisation par items** 
- 🧬 **Visualisation par matières** 
- 🔍 **Visualisation SDD** 

### Métriques Avancées
- 🎯 **Difficulté**
- 📊 **Statistiques de maîtrise** : Cartes matures vs. total
- 📉 **Ratio Appris/Désuspendu** : Suivi de progression réelle
- 🏷️ **Filtrage par rang** : Rang A uniquement, Rang B/C, ou tous
- 📁 **Export CSV** : Exportez vos statistiques pour analyse externe

### Intégration EDN
- ⌨️ **Raccourci clavier** : `Ctrl+U` pour accès rapide
- 🔧 **Configuration centralisée** : Gestion centralisée via le menu "⚙️ Paramètres EDN"

## 🚀 Installation

### Depuis AnkiWeb (Recommandé)
1. Ouvrir Anki
2. Tools → Add-ons → Get Add-ons...
3. Entrer le code : `[CODE_ANKIWEB]`

### Installation Manuelle
1. Télécharger la dernière release
2. Dézipper dans `[Anki Profile]/addons21/`
3. Redémarrer Anki

## 📖 Utilisation

### Accès
- **Menu** : `Anki EDN → 📊 EDN Progress`
- **Raccourci** : `Ctrl+U`

### Interface Principale

#### Vue Graphique
- Cliquer sur un point pour voir les détails d'un item
- Utiliser les boutons de tri pour organiser les données

#### Paramètres (⚙️)
1. **Sélection de sujets** : Choisir les matières à afficher
2. **Presets** : Sauvegarder/charger des configurations
3. **Filtres avancés** : Rang, seuils personnalisés

#### Filtrage
- **Mode** : Items / Sujets / SDD
- **Rang** : Tous / Rang A uniquement / Sans rang A
- **Inclure enfants** : Afficher ou masquer les sous-items

### Presets Standards

L'addon inclut un bouton "**Sélection Standard **" pour activer rapidement les matières principales EDN recommandées.

## 🛠️ Compatibilité

### Requis
- **Anki** : Version 23.10 ou supérieure
- **Système** : Qt6 (Windows, macOS, Linux)
- [**deck Anki EDN**](https://tools.c2su.org/Anki_EDN/book/) 


## ❓ FAQ

### Pourquoi mes presets ne s'affichent pas ?
Les presets sont sauvegardés dans `user_state.json`. Si le problème persiste, vérifier la console Anki pour les messages `[EDN LOAD_STATE]`.

### Puis-je utiliser cet addon sans le deck EDN ?
L'addon est optimisé pour le deck EDN (tags `EDN::item-XXX`, etc.). Il fonctionnera avec d'autres decks mais les fonctionnalités seront limitées.

### Comment exporter mes statistiques ?
Utiliser le bouton "📁 Export CSV" en bas de l'interface. Le fichier CSV peut être ouvert dans Excel/Google Sheets.

### Mon graphique est vide ?
Vérifier que :
- Vous avez des cartes Anki EDN dans votre collection
- Les filtres ne sont pas trop restrictifs
- Le seuil de suspension n'est pas trop élevé

## 🐛 Signaler un problème

Si vous rencontrez un bug :
1. Vérifier la console Anki
2. Noter le message d'erreur complet
3. Créer un issue sur GitHub ou laisser un commentaire sur AnkiWeb

## 📜 Licence

Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0).

Ce projet est partagé librement pour la communauté Anki EDN.

## 🙏 Remerciements

- **Communauté Anki EDN** 
- **Chart.js** : Pour la bibliothèque de graphiques

## 🔗 Liens

- **Deck Anki EDN** : [ankiweb.net/shared/info/...](https://ankiweb.net/shared/info/)
- **Documentation complète** : [GitHub Wiki](https://github.com/C2SU/Anki_EDN_Stats)
- **Support** : [AnkiWeb Comments](https://ankiweb.net/shared/info/...)

---
