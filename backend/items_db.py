"""
OSRSBox item database loader and helper functions.
Loads items JSON at startup and caches in memory.
"""
import json
import os
from typing import Optional, Dict, Any

# In-memory cache for items
_items_cache: Optional[Dict[str, Any]] = None


def load_items_db() -> Dict[str, Any]:
    """
    Load OSRSBox items database from local file.
    Caches in memory after first load.
    """
    global _items_cache
    
    if _items_cache is not None:
        return _items_cache
    
    # Load from local file
    local_path = os.path.join(os.path.dirname(__file__), "data", "items_osrsbox_min.json")
    if os.path.exists(local_path):
        try:
            with open(local_path, 'r', encoding='utf-8') as f:
                _items_cache = json.load(f)
                print(f"[ITEMS DB] Loaded {len(_items_cache)} items from local file")
                return _items_cache
        except Exception as e:
            print(f"[ITEMS DB WARNING] Failed to load local items file: {e}")
    else:
        print(f"[ITEMS DB WARNING] Local items file not found: {local_path}")
    
    # Return empty dict as fallback
    _items_cache = {}
    return _items_cache


def get_item(name: str) -> Optional[Dict[str, Any]]:
    """
    Get item by name (case-insensitive partial match).
    Returns: {slot, stats?, requirements?, tradeable?}
    """
    items_db = load_items_db()
    if not items_db:
        return None
    
    # Normalize search name
    search_name = name.lower().strip()
    
    # Find item by name (OSRSBox uses 'name' field)
    for item_id, item_data in items_db.items():
        item_name = item_data.get('name', '').lower()
        if search_name in item_name or item_name in search_name:
            # Extract relevant fields
            equipment = item_data.get('equipment', {})
            slot = equipment.get('slot', None)
            
            result = {
                'slot': slot,
                'tradeable': item_data.get('tradeable', None),
            }
            
            # Add requirements if present
            requirements = item_data.get('requirements', {})
            if requirements:
                result['requirements'] = requirements
            
            # Add stats if present (optional for now)
            if equipment:
                stats = {}
                for stat_key in ['attack_stab', 'attack_slash', 'attack_crush', 'attack_ranged', 'attack_magic',
                                'defence_stab', 'defence_slash', 'defence_crush', 'defence_ranged', 'defence_magic',
                                'melee_strength', 'ranged_strength', 'magic_damage', 'prayer']:
                    if stat_key in equipment:
                        stats[stat_key] = equipment[stat_key]
                if stats:
                    result['stats'] = stats
            
            return result
    
    return None


# Load items at module import
load_items_db()

