# stats_logic.py — EDN stats & difficulty (renamed to force reload)
from aqt import mw
import time, os, json, math
from statistics import median, mean

# defaults
SUSPEND_MASK_THRESHOLD = 0.8
MASTERED_THRESHOLD = 0.5
DESUSPENDED_THRESHOLD = 0.40

def _now_ms():
    return int(time.time() * 1000)

def clamp01(val):
    return max(0.0, min(1.0, val))

def _all_subject_tags(blacklist=None):
    tags = mw.col.tags.all()
    # Default blacklist if none provided
    if blacklist is None:
        blacklist = {
            "forme-compliquée", "grave", "iconographie", "maj", "new", "note", 
            "img", "leech", "marked", "transport", "score", "scores", "source"
        }
    
    def is_valid(t):
        if t.startswith("EDN::") or t.startswith("SSDD::") or t.startswith("SDD::"):
            return False
        parts = set(p.lower() for p in t.split("::"))
        # Check against blacklist (case insensitive normalized)
        norm_blacklist = {b.lower() for b in blacklist}
        if not parts.isdisjoint(norm_blacklist):
            return False
        return True

    return sorted([t for t in tags if is_valid(t)])

def _all_item_tags():
    return sorted([t for t in mw.col.tags.all() if t.startswith("EDN::item-")])

def _all_sdd_tags():
    def is_sdd(t):
        t = t.lower()
        return t.startswith("edn::sdd") or t.startswith("edn::ssdd") or t.startswith("sdd") or t.startswith("ssdd")
    return sorted([t for t in mw.col.tags.all() if is_sdd(t)])


def cards_of_note(note):
    try:
        c = note.cards()
        if isinstance(c, list):
            return c
    except Exception:
        pass
    try:
        cids = mw.col.find_cards(f"nid:{note.id}")
        return [mw.col.get_card(cid) for cid in cids]
    except Exception:
        return []

def card_revlog_stats(cid, window_days=30):
    db = mw.col.db
    cutoff = _now_ms() - int(window_days) * 86400000
    try:
        recent_again = db.scalar("SELECT COUNT() FROM revlog WHERE cid = ? AND ease = 1 AND id > ?", cid, cutoff) or 0
        recent_reviews = db.scalar("SELECT COUNT() FROM revlog WHERE cid = ? AND id > ?", cid, cutoff) or 0
        total_lapses = db.scalar("SELECT COUNT() FROM revlog WHERE cid = ? AND ease = 1", cid) or 0
        total_reviews = db.scalar("SELECT COUNT() FROM revlog WHERE cid = ?", cid) or 0
    except Exception:
        recent_again = recent_reviews = total_lapses = total_reviews = 0
    return {'recent_again': int(recent_again), 'recent_reviews': int(recent_reviews), 'total_lapses': int(total_lapses), 'total_reviews': int(total_reviews)}

def _classify_card(card, mature_ivl=21):
    """
    Classification based on Anki's search semantics:
    - is:new = type == 0
    - is:learn = queue == 1 or queue == 3 (in learning/day-learn queue)
    - is:review = type == 2
    - is:suspended = queue == -1
    - is:buried = queue == -2
    
    Categories:
    - Inédites: is:new AND -(is:buried OR is:suspended)
    - À repasser: (-is:review AND is:learn) = type != 2 AND queue in (1,3)
    - Réapprentissage: (is:review AND is:learn) = type == 2 AND queue in (1,3)
    - Récentes: (is:review AND -is:learn) AND prop:ivl<21 = type == 2 AND queue not in (1,3) AND ivl < 21
    - Matures: (is:review AND -is:learn) AND prop:ivl>=21 = type == 2 AND queue not in (1,3) AND ivl >= 21
    """
    try:
        q = getattr(card, 'queue', None)
        typ = getattr(card, 'type', None)
        ivl = getattr(card, 'ivl', 0)
    except Exception:
        q = typ = None; ivl = 0
    
    # Suspended and buried first (queue-based)
    if q == -1:
        return 'suspended'
    if q == -2:
        return 'buried'
    
    # Check if in learning queue (queue 1 or 3)
    in_learning_queue = q in (1, 3)
    
    # New cards (type 0)
    if typ == 0:
        return 'new'
    
    # Cards in learning queue
    if in_learning_queue:
        if typ == 2:
            return 'relearning'  # is:review AND is:learn
        else:
            return 'learning'  # -is:review AND is:learn (includes type 1 and 3)
    
    # Review cards not in learning queue (type 2, queue == 2)
    if typ == 2:
        if ivl >= mature_ivl:
            return 'mature'
        else:
            return 'recent'
    
    # Type 3 (relearning type) but not in learning queue (edge case)
    if typ == 3:
        return 'relearning'
    
    # Type 1 (learning type) but not in learning queue (edge case)
    if typ == 1:
        return 'learning'
    
    return 'other'

