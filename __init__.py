# __init__.py — EDN Progress (Anki 25.09, Qt6) - main entry & bridge
from __future__ import annotations
import os, json
from aqt import mw, gui_hooks
from aqt.qt import QDockWidget, QAction, Qt
from aqt.webview import AnkiWebView
from aqt.utils import showInfo, tooltip

from . import stats_backend

ADDON_PATH = os.path.dirname(__file__)
INDEX_HTML = os.path.join(ADDON_PATH, "web", "index.html")


def open_tag_in_browser(tag: str) -> None:
    # Use robust method to open browser and search
    from aqt import dialogs
    browser = dialogs.open("Browser", mw)
    browser.search(f'tag:"{tag}"')


def collect_lite_data(*args, **kwargs):
    """Version allégée - réduit JSON de 236KB à ~80KB"""
    # Fix: Pass arguments to backend!
    data = stats_backend.collect_overview(*args, **kwargs)
    
    lite_items = []
    for it in data['items']:
        lite_items.append({
            'tag': it['tag'],
            'display_name': it.get('display_name', it['tag']),
            'total': it['total'],
            'unsuspended': it.get('unsuspended', 0),
            'mastery': it['mastery'],
            'difficulty': it['difficulty'],
            'studied_ratio': it.get('studied_ratio', 0),
            'studied_total_ratio': it.get('studied_total_ratio', 0),
            'subject_overlap_count': it.get('subject_overlap_count', 0),
            'counts': {
                'new': it['counts'].get('new', 0),
                'suspended': it['counts'].get('suspended', 0),
                'mature': it['counts'].get('mature', 0),
                'learning': it['counts'].get('learning', 0)
            }
        })
    
    return {
        'mode': data['mode'],
        'items': lite_items,
        'meta': {
            'median_mastery': data['meta'].get('median_mastery', 0),
            'median_difficulty': data['meta'].get('median_difficulty', 0),
            'total_units': data['meta'].get('total_units', 0),
            'available_subjects': data['meta'].get('available_subjects', []),  # CRITICAL: needed for dropdown
            'num_critical_items': data['meta'].get('num_critical_items', 0)
        }
    }


