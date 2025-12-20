"""
Auto-construct gear options for builds using candidate items.
Currently only supports nmz_melee context.
"""
import json
import os
from typing import Dict, List, Optional
from build_synergy import validate_gear_tier, get_item_set, count_set_pieces, count_synergies, SYNERGY_RULES


def load_candidates(context: str) -> List[Dict]:
    """Load candidate items for a specific context"""
    if context != "nmz_melee":
        return []
    
    candidates_path = os.path.join(os.path.dirname(__file__), "data", "candidates_nmz_melee.json")
    try:
        with open(candidates_path, 'r') as f:
            data = json.load(f)
            return data.get("candidates", [])
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[BUILD CONSTRUCTOR WARNING] Failed to load candidates for {context}: {e}")
        return []


def score_item(item: Dict, tier: str, current_gear: List[str], slot: str) -> float:
    """
    Score an item for selection. Higher score = better choice.
    Prefers strength then accuracy, avoids set_piece for budget.
    """
    score = 0.0
    
    # Base score from tier match
    if tier in item.get("tier_tags", []):
        score += 10.0
    
    # Prefer strength items
    if "strength" in item.get("tags", []):
        score += 5.0
    
    # Prefer accuracy items
    if "accuracy" in item.get("tags", []):
        score += 3.0
    
    # Penalize set_piece for budget tier
    if tier == "budget" and "set_piece" in item.get("tags", []):
        score -= 20.0
    
    # Prefer hp_synergy for spot_specific
    if tier == "spot_specific" and "hp_synergy" in item.get("tags", []):
        score += 5.0
    
    # Prefer hp_synergy for bis
    if tier == "bis" and "hp_synergy" in item.get("tags", []):
        score += 3.0
    
    return score


def construct_gear_option(
    candidates: List[Dict],
    tier: str,
    membership: str,
    game_mode: str,
    slots: List[str]
) -> Optional[List[str]]:
    """
    Construct a gear option for the given tier by selecting one item per slot.
    Applies filters and synergy rules.
    """
    # Filter candidates by membership and iron status
    filtered = []
    for candidate in candidates:
        # Membership filter: member_only=True means members-only
        if membership == "f2p" and candidate.get("member_only", False):
            continue  # Skip members-only items for F2P
        
        # Iron filter
        if game_mode in ["ironman", "hcim", "gim"] and not candidate.get("iron_ok", False):
            continue  # Skip non-iron items for iron accounts
        
        # Tier filter
        if tier not in candidate.get("tier_tags", []):
            continue  # Skip items not tagged for this tier
        
        filtered.append(candidate)
    
    if not filtered:
        return None
    
    # Select one item per slot
    selected_gear = []
    selected_items = []
    
    for slot in slots:
        # Get candidates for this slot
        slot_candidates = [c for c in filtered if c.get("slot") == slot]
        if not slot_candidates:
            continue  # Skip slot if no candidates
        
        # Score and sort candidates
        scored = [(score_item(c, tier, selected_gear, slot), c) for c in slot_candidates]
        scored.sort(reverse=True, key=lambda x: x[0])
        
        # Try candidates in order until we find one that passes synergy rules
        for score, candidate in scored:
            test_gear = selected_gear + [candidate["name"]]
            
            # Quick validation: check if adding this item would violate rules
            is_valid, _ = validate_gear_tier(test_gear, tier)
            if is_valid:
                selected_gear.append(candidate["name"])
                selected_items.append(candidate)
                break
    
    # Final validation
    if not selected_gear:
        return None
    
    is_valid, error_msg = validate_gear_tier(selected_gear, tier)
    if not is_valid:
        print(f"[BUILD CONSTRUCTOR] Generated gear for tier '{tier}' failed validation: {error_msg}")
        return None
    
    return selected_gear


def auto_construct_nmz_melee_build(
    build_template: Dict,
    membership: str,
    game_mode: str
) -> Dict:
    """
    Auto-construct gear options for nmz_melee build.
    Replaces hardcoded gear_options[*].gear with auto-generated gear.
    """
    candidates = load_candidates("nmz_melee")
    if not candidates:
        # Fallback to original build if no candidates
        return build_template
    
    slots = ["weapon", "offhand", "helm", "body", "legs", "boots", "gloves", "amulet", "ring", "cape"]
    tiers = ["budget", "progression", "spot_specific", "bis"]
    
    # Get original gear_options structure
    original_options = build_template.get("gear_options", [])
    new_options = []
    
    for option in original_options:
        tier = option.get("id", "")
        if tier not in tiers:
            # Keep non-tier options as-is
            new_options.append(option)
            continue
        
        # Construct gear for this tier
        constructed_gear = construct_gear_option(candidates, tier, membership, game_mode, slots)
        
        if constructed_gear:
            # Replace gear but keep other fields
            new_option = option.copy()
            new_option["gear"] = constructed_gear
            new_options.append(new_option)
        else:
            # Fallback to original if construction failed
            print(f"[BUILD CONSTRUCTOR] Failed to construct gear for tier '{tier}', using original")
            new_options.append(option)
    
    # Create new build with constructed gear
    new_build = build_template.copy()
    new_build["gear_options"] = new_options
    return new_build