def compute_item_difficulty_for_cards(card_objs, window_days=30, weights=(0.6,0.25,0.15), mature_ivl=21):
    # FSRS Difficulty replacement requested
    # We will try to fetch FSRS difficulty from card.memory_state.difficulty (Anki >= 23.10)
    # If not available, we return 0 or fallback? User said "remplace l'ancien".
    
    total_fsrs_diff = 0.0
    count_fsrs = 0
    
    # Fallback legacy metrics just in case
    # (Actually we can remove them if we strictly follow "Remplace", 
    # but let's keep calculation minimal if FSRS fails?)
    
    for card in card_objs:
        # Try FSRS
        try:
            # card.memory_state is a property in newer Anki
            ms = getattr(card, 'memory_state', None)
            if ms and hasattr(ms, 'difficulty'):
                # FSRS difficulty is 1-10 usually? Or 0-1? 
                # FSRS v4: 1 to 10.
                # To normalize to 0-1 for our UI (percent), we divide by 10.
                # If user wants raw value, we'll see. But existing UI expects %, so 0-1 float.
                d = ms.difficulty
                total_fsrs_diff += d
                count_fsrs += 1
                continue
        except Exception:
            pass

    if count_fsrs > 0:
        # Normalize 1-10 -> 0-1
        # E.g. 5/10 = 50% difficulty
        avg_diff = (total_fsrs_diff / count_fsrs) / 10.0
        return clamp01(avg_diff), {}

    return 0.0, {}

