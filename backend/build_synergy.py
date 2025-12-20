"""
Build synergy rules and constraints for gear tiers.
Defines how different tiers should differ fundamentally, not just in power level.
"""
from typing import Dict, List, Optional, Set, Tuple
from items_db import get_item


# Synergy rules per tier
SYNERGY_RULES = {
    "budget": {
        "set_bonuses": False,  # No set bonuses allowed
        "synergy_count": 0,  # No synergies (mix-and-match only)
        "max_set_pieces": 0,  # No items from same set
        "description": "Budget tier: Mix-and-match gear, no set bonuses, no synergies. Focus on individual item value."
    },
    "progression": {
        "set_bonuses": False,  # No full set bonuses
        "synergy_count": 1,  # Allow one synergy (e.g., weapon + amulet combo)
        "max_set_pieces": 2,  # Max 2 pieces from same set
        "description": "Progression tier: One synergy allowed, no full sets. Balanced mix of individual items and one key combo."
    },
    "spot_specific": {
        "set_bonuses": True,  # Allow set bonuses for context-specific builds
        "synergy_count": 2,  # Allow 2 synergies (e.g., Dharok's set + specific method)
        "max_set_pieces": 4,  # Allow up to 4 pieces from same set
        "description": "Spot-specific tier: Context-optimized builds with set bonuses and multiple synergies."
    },
    "bis": {
        "set_bonuses": True,  # Full set bonuses allowed
        "synergy_count": 3,  # Multiple synergies (full optimization)
        "max_set_pieces": 10,  # No limit (full sets allowed)
        "description": "BiS tier: Full optimization with set bonuses and multiple synergies. Maximum power."
    }
}


# Known item sets (for synergy detection)
ITEM_SETS = {
    "dharok": {"Dharok's Helm", "Dharok's Platebody", "Dharok's Platelegs", "Dharok's Greataxe"},
    "torag": {"Torag's Helm", "Torag's Platebody", "Torag's Platelegs", "Torag's Hammers"},
    "verac": {"Verac's Helm", "Verac's Brassard", "Verac's Plateskirt", "Verac's Flail"},
    "guthan": {"Guthan's Helm", "Guthan's Platebody", "Guthan's Chainskirt", "Guthan's Warspear"},
    "ahrim": {"Ahrim's Hood", "Ahrim's Robetop", "Ahrim's Robeskirt", "Ahrim's Staff"},
    "karil": {"Karil's Coif", "Karil's Leathertop", "Karil's Leatherskirt", "Karil's Crossbow"},
    "dragon": {"Dragon Med Helm", "Dragon Chainbody", "Dragon Platelegs", "Dragon Scimitar", "Dragon Boots"},
    "barrows_gloves": {"Barrows Gloves"},  # Special case: single item but part of quest set
}


# Known synergies (item combinations that work well together)
ITEM_SYNERGIES = {
    # Weapon + Amulet synergies
    ("Dharok's Greataxe", "Amulet of Torture"): "Dharok's set bonus + Torture strength bonus",
    ("Abyssal Whip", "Amulet of Fury"): "Whip accuracy + Fury all-around stats",
    ("Dragon Scimitar", "Amulet of Glory"): "Scimitar speed + Glory strength",
    
    # Ring + Cape synergies
    ("Berserker Ring (i)", "Fire Cape"): "Imbued ring + Fire Cape strength bonus",
    ("Berserker Ring (i)", "Infernal Cape"): "Imbued ring + Infernal Cape max strength",
    
    # Set piece synergies
    ("Dharok's Platebody", "Dharok's Platelegs"): "Dharok's set pieces (partial set bonus)",
    ("Torag's Platebody", "Torag's Platelegs"): "Torag's set pieces (defence synergy)",
    
    # Weapon + Offhand synergies
    ("Abyssal Whip", "Dragon Defender"): "Whip + Defender accuracy and strength",
    ("Dragon Scimitar", "Dragon Defender"): "Scimitar + Defender combo",
}


def get_item_set(item_name: str) -> Optional[str]:
    """Get the set name an item belongs to, if any."""
    item_lower = item_name.lower()
    for set_name, set_items in ITEM_SETS.items():
        for set_item in set_items:
            if set_item.lower() in item_lower or item_lower in set_item.lower():
                return set_name
    return None


def count_set_pieces(gear: List[str]) -> Dict[str, int]:
    """Count how many pieces from each set are in the gear list."""
    set_counts = {}
    for item in gear:
        set_name = get_item_set(item)
        if set_name:
            set_counts[set_name] = set_counts.get(set_name, 0) + 1
    return set_counts


def count_synergies(gear: List[str]) -> int:
    """Count the number of synergies present in the gear list."""
    synergy_count = 0
    gear_set = set(gear)
    
    for (item1, item2), _ in ITEM_SYNERGIES.items():
        # Check if both items are in gear (order-independent)
        if item1 in gear_set and item2 in gear_set:
            synergy_count += 1
    
    return synergy_count


def validate_gear_tier(gear: List[str], tier: str) -> Tuple[bool, Optional[str]]:
    """
    Validate gear list against tier synergy rules.
    Returns: (is_valid, error_message)
    """
    if tier not in SYNERGY_RULES:
        return False, f"Unknown tier: {tier}"
    
    rules = SYNERGY_RULES[tier]
    
    # Check set piece limits
    set_counts = count_set_pieces(gear)
    max_set_pieces = rules["max_set_pieces"]
    for set_name, count in set_counts.items():
        if count > max_set_pieces:
            return False, f"Tier '{tier}' allows max {max_set_pieces} pieces from set '{set_name}', found {count}"
    
    # Check set bonuses
    if not rules["set_bonuses"]:
        # No set bonuses means no full sets (3+ pieces from same set)
        for set_name, count in set_counts.items():
            if count >= 3:
                return False, f"Tier '{tier}' does not allow set bonuses (found {count} pieces from '{set_name}')"
    
    # Check synergy count
    synergy_count = count_synergies(gear)
    max_synergies = rules["synergy_count"]
    if synergy_count > max_synergies:
        return False, f"Tier '{tier}' allows max {max_synergies} synergies, found {synergy_count}"
    
    return True, None


def get_tier_description(tier: str) -> str:
    """Get human-readable description of tier rules."""
    return SYNERGY_RULES.get(tier, {}).get("description", f"Unknown tier: {tier}")

