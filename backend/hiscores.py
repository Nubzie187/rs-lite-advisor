import httpx
from typing import Dict, Optional, Tuple
from urllib.parse import quote


# OSRS skill names in hiscores order
SKILL_NAMES = [
    "overall", "attack", "defence", "strength", "hitpoints",
    "ranged", "prayer", "magic", "cooking", "woodcutting",
    "fletching", "fishing", "firemaking", "crafting", "smithing",
    "mining", "herblore", "agility", "thieving", "slayer",
    "farming", "runecraft", "hunter", "construction"
]


def fetch_hiscores(player_name: str) -> Tuple[Optional[Dict[str, int]], Optional[str]]:
    """
    Fetch OSRS hiscores for a player and return skills as a dict.
    Returns (skills_dict, error_message) tuple.
    If successful, returns (skills_dict, None).
    If error, returns (None, error_message).
    """
    if not player_name or not player_name.strip():
        return None, "Player name is required"
    
    # URL-encode the player name
    encoded_name = quote(player_name.strip())
    url = f"https://secure.runescape.com/m=hiscore_oldschool/index_lite.ws?player={encoded_name}"
    
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url)
            response.raise_for_status()
            
            # Get raw response as plain text (NOT JSON)
            raw_content = response.text
            print(f"[HISCORES DEBUG] Raw response for player '{player_name}': {raw_content[:500]}...")  # Log first 500 chars
            
            content = raw_content.strip()
            
            # Check if response is empty or starts with "404"
            if not content:
                return None, "Player not found on OSRS hiscores"
            
            if content.startswith("404"):
                return None, "Player not found on OSRS hiscores"
            
            # Parse plain text response - split by newline
            lines = content.split('\n')
            if len(lines) < 2:  # Need at least overall + one skill
                return None, "Invalid hiscores response format"
            
            skills = {}
            
            # OSRS hiscores order: Overall (line 0), Attack (line 1), Defence (line 2), Strength (line 3), etc.
            # Skip overall (index 0), map remaining lines to skills
            # Each line format: rank,level,xp
            for i, skill_name in enumerate(SKILL_NAMES[1:], start=1):
                if i < len(lines):
                    line = lines[i].strip()
                    if line:
                        # Parse line: rank,level,xp
                        parts = line.split(',')
                        if len(parts) >= 2:
                            try:
                                # Extract level (second field, index 1)
                                level = int(parts[1].strip())
                                skills[skill_name] = level
                            except (ValueError, IndexError) as e:
                                print(f"[HISCORES WARNING] Failed to parse level for {skill_name} from line '{line}': {e}")
                                skills[skill_name] = 1
            
            if not skills:
                return None, "No skills data found in hiscores response"
            
            print(f"[HISCORES DEBUG] Successfully parsed {len(skills)} skills")
            return skills, None
            
    except (httpx.HTTPError, httpx.TimeoutException) as e:
        error_msg = f"Error fetching hiscores: {str(e)}"
        print(f"[HISCORES ERROR] {error_msg}")
        return None, error_msg
    except ValueError as e:
        error_msg = f"Error parsing hiscores data: {str(e)}"
        print(f"[HISCORES ERROR] {error_msg}")
        return None, error_msg