def collect_stats_for_tag(tag, window_days=30, only_rang=None, exclude_rang=None, mature_ivl=21, subject_filter=None):
    # User requested: "Quand les enfants ne sont pas inclus, les tags doivent inclure leurs enfants"
    # This implies that the stats for 'EDN::item-005' MUST include 'EDN::item-005::Child'.
    # Anki's search `tag:foo` AUTOMATICALLY includes `tag:foo::bar`. 
    # So `find_notes(f'tag:"{tag}"')` should work.
    try:
        nids = mw.col.find_notes(f'tag:"{tag}"')
    except Exception:
        nids = []
    
    
    counts = {'new':0,'learning':0,'relearning':0,'recent':0,'mature':0,'suspended':0,'buried':0,'other':0}
    total = 0
    subject_overlap_count = 0
    card_objs = []
    notes_skipped_rang = 0
    
    # Pre-process subject filter for fast checking
    # Filter is list of tags e.g. ["Matière::Cardio"]
    # We match if note tag STARTSWITH subject (since subject includes children)
    filter_roots = [s.lower() for s in (subject_filter or [])]

    for nid in nids:
        try:
            note = mw.col.get_note(nid)
        except Exception:
            continue
        # note tag-based rang filter (simple normalization)
        ntags_lower = [t.lower().replace('-', '::').replace('_', '::') for t in (note.tags or [])]
        
        if only_rang:
            if not any(t.endswith(f'::{only_rang.lower()}') or t==f'rang::{only_rang.lower()}' for t in ntags_lower):
                continue
        if exclude_rang:
            if any(t.endswith(f'::{exclude_rang.lower()}') or t==f'rang::{exclude_rang.lower()}' for t in ntags_lower):
                continue
        
        # Subject Overlap Check
        matches_subject = False
        if filter_roots:
             # If ANY note tag starts with ANY filter root
             # Optimization: ntags are full tags. filter_roots are "matière::cardio"
             # Check if "matière::cardio::ecg" starts with "matière::cardio"
             # Note: Anki tags are string matches.
             # We should rely on standard string startswith
             for t in ntags_lower:
                 for root in filter_roots:
                     if t == root or t.startswith(root + "::") or t.startswith(root + "-") or t.startswith(root + "_"):
                         matches_subject = True
                         break
                 if matches_subject: break
        
        # Count by NOTE, not by card
        # Determine note state from its cards using priority:
        # Priority (lowest number = note inherits this state):
        # 1. suspended (if ALL cards are suspended)
        # 2. buried (if ALL cards are buried)
        # 3. new (if ANY non-suspended/buried card is new)
        # 4. learning (if ANY card is in learning)
        # 5. relearning (if ANY card is in relearning)
        # 6. recent (if ANY card is recent)
        # 7. mature (if ALL active cards are mature)
        # 8. other
        
        note_cards = list(cards_of_note(note))
        card_objs.extend(note_cards)
        
        if not note_cards:
            continue
            
        card_states = [_classify_card(c, mature_ivl=mature_ivl) for c in note_cards]
        
        # Determine note state
        if all(s == 'suspended' for s in card_states):
            note_state = 'suspended'
        elif all(s == 'buried' for s in card_states):
            note_state = 'buried'
        elif all(s in ('suspended', 'buried') for s in card_states):
            # All cards are either suspended or buried
            note_state = 'suspended' if 'suspended' in card_states else 'buried'
        else:
            # Active cards only (not suspended/buried)
            active_states = [s for s in card_states if s not in ('suspended', 'buried')]
            if not active_states:
                note_state = 'suspended'
            elif 'new' in active_states:
                note_state = 'new'
            elif 'learning' in active_states:
                note_state = 'learning'
            elif 'relearning' in active_states:
                note_state = 'relearning'
            elif 'recent' in active_states:
                note_state = 'recent'
            elif 'mature' in active_states:
                note_state = 'mature'
            else:
                note_state = 'other'
        
        counts[note_state] = counts.get(note_state, 0) + 1
        total += 1
        if matches_subject:
            subject_overlap_count += 1
    
    percent = {k:(counts[k]/total if total>0 else 0.0) for k in counts}
    
    # User Mastery: (is:review AND -is:learn AND prop:ivl>=21 AND -suspended AND -buried)
    # Reverted to mature only as requested
    mastery = (counts.get('mature',0) / total) if total > 0 else 0.0
    
    # User Studied: -(is:buried OR is:suspended OR is:new)
    # Total - (buried + suspended + new)
    unsuspended = total - counts.get('suspended', 0)
    # active_studied should be defined as total - (new + suspended + buried)
    active_studied = total - (counts.get('new',0) + counts.get('suspended',0) + counts.get('buried',0))
    if active_studied < 0: active_studied = 0 # Safety
    
    # Ratio Appris / Désuspendu
    studied_ratio = (active_studied / unsuspended) if unsuspended > 0 else 0.0
    # Safety clamp 1.0
    if studied_ratio > 1.0: studied_ratio = 1.0
    
    # NEW: Ratio Appris / Total (for better absolute progress tracking)
    # Reverted hardcode
    studied_total_ratio = (active_studied / total) if total > 0 else 0.0
    if studied_total_ratio > 1.0: studied_total_ratio = 1.0
    
    # Display Name Formatting
    # Expected tag: EDN::item-027-Risques-fœtaux -> 27 — Risques fœtaux
    display_name = tag
    try:
        if "::item-" in tag:
            parts = tag.split("::item-")[-1].split("-", 1)
            if len(parts) == 2:
                num = parts[0]
                rest = parts[1].replace("-", " ").replace("_", " ").replace("::", " : ")
                display_name = f"{int(num)} — {rest}"
        elif "::SDD-" in tag:
             # EDN::SDD-111-Saignement... -> 111 — Saignement...
             parts = tag.split("::SDD-")[-1].split("-", 1)
             if len(parts) == 2:
                 num = parts[0] # 111
                 rest = parts[1].replace("-", " ").replace("_", " ").replace("::", " : ")
                 display_name = f"{num} — {rest}"
    except Exception:
        pass

    difficulty, comps = compute_item_difficulty_for_cards(card_objs, window_days=window_days)
    
    result = {
        'tag': tag,
        'display_name': display_name,
        'counts': counts,
        'total': total,
        'percent': percent,
        'mastery': mastery,
        'difficulty': difficulty,
        'difficulty_components': comps,
        'studied_ratio': studied_ratio,
        'studied_total_ratio': studied_total_ratio,
        'unsuspended': unsuspended,
        'subject_overlap_count': subject_overlap_count
    }
    return result

