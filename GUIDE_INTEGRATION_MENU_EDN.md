# Guide d'Intégration au Menu Anki EDN

Ce guide explique comment intégrer un **nouvel addon** au système de menu partagé Anki EDN, surtout pour les addons créés **après** l'existence du menu.

---

## 📋 Vue d'ensemble

Le système `shared_menu.py` permet à tous les addons EDN de partager un seul menu "Anki EDN" dans la barre de menu d'Anki, avec :
- ✅ Activation/désactivation des modules
- ✅ Raccourcis personnalisables
- ✅ Configuration centralisée
- ✅ Dialog de paramètres intégré

---

## 🚀 Intégration d'un nouvel addon

### Étape 1 : Structure du projet

```
MonNouvelAddonEDN/
├── __init__.py          # Point d'entrée
├── shared_menu.py       # ← COPIER depuis Anki_EDN_Assistant
├── ma_fonction.py       # Votre code
└── ...
```

**Important** : Copier le fichier `shared_menu.py` depuis `Anki_EDN_Assistant` dans votre nouvel addon.

---

### Étape 2 : Code d'intégration dans `__init__.py`

```python
"""
Mon Nouvel Addon EDN
Description de l'addon
"""
from aqt import gui_hooks
from .shared_menu import register_module, register_action

def init_mon_addon():
    """Initialise l'addon et s'enregistre au menu EDN."""
    
    # 1. Enregistrer le module
    # Si l'utilisateur a désactivé ce module, la fonction retourne False
    if not register_module(
        module_id="mon_addon",           # ID unique (lowercase, underscores)
        name="Mon Addon",                # Nom affiché dans les paramètres
        description="Description courte",# Description pour l'UI
        default_enabled=True             # Activé par défaut
    ):
        return  # Module désactivé, ne rien faire
    
    # 2. Enregistrer vos actions au menu
    register_action(
        module_id="mon_addon",
        label="🎯 Ma Fonctionnalité Principale",
        callback=ma_fonction_principale,
        shortcut="Ctrl+Shift+M",         # Optionnel
        icon=None                         # Optionnel (ou inclus dans label)
    )
    
    register_action(
        module_id="mon_addon",
        label="📊 Autre Fonctionnalité",
        callback=autre_fonction,
        shortcut="Ctrl+Shift+O"
    )
    
    # 3. Autres initialisations de votre addon
    # ...

# Attacher au démarrage d'Anki
gui_hooks.main_window_did_init.append(init_mon_addon)
```

---

### Étape 3 : Définir vos fonctions

```python
# Dans ma_fonction.py ou __init__.py

def ma_fonction_principale():
    """Fonction appelée depuis le menu."""
    from aqt.utils import showInfo
    showInfo("Ma fonctionnalité EDN !")

def autre_fonction():
    """Autre fonction du menu."""
    # Votre code ici
    pass
```

---

## 🔧 Scénarios d'installation

### Scénario 1 : Menu principal déjà installé

Si `Anki_EDN_Assistant` (ou un autre addon avec le menu) est déjà installé :
- ✅ Le menu "Anki EDN" existe déjà
- ✅ Votre addon s'ajoute automatiquement au menu
- ✅ Partage la même instance de menu

### Scénario 2 : Votre addon installé en premier

Si votre addon est le premier addon EDN installé :
- ✅ `shared_menu.py` crée le menu "Anki EDN"
- ✅ Votre addon s'enregistre
- ✅ Les futurs addons EDN s'y ajouteront

**Conclusion** : Peu importe l'ordre d'installation, ça fonctionne ! 🎉

---

## 📚 Référence API `shared_menu.py`

### `register_module(module_id, name, description, default_enabled)`

Enregistre un module dans le système EDN.

**Paramètres** :
- `module_id` (str) : Identifiant unique (ex: `"smart_queue"`)
- `name` (str) : Nom affiché dans les paramètres
- `description` (str) : Description du module
- `default_enabled` (bool) : Activé par défaut (généralement `True`)

**Retour** : `bool` - `True` si module activé, `False` si désactivé par l'utilisateur

