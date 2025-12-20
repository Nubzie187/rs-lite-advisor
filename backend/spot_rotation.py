"""
Spot Rotation - provides alternate training locations for the same goal
"""
from typing import List, Dict, Optional

# Training spot data organized by membership, style, and level bands
SPOT_DATA = {
    "f2p": {
        "melee": {
            "1-20": [
                {"name": "Lumbridge Cows", "reason": "Safe, close to bank, good for beginners", "requirements": None, "tags": ["safe", "beginner"]},
                {"name": "Al Kharid Warriors", "reason": "Better XP than cows, slightly more dangerous", "requirements": None, "tags": ["xp", "combat"]},
                {"name": "Goblins (Lumbridge)", "reason": "Very safe, low damage, good for first levels", "requirements": None, "tags": ["safe", "beginner"]},
                {"name": "Chickens (Lumbridge)", "reason": "Extremely safe, minimal damage", "requirements": None, "tags": ["safe", "beginner"]}
            ],
            "21-40": [
                {"name": "Al Kharid Warriors", "reason": "Best F2P XP for mid-levels, close to bank", "requirements": None, "tags": ["xp", "combat"]},
                {"name": "Hill Giants", "reason": "Good drops, decent XP, requires 28 combat", "requirements": "28 combat", "tags": ["drops", "combat"]},
                {"name": "Moss Giants", "reason": "Better drops than Hill Giants, requires 30 combat", "requirements": "30 combat", "tags": ["drops", "combat"]},
                {"name": "Stronghold of Security", "reason": "Safe, good XP, requires completion", "requirements": "Stronghold completion", "tags": ["safe", "xp"]}
            ],
            "41-60": [
                {"name": "Hill Giants", "reason": "Best F2P training spot, good drops", "requirements": "28 combat", "tags": ["drops", "xp"]},
                {"name": "Moss Giants", "reason": "Better drops, slightly less XP than Hill Giants", "requirements": "30 combat", "tags": ["drops", "combat"]},
                {"name": "Ogress Warriors", "reason": "Excellent drops, requires completion of Corsair Curse", "requirements": "Corsair Curse quest", "tags": ["drops", "money"]},
                {"name": "Stronghold of Security", "reason": "Safe alternative, consistent XP", "requirements": "Stronghold completion", "tags": ["safe", "xp"]}
            ],
            "61+": [
                {"name": "Hill Giants", "reason": "Best F2P option, consistent XP and drops", "requirements": "28 combat", "tags": ["drops", "xp"]},
                {"name": "Ogress Warriors", "reason": "Best F2P money maker, requires quest", "requirements": "Corsair Curse quest", "tags": ["drops", "money"]},
                {"name": "Moss Giants", "reason": "Good balance of XP and drops", "requirements": "30 combat", "tags": ["drops", "combat"]}
            ]
        },
        "ranged": {
            "1-20": [
                {"name": "Lumbridge Cows", "reason": "Safe, good for early ranged training", "requirements": None, "tags": ["safe", "beginner"]},
                {"name": "Chickens (Lumbridge)", "reason": "Very safe, minimal damage", "requirements": None, "tags": ["safe", "beginner"]},
                {"name": "Goblins (Lumbridge)", "reason": "Safe, good for first ranged levels", "requirements": None, "tags": ["safe", "beginner"]}
            ],
            "21-40": [
                {"name": "Al Kharid Warriors", "reason": "Best F2P ranged XP, safe distance", "requirements": None, "tags": ["xp", "safe"]},
                {"name": "Hill Giants", "reason": "Good XP and drops, safe with ranged", "requirements": "28 combat", "tags": ["drops", "xp"]}
            ],
            "41-60": [
                {"name": "Hill Giants", "reason": "Best F2P ranged training, good drops", "requirements": "28 combat", "tags": ["drops", "xp"]},
                {"name": "Moss Giants", "reason": "Better drops, safe with ranged", "requirements": "30 combat", "tags": ["drops", "combat"]}
            ],
            "61+": [
                {"name": "Hill Giants", "reason": "Best F2P ranged option", "requirements": "28 combat", "tags": ["drops", "xp"]},
                {"name": "Ogress Warriors", "reason": "Best F2P money maker with ranged", "requirements": "Corsair Curse quest", "tags": ["drops", "money"]}
            ]
        },
        "magic": {
            "1-20": [
                {"name": "Chickens (Lumbridge)", "reason": "Very safe, good for early magic", "requirements": None, "tags": ["safe", "beginner"]},
                {"name": "Lumbridge Cows", "reason": "Safe, decent magic XP", "requirements": None, "tags": ["safe", "beginner"]},
                {"name": "Goblins (Lumbridge)", "reason": "Safe, minimal damage", "requirements": None, "tags": ["safe", "beginner"]}
            ],
            "21-40": [
                {"name": "Al Kharid Warriors", "reason": "Best F2P magic XP", "requirements": None, "tags": ["xp", "safe"]},
                {"name": "Hill Giants", "reason": "Good XP and drops with magic", "requirements": "28 combat", "tags": ["drops", "xp"]}
            ],
            "41-60": [
                {"name": "Hill Giants", "reason": "Best F2P magic training", "requirements": "28 combat", "tags": ["drops", "xp"]},
                {"name": "Moss Giants", "reason": "Better drops, safe with magic", "requirements": "30 combat", "tags": ["drops", "combat"]}
            ],
            "61+": [
                {"name": "Hill Giants", "reason": "Best F2P magic option", "requirements": "28 combat", "tags": ["drops", "xp"]},
                {"name": "Ogress Warriors", "reason": "Best F2P money maker with magic", "requirements": "Corsair Curse quest", "tags": ["drops", "money"]}
            ]
        }
    },
    "p2p": {
        "melee": {
            "1-20": [
                {"name": "Lumbridge Cows", "reason": "Safe, close to bank, good for beginners", "requirements": None, "tags": ["safe", "beginner"]},
                {"name": "Rock Crabs", "reason": "Best early-game XP, high HP, AFK-friendly", "requirements": "15 combat", "tags": ["xp", "afk"]},
                {"name": "Sand Crabs", "reason": "Excellent XP, very AFK, requires 15 combat", "requirements": "15 combat", "tags": ["xp", "afk"]},
                {"name": "Ammonite Crabs", "reason": "Best early-game XP, requires 15 combat", "requirements": "15 combat", "tags": ["xp", "afk"]}
            ],
            "21-40": [
                {"name": "Sand Crabs", "reason": "Best early-game XP, very AFK", "requirements": "15 combat", "tags": ["xp", "afk"]},
                {"name": "Ammonite Crabs", "reason": "Best early-game XP rates", "requirements": "15 combat", "tags": ["xp", "afk"]},
                {"name": "Rock Crabs", "reason": "Good XP, high HP, AFK-friendly", "requirements": "15 combat", "tags": ["xp", "afk"]},
                {"name": "Slayer Tasks", "reason": "Varied training, unlocks content, requires Slayer level", "requirements": "Slayer level varies", "tags": ["varied", "unlocks"]}
            ],
            "41-60": [
                {"name": "Sand Crabs", "reason": "Best mid-game XP, very AFK", "requirements": "15 combat", "tags": ["xp", "afk"]},
                {"name": "Nightmare Zone", "reason": "Best AFK training, requires quest completion", "requirements": "Dream Mentor quest", "tags": ["xp", "afk", "best"]},
                {"name": "Slayer Tasks", "reason": "Varied training, unlocks content", "requirements": "Slayer level varies", "tags": ["varied", "unlocks"]},
                {"name": "Ammonite Crabs", "reason": "Excellent XP, very AFK", "requirements": "15 combat", "tags": ["xp", "afk"]}
            ],
            "61+": [
                {"name": "Nightmare Zone", "reason": "Best AFK training method in the game", "requirements": "Dream Mentor quest", "tags": ["xp", "afk", "best"]},
                {"name": "Slayer Tasks", "reason": "Varied training, unlocks content, good money", "requirements": "Slayer level varies", "tags": ["varied", "unlocks", "money"]},
                {"name": "Sand Crabs", "reason": "Good AFK alternative to NMZ", "requirements": "15 combat", "tags": ["xp", "afk"]}
            ]
        },
        "ranged": {
            "1-20": [
                {"name": "Lumbridge Cows", "reason": "Safe, good for early ranged", "requirements": None, "tags": ["safe", "beginner"]},
                {"name": "Rock Crabs", "reason": "Best early-game ranged XP", "requirements": "15 combat", "tags": ["xp", "afk"]},
                {"name": "Sand Crabs", "reason": "Excellent ranged XP, very AFK", "requirements": "15 combat", "tags": ["xp", "afk"]}
            ],
            "21-40": [
                {"name": "Sand Crabs", "reason": "Best early-game ranged XP, very AFK", "requirements": "15 combat", "tags": ["xp", "afk"]},
                {"name": "Ammonite Crabs", "reason": "Best early-game ranged XP rates", "requirements": "15 combat", "tags": ["xp", "afk"]},
                {"name": "Slayer Tasks", "reason": "Varied training, unlocks content", "requirements": "Slayer level varies", "tags": ["varied", "unlocks"]}
            ],
            "41-60": [
                {"name": "Sand Crabs", "reason": "Best mid-game ranged XP, very AFK", "requirements": "15 combat", "tags": ["xp", "afk"]},
                {"name": "Nightmare Zone", "reason": "Best AFK ranged training", "requirements": "Dream Mentor quest", "tags": ["xp", "afk", "best"]},
                {"name": "Slayer Tasks", "reason": "Varied training, unlocks content", "requirements": "Slayer level varies", "tags": ["varied", "unlocks"]}
            ],
            "61+": [
                {"name": "Nightmare Zone", "reason": "Best AFK ranged training method", "requirements": "Dream Mentor quest", "tags": ["xp", "afk", "best"]},
                {"name": "Slayer Tasks", "reason": "Varied training, unlocks content, good money", "requirements": "Slayer level varies", "tags": ["varied", "unlocks", "money"]}
            ]
        },
        "magic": {
            "1-20": [
                {"name": "Chickens (Lumbridge)", "reason": "Very safe, good for early magic", "requirements": None, "tags": ["safe", "beginner"]},
                {"name": "Lumbridge Cows", "reason": "Safe, decent magic XP", "requirements": None, "tags": ["safe", "beginner"]},
                {"name": "Rock Crabs", "reason": "Best early-game magic XP", "requirements": "15 combat", "tags": ["xp", "afk"]}
            ],
            "21-40": [
                {"name": "Sand Crabs", "reason": "Best early-game magic XP, very AFK", "requirements": "15 combat", "tags": ["xp", "afk"]},
                {"name": "Ammonite Crabs", "reason": "Best early-game magic XP rates", "requirements": "15 combat", "tags": ["xp", "afk"]},
                {"name": "Slayer Tasks", "reason": "Varied training, unlocks content", "requirements": "Slayer level varies", "tags": ["varied", "unlocks"]}
            ],
            "41-60": [
                {"name": "Sand Crabs", "reason": "Best mid-game magic XP, very AFK", "requirements": "15 combat", "tags": ["xp", "afk"]},
                {"name": "Nightmare Zone", "reason": "Best AFK magic training", "requirements": "Dream Mentor quest", "tags": ["xp", "afk", "best"]},
                {"name": "Slayer Tasks", "reason": "Varied training, unlocks content", "requirements": "Slayer level varies", "tags": ["varied", "unlocks"]}
            ],
            "61+": [
                {"name": "Nightmare Zone", "reason": "Best AFK magic training method", "requirements": "Dream Mentor quest", "tags": ["xp", "afk", "best"]},
                {"name": "Slayer Tasks", "reason": "Varied training, unlocks content, good money", "requirements": "Slayer level varies", "tags": ["varied", "unlocks", "money"]}
            ]
        }
    }
}


def get_level_band(level: int) -> str:
    """Determine level band for spot selection"""
    if level <= 20:
        return "1-20"
    elif level <= 40:
        return "21-40"
    elif level <= 60:
        return "41-60"
    else:
        return "61+"


def get_alternate_spots(
    primary_spot: str,
    membership: str,
    style: str,
    target_level: int,
    max_alternates: int = 4
) -> List[Dict]:
    """
    Get alternate training spots for the same goal, excluding the primary spot.
    
    Args:
        primary_spot: Name of the primary recommended spot
        membership: "f2p" or "p2p"
        style: "melee", "ranged", or "magic"
        target_level: Target skill level
        max_alternates: Maximum number of alternates to return (default 4)
    
    Returns:
        List of alternate spot dictionaries with name, reason, requirements, tags
    """
    if membership not in SPOT_DATA:
        return []
    
    if style not in SPOT_DATA[membership]:
        return []
    
    level_band = get_level_band(target_level)
    spots = SPOT_DATA[membership][style].get(level_band, [])
    
    # Filter out primary spot and return alternates
    alternates = [spot for spot in spots if spot["name"] != primary_spot]
    
    # Return up to max_alternates (default 4, but ensure at least 2)
    return alternates[:max(max_alternates, 2)]