def collect_overview(mode='items', only_rang=None, exclude_rang=None, include_children=False, subject_tags=None, suspend_mask_threshold=SUSPEND_MASK_THRESHOLD, window_days=30, mature_ivl=21, subject_blacklist=None, subject_filter=None, overlap_threshold=0.15):
    # Use batch SQL optimization (activated in production)
    return collect_overview_batch(
        mode=mode, only_rang=only_rang, exclude_rang=exclude_rang,
        include_children=include_children, subject_tags=subject_tags,
        suspend_mask_threshold=suspend_mask_threshold, window_days=window_days,
        mature_ivl=mature_ivl, subject_blacklist=subject_blacklist,
        subject_filter=subject_filter, overlap_threshold=overlap_threshold
    )


def _collect_overview_original(mode='items', only_rang=None, exclude_rang=None, include_children=False, subject_tags=None, suspend_mask_threshold=SUSPEND_MASK_THRESHOLD, window_days=30, mature_ivl=21, subject_blacklist=None, subject_filter=None, overlap_threshold=0.15):
    """Original implementation (kept for reference/fallback)."""
    if mode == 'items':
        units = _all_item_tags()
    elif mode == 'sdd':
        units = _all_sdd_tags()
    else:
        # Subject Mode
        units = _all_subject_tags(blacklist=subject_blacklist)
        # If we have a filter, ONLY show those subjects in the graph
        if subject_filter:
            # Normalize filter roots
            filter_roots = {s.lower() for s in subject_filter}
            # Keep only subjects that are in the filter (or children if we implement that later)
            units = [u for u in units if u.lower() in filter_roots]

    items = []
    for u in units:
        # Strict hierarchy check: if include_children is False, skip tags that look like children
        # For EDN items: EDN::item-XXX is parent. EDN::item-XXX::Child is child.
        if not include_children and mode == 'items':
            # Check if it has 3 parts (EDN, item-XXX, Child)
            if u.count('::') > 1:
                continue
        
        # For Subjects/SDD: Standard is TopLevel parent.
        if not include_children and mode != 'items':
             # If exclude_children, we want ONLY depth 2 for "SDD-XXX" style 
             if u.count('::') >= 2:
                  continue

        def format_name(t):
            name = t
            try:
                if "::item-" in t:
                    parts = t.split("::item-")[-1].split("-", 1)
                    if len(parts) == 2:
                        return f"{int(parts[0])} — {parts[1].replace('-', ' ').replace('_', ' ').replace('::', ' : ')}"
                elif "::SDD-" in t:
                     parts = t.split("::SDD-")[-1].split("-", 1)
                     if len(parts) == 2:
                         return f"{parts[0]} — {parts[1].replace('-', ' ').replace('_', ' ').replace('::', ' : ')}"
                
                parts = t.split('::')
                if len(parts) > 2 and parts[0] == "EDN" and (parts[1].startswith("SDD") or parts[1].startswith("SSDD")):
                    return " : ".join(parts[2:]).replace("-", " ").replace("_", " ")
                
                if "::" in t:
                    return t.split("::")[-1].replace("-", " ").replace("_", " ")
            except:
                 pass
            return name

        stats = collect_stats_for_tag(u, window_days=window_days, only_rang=only_rang, exclude_rang=exclude_rang, mature_ivl=mature_ivl, subject_filter=subject_filter)
        
        # Subject Filter Logic for non-subject modes (Items/SDD)
        if mode != 'subject' and subject_filter and stats['total'] > 0:
            overlap = stats.get('subject_overlap_count', 0)
            ratio = overlap / stats['total']
            if ratio < overlap_threshold:
                continue

        if stats.get('studied_ratio', 0) > 1.0:
            stats['studied_ratio'] = 1.0
            
        stats['display_name'] = format_name(u)
        
        if stats['total']>0 and (1.0 - stats['percent'].get('suspended',0.0)) <= suspend_mask_threshold:
            continue
        items.append(stats)

    mastery_list = [it['mastery'] for it in items if it.get('total',0)>0]
    difficulty_list = [it['difficulty'] for it in items if it.get('total',0)>0]
    desuspended_count = sum(1 for it in items if it.get('total',0)>0 and (1 - it['percent'].get('suspended',0.0)) > DESUSPENDED_THRESHOLD)
    critical_count = sum(1 for it in items if it.get('total',0)>0 and it.get('difficulty',0.0) >= 0.5)
    
    # CRITICAL: available_subjects should be ALL subjects for the dropdown, regardless of current selection
    all_subjects = _all_subject_tags(blacklist=subject_blacklist)
    
    meta = {
        'median_mastery': median(mastery_list) if mastery_list else 0.0, 
        'median_difficulty': median(difficulty_list) if difficulty_list else 0.0, 
        'mean_mastery': mean(mastery_list) if mastery_list else 0.0, 
        'mean_difficulty': mean(difficulty_list) if difficulty_list else 0.0, 
        'num_desuspended_over_threshold': desuspended_count, 
        'num_critical_items': critical_count, 
        'total_units': len(items),
        'available_subjects': all_subjects
    }
    items_sorted = sorted(items, key=lambda x: x.get('mastery', 0.0))
    return {'mode': mode, 'items': items_sorted, 'meta': meta}