def open_edn_progress() -> None:
    if not os.path.exists(INDEX_HTML):
        showInfo("EDN Progress: web/index.html introuvable dans l'addon.")
        return

    dock = QDockWidget("EDN Progress", mw)
    dock.setObjectName("EDN_PROGRESS_DOCK")
    dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)

    web = AnkiWebView(parent=mw)
    dock.setWidget(web)

    # User Request: Standard window controls (Min/Max/Close) when floating
    def on_top_level_changed(floating):
        if floating:
            # Qt6 compatibility: Use WindowType enum
            try:
                from aqt.qt import Qt
                flags = Qt.WindowType.Window
                dock.setWindowFlags(flags)
                dock.show()
            except (AttributeError, ImportError):
                # Fallback - dock already has default controls
                pass
    
    dock.topLevelChanged.connect(on_top_level_changed)

    def _on_bridge(cmd: str) -> None:
        """Bridge handler"""
        try:
            if cmd == "recompute_initial":
                try:
                    tooltip("Chargement...")
                    
                    # Try to load saved state to get last used mode and rang
                    state_file = os.path.join(ADDON_PATH, "user_state.json")
                    saved_settings = {}
                    if os.path.exists(state_file):
                        try:
                            with open(state_file, "r", encoding="utf-8") as f:
                                st = json.load(f)
                                saved_settings = st.get("settings", {})
                        except: pass
                    
                    mode = saved_settings.get("mode", "items")
                    rang = saved_settings.get("rang", "all")
                    include_children = saved_settings.get("includeChildren", False)
                    filter_by_subject = saved_settings.get("filterBySubject", False)
                    subject_filter = saved_settings.get("enabledSubjects", None)
                    if not filter_by_subject and mode != 'subject':
                        subject_filter = None
                    
                    data = collect_lite_data(
                        mode=mode,
                        only_rang='A' if rang == 'onlyA' else None,
                        exclude_rang='A' if rang == 'notA' else None,
                        include_children=include_children,
                        subject_filter=subject_filter,
                        subject_blacklist=set()
                    )
                    web.eval(f"window.EDN_reload({json.dumps(data)});")
                except Exception as e:
                    tooltip(f"Erreur: {e}")
                    import traceback
                    traceback.print_exc()
                return
                
            if cmd == "load_state":
                # Load state from JSON file
                state_file = os.path.join(ADDON_PATH, "user_state.json")
                try:
                    if os.path.exists(state_file):
                        with open(state_file, "r", encoding="utf-8") as f:
                            state = json.load(f)
                    else:
                        state = {"presets": {}, "settings": {}}
                    web.eval(f"window.EDN_receiveState({json.dumps(state)});")
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    web.eval("window.EDN_receiveState({});")
                return

            if cmd.startswith("save_state "):
                # Save state to JSON file
                state_file = os.path.join(ADDON_PATH, "user_state.json")
                try:
                    payload = json.loads(cmd[len("save_state "):])
                    with open(state_file, "w", encoding="utf-8") as f:
                        json.dump(payload, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    tooltip(f"Erreur sauvegarde: {e}")
                return

            if cmd == "get_config":
                # Return the entire addon config (presets, last state)
                conf = mw.addonManager.getConfig(__name__) or {}
                if not conf:
                    conf = {"presets": {}, "last_state": {}}
                web.eval(f"window.EDN_receiveConfig({json.dumps(conf)});")
                return

            if cmd.startswith("save_config "):
                # Save updated config
                try:
                    payload = json.loads(cmd[len("save_config "):])
                    conf = mw.addonManager.getConfig(__name__) or {}
                    conf.update(payload)
                    mw.addonManager.writeConfig(__name__, conf)
                except Exception:
                    pass
                return

            if cmd.startswith("recompute "):
                payload = json.loads(cmd[len("recompute "):])
                tooltip(f"Chargement {payload.get('mode')}...")
                
                data = collect_lite_data(
                    mode=payload.get("mode", "items"),
                    only_rang=payload.get("only_rang"),
                    exclude_rang=payload.get("exclude_rang"),
                    include_children=payload.get("include_children", False),
                    suspend_mask_threshold=payload.get("mask_threshold", 0.8),
                    window_days=payload.get("window_days", 30),
                    mature_ivl=payload.get("mature_ivl", 21),
                    subject_blacklist=set(),
                    subject_filter=payload.get("subject_filter", None),
                    overlap_threshold=payload.get("overlap_threshold", 15)
                )
                try:
                    web.eval(f"window.EDN_reload({json.dumps(data)});")
                except Exception as e:
                    tooltip(f"Erreur: {e}")
                return

            if cmd == "open_tag_browser":
                # Use the fuzzy search tag selector
                from .tag_selector import TagSelectorDialog
                
                all_tags = mw.col.tags.all()
                # Filter to show only relevant tags (EDN items, SDD, Matière)
                item_tags = [t for t in all_tags if t.startswith("EDN::item-") or t.startswith("EDN::SDD") or t.startswith("Matière::")]
                
                dialog = TagSelectorDialog(
                    parent=mw,
                    tags=item_tags,
                    windowtitle="Ajouter un Item / Tag",
                    multi_selection=False,
                )
                
                if dialog.exec() and dialog.sel_keys_list:
                    tag = dialog.sel_keys_list[0]
                    # Get display name
                    display_name = tag
                    if "::item-" in tag:
                        try:
                            parts = tag.split("::item-")[-1].split("-", 1)
                            if len(parts) == 2:
                                display_name = f"{int(parts[0])} — {parts[1].replace('-', ' ')}"
                        except: pass
                    # Send back to JS
                    web.eval(f"window.EDN_addCustomTag('{tag}', '{display_name}');")
                return

            if cmd.startswith("get_tag_stats "):
                tag = cmd[len("get_tag_stats "):]
                # Calculate stats for this specific tag and add to current data
                from . import stats_backend as sb
                stats = sb.collect_stats_for_tag(tag)
                # Send to JS to add to display
                web.eval(f"window.EDN_addTagStats({json.dumps(stats)});")
                return

            if cmd.startswith("open_search "):
                query = cmd[len("open_search "):]
                # Open browser with search query
                from aqt import dialogs
                browser = dialogs.open("Browser", mw)
                if hasattr(browser, "setFilter"):
                    browser.setFilter(query)
                elif hasattr(browser.form.searchEdit.lineEdit(), "setText"):
                    browser.form.searchEdit.lineEdit().setText(query)
                    browser.onSearchActivated()
                else:
                    # Fallback for very new/old versions
                    mw.col.find_notes(query) # Just to ensure cache?
                    browser.search(query)
                return

            if cmd == "export_csv":
                from aqt.utils import getSaveFile
                from . import stats_backend
                
                # Fix: getSaveFile(parent, title, dir, key, ext) or similar depending on Anki version
                # Correct usage for recent Anki: getSaveFile(mw, "Title", "def", "key", ".csv") 
                # or getSaveFile(mw, title="...", dir_description="...", key="...", ext=".csv")
                
                path = getSaveFile(
                    mw,
                    "Exporter CSV",
                    "edn_export.csv",
                    "edn_export_csv",
                    ".csv"
                )
                if not path:
                    return # Cancelled

                try:
                    # Pass path to backend
                    final_path = stats_backend.export_csv(path=path)
                    showInfo(f"EDN: CSV exporté → {final_path}")
                except Exception as e:
                    showInfo(f"Erreur export CSV: {e}")
                return

            tooltip(f"Commande inconnue EDN: {cmd}")

        except Exception as e:
            tooltip(f"EDN bridge error: {e}")
            import traceback
            traceback.print_exc()

    with open(INDEX_HTML, "r", encoding="utf-8") as f:
        html = f.read()

    # Pas de chargement initial - évite freeze
    initial = {"mode":"items","items":[], "meta": {}, "loading": True}
    
    # CRITICAL FIX: Load saved state (presets + settings) BEFORE recompute_initial
    # This ensures presets are available in JavaScript cache on startup
    html = html.replace("/*__DATA_INJECTION__*/", f"window.EDN_DATA = {json.dumps(initial)}; setTimeout(function() {{ if(window.pycmd) {{ pycmd('load_state'); setTimeout(function() {{ pycmd('recompute_initial'); }}, 50); }} }}, 100);")

    web.stdHtml(html)

    # Install bridge
    try:
        web.set_bridge_command(_on_bridge, web)
    except TypeError:
        try:
            web.set_bridge_command(_on_bridge, context=web)
        except Exception:
            pass

    # Attach dock
    try:
        mw.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
    except Exception:
        mw.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)

    dock.show()


def init_edn_progress():
    """Initialize EDN Progress and register with shared menu."""
    try:
        from .shared_menu import register_module, register_action
        
        # Register module
        if not register_module(
            module_id="edn_progress",
            name="EDN Progress",
            description="Statistiques de progression et difficulté des items EDN",
            default_enabled=True
        ):
            return  # Module disabled by user
        
        # Register menu action
        register_action(
            module_id="edn_progress",
            label="EDN Progress",
            callback=open_edn_progress,
            shortcut="Ctrl+U"
        )
    except ImportError:
        # Fallback if shared_menu not available
        action = QAction("EDN Progress", mw)
        action.triggered.connect(open_edn_progress)
        mw.form.menuTools.addAction(action)
    except Exception:
        import traceback
        traceback.print_exc()

gui_hooks.main_window_did_init.append(init_edn_progress)