**Exemple** :
```python
if register_module("mon_module", "Mon Module", "Description"):
    # Module activé, continuer
    pass
else:
    # Module désactivé par l'utilisateur, ne rien faire
    return
```

---

### `register_action(module_id, label, callback, shortcut, icon)`

Ajoute une action au menu "Anki EDN".

**Paramètres** :
- `module_id` (str) : ID du module (doit avoir été enregistré)
- `label` (str) : Texte du menu (peut inclure emoji: `"🎯 Ma Feature"`)
- `callback` (callable) : Fonction à appeler au clic
- `shortcut` (str, optionnel) : Raccourci clavier (ex: `"Ctrl+Shift+Q"`)
- `icon` (str, optionnel) : Chemin icône (ou `None` si emoji dans label)

**Retour** : `QAction` ou `None` si module désactivé

**Exemple** :
```python
register_action(
    module_id="mon_module",
    label="🔧 Paramètres",
    callback=ouvrir_parametres,
    shortcut="Ctrl+Shift+P"
)
```

---

### `get_config()` / `save_config(config)`

Gestion de la configuration persistante.

**get_config()** :
```python
config = get_config()
# Structure :
# {
#   "modules": {"module_id": True/False},
#   "shortcuts": {"module_id": "Ctrl+..."},
#   "custom_key": "votre donnée"
# }
```

**save_config(config)** :
```python
config = get_config()
config["ma_cle"] = "ma_valeur"
save_config(config)
```

**Note** : La config est partagée entre tous les addons EDN. Utilisez des clés préfixées par votre `module_id` pour éviter les conflits.

---

## 🎨 Bonnes Pratiques

### 2. Raccourcis cohérents

Utilisez le pattern `Ctrl+Shift+LETTRE` pour éviter les conflits :
```python
# ✅ Bon
"Ctrl+Shift+Q"  # Smart Queue
"Ctrl+Shift+L"  # Linked Cards

# ❌ Éviter
"Ctrl+Q"        # Peut entrer en conflit avec Anki
```

### 3. Gestion gracieuse de la désactivation

```python
def init_mon_addon():
    if not register_module(...):
        # Module désactivé, nettoyer les hooks si nécessaire
        return
    
    # Enregistrer les actions SEULEMENT si module activé
    register_action(...)
```

### 4. Configuration personnalisée

```python
# Stocker votre config
config = get_config()
if "mon_module" not in config:
    config["mon_module"] = {
        "option1": True,
        "option2": 42
    }
save_config(config)

# Lire votre config
config = get_config()
mes_options = config.get("mon_module", {})
```

---
## ✅ Checklist d'intégration

Avant de publier votre addon, vérifier :

- [ ] `shared_menu.py` copié dans votre addon
- [ ] Module enregistré avec `register_module()`
- [ ] Actions enregistrées avec `register_action()`
- [ ] Raccourcis clavier définis (pattern `Ctrl+Shift+X`)
- [ ] Gestion de la désactivation (retour si module désactivé)
- [ ] Tests : addon installé seul
- [ ] Tests : addon installé avec autre addon EDN
- [ ] Documentation utilisateur mise à jour

---

## 🐛 Dépannage

### Le menu n'apparaît pas

**Cause** : `shared_menu.py` manquant ou erreur d'import

**Solution** :
```python
try:
    from .shared_menu import register_module, register_action
except ImportError as e:
    print(f"Erreur import shared_menu: {e}")
    return
```

### Mes actions n'apparaissent pas

**Cause** : Module désactivé par l'utilisateur

**Vérification** :
```python
if not register_module(...):
    print("Module désactivé par l'utilisateur")
    return
```

### Conflit de raccourcis

**Solution** : Utiliser des raccourcis uniques ou vérifier dans "⚙️ Paramètres EDN"

---

## 📞 Support

Pour questions ou problèmes d'intégration :
- Vérifier que `shared_menu.py` est à jour
- Consulter le code source de `Anki_EDN_Assistant` comme référence
- Tester avec les autres addons EDN installés

---

## 🎯 Exemple complet

Voir `Anki_EDN_Assistant/__init__.py` pour un exemple de référence complet.