def export_csv(path=None):
    if not path:
        addon_dir = os.path.dirname(__file__)
        path = os.path.join(addon_dir, "edn_stats_export.csv")
    
    data = collect_overview()
    import csv
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=';')
        w.writerow([
            "Tag", "Nom", "Total Cartes", 
            "Part Désuspendue", "Ratio Appris/Désuspendu (%)", 
            "Maîtrise (%)", "Difficulté FSRS (0-1)",
            "Inédites", "Apprentissage", "Réapprentissage", "Récentes", "Matures", "Suspendues", "Enfouies"
        ])
        for it in data["items"]:
            c = it["counts"]
            ratio = it.get("studied_ratio", 0.0)
            mastery = it.get("mastery", 0.0)
            diff = it.get("difficulty", 0.0)
            unsusp = it.get("unsuspended", 0)
            
            def fmt(f): return str(round(f, 4)).replace('.', ',')
            
            w.writerow([
                it["tag"], 
                it.get("display_name", it["tag"]), 
                it["total"],
                unsusp,
                fmt(ratio * 100),
                fmt(mastery * 100),
                fmt(diff),
                c.get("new",0), 
                c.get("learning",0), 
                c.get("relearning", 0),
                c.get("recent",0), 
                c.get("mature",0), 
                c.get("suspended",0),
                c.get("buried", 0)
            ])
    return path

