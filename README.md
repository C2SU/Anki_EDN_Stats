# EDN Progress - Statistiques pour Anki EDN

![Version](https://img.shields.io/badge/version-1.0.0-blue) ![Anki](https://img.shields.io/badge/Anki-23.10%2B-green) ![License](https://img.shields.io/badge/license-CC%20BY--SA%204.0-orange)

## 📊 Vue d'ensemble

**EDN Progress** est un addon conçu pour les utilisateurs du **deck Anki EDN** (Externat médecine - gratuit et libre de droit). Il offre une visualisation complète de votre progression et de la difficulté FSRS de vos items EDN.

## ✨ Fonctionnalités

### Graphiques Interactifs
- 📈 **Visualisation par items** : Progression détaillée item par item (300+)
- 🧬 **Visualisation par matières** : Filtrage par spécialités médicales
- 🔍 **Visualisation SDD/SSDD** : situations de départ

### Métriques Avancées
- 🎯 **Difficulté FSRS intégrée** : Utilise le système de difficulté FSRS natif d'Anki 23.10+
- 📊 **Statistiques de maîtrise** : Cartes matures vs. total
- 📉 **Ratio Appris/Désuspendu** : Suivi de progression réelle
- 🏷️ **Filtrage par rang** : Rang A uniquement, Rang B/C, ou tous

### Gestion des Préférences
- 💾 **Presets personnalisables** : Sauvegardez vos sélections de sujets favoris
- 🎨 **Interface moderne** : Design responsive avec graphiques Chart.js
- 📁 **Export CSV** : Exportez vos statistiques pour analyse externe

### Intégration EDN
- 🔗 **Menu partagé Anki EDN** : S'intègre au menu centralisé pour tous les addons EDN
- ⌨️ **Raccourci clavier** : `Ctrl+Shift+P` pour accès rapide
- 🔧 **Configuration centralisée** : Gestion via le menu "⚙️ Paramètres EDN"

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
- **Raccourci** : `Ctrl+Shift+P`

### Interface Principale

#### Vue Graphique
- Cliquer sur un point pour voir les détails d'un item
- Utiliser les boutons de tri pour organiser les données
- Hover sur les graphiques pour infobulles détaillées

#### Paramètres (⚙️)
1. **Sélection de sujets** : Choisir les matières à afficher
2. **Presets** : Sauvegarder/charger des configurations
3. **Filtres avancés** : Rang, enfants, seuils personnalisés

#### Filtrage
- **Mode** : Items / Sujets / SDD
- **Rang** : Tous / Rang A uniquement / Sans rang A
- **Inclure enfants** : Afficher ou masquer les sous-items

### Presets Standards

L'addon inclut un bouton "**Sélection Standard (37)**" pour activer rapidement les 37 matières principales EDN recommandées.

## 🛠️ Compatibilité

### Requis
- **Anki** : Version 23.10 ou supérieure
- **Système** : Qt6 (Windows, macOS, Linux)
- **Deck** : Anki EDN (gratuit, disponible sur AnkiWeb)

### Optionnel
- **Autres addons EDN** : Compatible avec toute la suite d'addons EDN

## 🎯 Suite Anki EDN

Cet addon fait partie de la **suite Anki EDN**, un écosystème d'outils pour optimiser l'utilisation du deck EDN :

- **EDN Progress** (cet addon) - Statistiques et progression
- **EDN Assistant** - Fonctionnalités complémentaires
- **EDN Smart Queue** - Algorithme de tri intelligent

Tous les addons EDN partagent un menu "**Anki EDN**" dans la barre de menu et peuvent être activés/désactivés individuellement via "⚙️ Paramètres EDN".

## ❓ FAQ

### Pourquoi mes presets ne s'affichent pas ?
Les presets sont sauvegardés dans `user_state.json`. Si le problème persiste, vérifier la console Anki pour les messages `[EDN LOAD_STATE]`.

### Puis-je utiliser cet addon sans le deck EDN ?
L'addon est optimisé pour le deck EDN (tags `EDN::item-XXX`, etc.). Il fonctionnera avec d'autres decks mais les fonctionnalités seront limitées.

### Comment exporter mes statistiques ?
Utiliser le bouton "📁 Export CSV" en bas de l'interface. Le fichier CSV peut être ouvert dans Excel/Google Sheets.

### Mon graphique est vide ?
Vérifier que :
- Vous avez des cartes EDN dans votre collection
- Les filtres ne sont pas trop restrictifs
- Le seuil de suspension n'est pas trop élevé

## 🐛 Signaler un problème

Si vous rencontrez un bug :
1. Vérifier la console Anki (`Tools → Add-ons → [addon] → View Files`)
2. Noter le message d'erreur complet
3. Créer un issue sur GitHub ou laisser un commentaire sur AnkiWeb

## 📜 Licence

Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0) - Voir fichier [LICENSE](LICENSE) pour détails.

Ce projet est partagé librement pour la communauté Anki EDN.

## 🙏 Remerciements

- **Deck Anki EDN** : Pour le contenu de qualité
- **Communauté Anki** : Pour le support et les retours
- **Chart.js** : Pour la bibliothèque de graphiques

## 🔗 Liens

- **Deck Anki EDN** : [ankiweb.net/shared/info/...](https://ankiweb.net/shared/info/)
- **Documentation complète** : [GitHub Wiki](https://github.com/...)
- **Support** : [AnkiWeb Comments](https://ankiweb.net/shared/info/...)

---

**Note** : Cet addon est un projet communautaire indépendant, non affilié officiellement au deck Anki EDN.