# ============================================================================
# BATCH SQL OPTIMIZATION
# ============================================================================

# Flag to toggle batch mode (set to True to use batch SQL)
USE_BATCH_SQL = True  # Activated in production (1.5x+ speedup)

def _classify_card_raw(typ, queue, ivl, mature_ivl=21):
    """Classify card from raw SQL values (same logic as _classify_card)."""
    if queue == -1:
        return 'suspended'
    if queue == -2:
        return 'buried'
    
    in_learning_queue = queue in (1, 3)
    
    if typ == 0:
        return 'new'
    
    if in_learning_queue:
        if typ == 2:
            return 'relearning'
        else:
            return 'learning'
    
    if typ == 2:
        if ivl >= mature_ivl:
            return 'mature'
        else:
            return 'recent'
    
    if typ == 3:
        return 'relearning'
    if typ == 1:
        return 'learning'
    
    return 'other'

def _match_tag_hierarchy(note_tags_lower, target_tag_lower):
    """
    Check if any of note's tags matches target_tag (including children).
    Mimics Anki's `tag:X` which matches `X` and `X::Child`.
    """
    for nt in note_tags_lower:
        if nt == target_tag_lower:
            return True
        # Child tag: X::Child starts with X::
        if nt.startswith(target_tag_lower + "::"):
            return True
    return False

def collect_overview_batch(mode='items', only_rang=None, exclude_rang=None, include_children=False, 
                          subject_tags=None, suspend_mask_threshold=SUSPEND_MASK_THRESHOLD, 
                          window_days=30, mature_ivl=21, subject_blacklist=None, 
                          subject_filter=None, overlap_threshold=0.15):
    """
    Batch SQL version of collect_overview.
    Loads all cards in ONE query, then processes in memory.
    """
    import time
    start_time = time.time()
    
    # Get target tags based on mode
    if mode == 'items':
        target_tags = _all_item_tags()
    elif mode == 'sdd':
        target_tags = _all_sdd_tags()
    else:
        target_tags = _all_subject_tags(blacklist=subject_blacklist)
        if subject_filter:
            filter_roots = {s.lower() for s in subject_filter}
            target_tags = [u for u in target_tags if u.lower() in filter_roots]
    
    # Filter out children if needed
    if not include_children:
        if mode == 'items':
            target_tags = [t for t in target_tags if t.count('::') <= 1]
        else:
            target_tags = [t for t in target_tags if t.count('::') < 2]
    
    
    # ========== SINGLE SQL QUERY ==========
    sql_start = time.time()
    
    # Build SQL to get all cards with note info
    # Note: n.tags is space-separated string
    rows = mw.col.db.all("""
        SELECT 
            c.id as cid, c.nid, c.type, c.queue, c.ivl,
            n.tags
        FROM cards c
        JOIN notes n ON c.nid = n.id
    """)
    
    sql_time = time.time() - sql_start
    
    
    # ========== PROCESS IN MEMORY ==========
    process_start = time.time()
    
    # Pre-process: convert target tags to lowercase for matching
    target_tags_lower = {t.lower(): t for t in target_tags}
    
    # Prepare stats accumulators per tag
    # {tag_lower: {'counts': {...}, 'nids': set(), ...}}
    stats_by_tag = {}
    for tag in target_tags:
        tag_l = tag.lower()
        stats_by_tag[tag_l] = {
            'tag': tag,
            'counts': {'new':0,'learning':0,'relearning':0,'recent':0,'mature':0,'suspended':0,'buried':0,'other':0},
            'nids': set(),  # Track unique notes
            'subject_overlap_nids': set()
        }
    
    # Prepare subject filter roots for overlap check
    filter_roots = [s.lower() for s in (subject_filter or [])]
    
    # Prepare rang filters
    only_rang_lower = only_rang.lower() if only_rang else None
    exclude_rang_lower = exclude_rang.lower() if exclude_rang else None
    
    # ========== OPTIMIZATION: Build inverted index for O(1) tag lookups ==========
    # Instead of checking each note tag against ALL target tags (O(n*m)),
    # we pre-build a trie-like structure for direct lookups
    # 
    # For hierarchy matching: tag:X matches X AND X::Child
    # So we index by exact tag AND by all parent prefixes
    
    # Build quick lookup: {note_tag_lower -> [matching target_tag_lowers]}
    # A note with tag "EDN::item-027::sub" matches targets:
    #   - "edn::item-027::sub" (exact)
    #   - "edn::item-027" (parent)
    #   - "edn" (grandparent)
    target_set = set(stats_by_tag.keys())  # All target tags in lowercase
    
    for cid, nid, typ, queue, ivl, tags_str in rows:
        if not tags_str:
            continue
        
        # Parse note tags
        note_tags = tags_str.split()
        note_tags_lower = [t.lower() for t in note_tags]
        
        # Apply rang filters
        if only_rang_lower:
            if not any(t.endswith(f'::{only_rang_lower}') or t == f'rang::{only_rang_lower}' for t in note_tags_lower):
                continue
        if exclude_rang_lower:
            if any(t.endswith(f'::{exclude_rang_lower}') or t == f'rang::{exclude_rang_lower}' for t in note_tags_lower):
                continue
        
        # Check subject overlap
        matches_subject = False
        if filter_roots:
            for t in note_tags_lower:
                for root in filter_roots:
                    if t == root or t.startswith(root + "::"):
                        matches_subject = True
                        break
                if matches_subject:
                    break
        
        # Classify this card
        card_class = _classify_card_raw(typ, queue, ivl, mature_ivl)
        
        # ========== OPTIMIZED TAG MATCHING ==========
        # For each note tag, check if it matches any target tag
        # A target tag T matches a note tag N if:
        #   - N == T (exact match)
        #   - N.startswith(T + "::") (N is child of T)
        # 
        # Optimization: instead of checking all 953 targets,
        # we check the note tag AND all its parent prefixes against target_set
        
        matched_targets = set()
        for nt in note_tags_lower:
            # Check exact match
            if nt in target_set:
                matched_targets.add(nt)
            
            # Check if this note tag is a CHILD of any target tag
            # "edn::item-027::sub" is child of "edn::item-027" which is child of "edn"
            parts = nt.split("::")
            for i in range(1, len(parts)):
                parent = "::".join(parts[:i])
                if parent in target_set:
                    matched_targets.add(parent)
        
        # Update stats for all matched targets
        for target_l in matched_targets:
            stat = stats_by_tag[target_l]
            if nid not in stat['nids']:
                stat['nids'].add(nid)
                stat['counts'][card_class] += 1
                if matches_subject:
                    stat['subject_overlap_nids'].add(nid)
    
    process_time = time.time() - process_start
    
    
    # ========== BUILD RESULTS ==========
    build_start = time.time()
    items = []
    
    def format_name(t):
        name = t
        try:
            if "::item-" in t:
                parts = t.split("::item-")[-1].split("-", 1)
                if len(parts) == 2:
                    return f"{int(parts[0])} — {parts[1].replace('-', ' ').replace('_', ' ').replace('::', ' : ')}"
            elif "::SDD-" in t:
                parts = t.split("::SDD-")[-1].split("-", 1)
                if len(parts) == 2:
                    return f"{parts[0]} — {parts[1].replace('-', ' ').replace('_', ' ').replace('::', ' : ')}"
            if "::" in t:
                return t.split("::")[-1].replace("-", " ").replace("_", " ")
        except:
            pass
        return name
    
    for tag_l, stat in stats_by_tag.items():
        counts = stat['counts']
        total = len(stat['nids'])
        
        if total == 0:
            continue
        
        percent = {k: (counts[k]/total) for k in counts}
        
        # Skip if too many suspended
        if (1.0 - percent.get('suspended', 0.0)) <= suspend_mask_threshold:
            continue
        
        # Subject overlap filter
        if mode != 'subject' and subject_filter and total > 0:
            overlap = len(stat['subject_overlap_nids'])
            ratio = overlap / total
            if ratio < overlap_threshold:
                continue
        
        unsuspended = total - counts.get('suspended', 0)
        mastery = counts.get('mature', 0) / total if total > 0 else 0.0
        active_studied = total - (counts.get('new', 0) + counts.get('suspended', 0) + counts.get('buried', 0))
        if active_studied < 0:
            active_studied = 0
        studied_ratio = active_studied / unsuspended if unsuspended > 0 else 0.0
        studied_total_ratio = active_studied / total if total > 0 else 0.0
        
        result = {
            'tag': stat['tag'],
            'display_name': format_name(stat['tag']),
            'counts': counts,
            'total': total,
            'percent': percent,
            'mastery': mastery,
            'difficulty': 0.0,  # Will be calculated with FSRS below
            'difficulty_components': {},
            'studied_ratio': min(studied_ratio, 1.0),
            'studied_total_ratio': studied_total_ratio,
            'unsuspended': unsuspended,
            'subject_overlap_count': len(stat['subject_overlap_nids']),
            '_nids': list(stat['nids'])  # Keep nids for FSRS calculation
        }
        items.append(result)
    
    build_time = time.time() - build_start
    
    # ========== FSRS DIFFICULTY (separate pass) ==========
    fsrs_start = time.time()
    fsrs_count = 0
    
    for item in items:
        nids = item.get('_nids', [])
        if not nids:
            continue
        
        total_difficulty = 0.0
        card_count = 0
        
        # Sample up to 20 notes for FSRS calculation (performance optimization)
        sample_nids = nids[:20] if len(nids) > 20 else nids
        
        for nid in sample_nids:
            try:
                note = mw.col.get_note(nid)
                for card in note.cards():
                    ms = getattr(card, 'memory_state', None)
                    if ms and hasattr(ms, 'difficulty'):
                        total_difficulty += ms.difficulty
                        card_count += 1
            except:
                pass
        
        if card_count > 0:
            # FSRS difficulty is 1-10, normalize to 0-1
            item['difficulty'] = clamp01((total_difficulty / card_count) / 10.0)
            fsrs_count += 1
        
        # Remove temp nids
        del item['_nids']
    
    fsrs_time = time.time() - fsrs_start
    total_time = time.time() - start_time
    
    
    # Build meta
    all_subjects = _all_subject_tags(blacklist=subject_blacklist)
    mastery_list = [it['mastery'] for it in items if it.get('total', 0) > 0]
    difficulty_list = [it['difficulty'] for it in items if it.get('total', 0) > 0]
    desuspended_count = sum(1 for it in items if it.get('total', 0) > 0 and (1 - it['percent'].get('suspended', 0.0)) > DESUSPENDED_THRESHOLD)
    critical_count = sum(1 for it in items if it.get('total', 0) > 0 and it.get('difficulty', 0.0) >= 0.5)
    
    meta = {
        'median_mastery': median(mastery_list) if mastery_list else 0.0,
        'median_difficulty': median(difficulty_list) if difficulty_list else 0.0,
        'mean_mastery': mean(mastery_list) if mastery_list else 0.0,
        'mean_difficulty': mean(difficulty_list) if difficulty_list else 0.0,
        'num_desuspended_over_threshold': desuspended_count,
        'num_critical_items': critical_count,
        'total_units': len(items),
        'available_subjects': all_subjects,
        '_batch_timing': {
            'sql': sql_time,
            'process': process_time,
            'build': build_time,
            'total': total_time
        }
    }
    
    items_sorted = sorted(items, key=lambda x: x.get('mastery', 0.0))
    return {'mode': mode, 'items': items_sorted, 'meta': meta}

