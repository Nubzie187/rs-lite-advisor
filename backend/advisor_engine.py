import json
import os
from models import Profile, AdviceItem, StrategyCard, BeginnerCard
from typing import Optional, Tuple, List


def load_combat_progression():
    """Load combat progression knowledge pack"""
    knowledge_path = os.path.join(os.path.dirname(__file__), "knowledge", "combat_progression.json")
    try:
        with open(knowledge_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[ADVISOR WARNING] Failed to load combat progression: {e}")
        return {"combat_brackets": []}


def load_items_metadata():
    """Load items acquisition metadata"""
    items_path = os.path.join(os.path.dirname(__file__), "data", "items_v1.json")
    try:
        with open(items_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[ADVISOR WARNING] Failed to load items metadata: {e}")
        return {"items": []}


def load_loadouts():
    """Load loadouts data"""
    loadouts_path = os.path.join(os.path.dirname(__file__), "data", "loadouts_v1.json")
    try:
        with open(loadouts_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[ADVISOR WARNING] Failed to load loadouts: {e}")
        return {"loadouts": []}


def get_loadout_for_level(loadouts_data: dict, membership: str, combat_level: int, context: str = "general_melee", tier: str = "mid") -> dict:
    """Get appropriate loadout based on combat level, membership, context, and tier"""
    loadouts = loadouts_data.get("loadouts", [])
    
    # Filter by membership and context
    matching = [l for l in loadouts if l.get("membership") == membership and l.get("context") == context]
    
    # Filter by combat level
    matching = [l for l in matching if combat_level >= l.get("min_combat", 0)]
    
    if not matching:
        return None
    
    # Prefer specified tier, fallback to closest
    tier_loadout = next((l for l in matching if l.get("tier") == tier), None)
    if tier_loadout:
        return tier_loadout
    
    # Fallback: use highest tier available
    tier_order = {"budget": 1, "mid": 2, "best": 3}
    matching.sort(key=lambda x: tier_order.get(x.get("tier", "budget"), 1))
    return matching[-1] if matching else None


def get_item_acquisition(item_name: str, items_metadata: dict, membership: str, game_mode: str = "main") -> list:
    """Get acquisition options for an item, mode-aware"""
    items = items_metadata.get("items", [])
    for item in items:
        if item.get("name", "").lower() == item_name.lower():
            # Filter by membership
            if item.get("p2p", False) and membership == "f2p":
                continue
            
            sources = item.get("sources", [])
            
            # Mode-aware filtering
            if game_mode == "main":
                # For main accounts: filter out low-probability drops as primary
                # Keep quests, shops, craft, and common drops
                # Low-probability drops (e.g., 1/32,768) should be marked as optional
                filtered_sources = []
                for source in sources:
                    source_type = source.get("type")
                    if source_type == "GE":
                        filtered_sources.append(source)
                    elif source_type == "Quest":
                        filtered_sources.append(source)
                    elif source_type == "Shop":
                        filtered_sources.append(source)
                    elif source_type == "Craft":
                        filtered_sources.append(source)
                    elif source_type == "Drop":
                        # Check if it's a common drop (not extremely rare)
                        desc = source.get("description", "").lower()
                        if "1/512" in desc or "1/128" in desc or "1/381" in desc:
                            # Common enough for main accounts
                            filtered_sources.append(source)
                        # Very rare drops (1/32k+) are excluded for main accounts
                
                # If no non-GE sources remain, use GE
                if not any(s.get("type") != "GE" for s in filtered_sources):
                    ge_sources = [s for s in sources if s.get("type") == "GE"]
                    return ge_sources
                
                # Return non-GE first, then GE
                non_ge = [s for s in filtered_sources if s.get("type") != "GE"]
                ge = [s for s in filtered_sources if s.get("type") == "GE"]
                return non_ge + ge
            else:
                # For iron accounts: prefer non-GE sources, avoid GE
                non_ge_sources = [s for s in sources if s.get("type") != "GE"]
                ge_sources = [s for s in sources if s.get("type") == "GE"]
                # Return non-GE first, GE only as last resort
                return non_ge_sources + ge_sources
    
    return []


def get_combat_bracket(combat_level: int, progression_data: dict) -> dict:
    """Get the appropriate combat bracket for a given combat level"""
    brackets = progression_data.get("combat_brackets", [])
    for bracket in brackets:
        if bracket["min_level"] <= combat_level <= bracket["max_level"]:
            return bracket
    if brackets:
        return brackets[-1]
    return None


def calculate_combat_level(skills: dict) -> int:
    """Calculate combat level using standard OSRS formula"""
    import math
    
    attack = skills.get("attack", 1)
    strength = skills.get("strength", 1)
    defence = skills.get("defence", 1)
    hitpoints = skills.get("hitpoints", 10)
    ranged = skills.get("ranged", 1)
    magic = skills.get("magic", 1)
    prayer = skills.get("prayer", 1)
    
    base = 0.25 * (defence + hitpoints + (prayer // 2))
    melee = 0.325 * (attack + strength)
    ranged_cb = 0.325 * (math.floor(ranged * 1.5) + (prayer // 2))
    magic_cb = 0.325 * (math.floor(magic * 1.5) + (prayer // 2))
    
    combat = base + max(melee, ranged_cb, magic_cb)
    return int(combat)


def get_recipe_for_disaster_advice(profile: Profile, combat_level: int, total_level: int) -> AdviceItem:
    """Generate detailed Recipe for Disaster advice"""
    cooking = profile.skills.get("cooking", 1)
    fishing = profile.skills.get("fishing", 1)
    thieving = profile.skills.get("thieving", 1)
    firemaking = profile.skills.get("firemaking", 1)
    magic = profile.skills.get("magic", 1)
    
    requirements = [
        "Cook's Assistant quest (prerequisite)",
        "Cooking 40+ (for subquests)",
        "Fishing 53+ (for Evil Dave subquest)",
        "Thieving 53+ (for Evil Dave subquest)",
        "Firemaking 50+ (for Evil Dave subquest)",
        "Magic 59+ (for Evil Dave subquest)",
        "175 Quest Points (for final subquest)"
    ]
    
    rewards = [
        "Barrows Gloves (best-in-slot gloves): +12 Attack, +12 Strength, +12 Defence, +12 Magic, +12 Ranged",
        "Barrows Gloves are best-in-slot for most combat builds (melee, magic, ranged)",
        "Required for optimal DPS in PvM, PvP, and bossing",
        "Unlocks access to Culinaromancer's Chest (130K GP to purchase gloves)",
        "Combat XP rewards from each subquest"
    ]
    
    next_actions = []
    if cooking < 40:
        next_actions.append(f"Train Cooking to 40 (currently {cooking}) - cook Lobsters at Cooking Guild")
    elif fishing < 53:
        next_actions.append(f"Train Fishing to 53 (currently {fishing}) - fish Lobsters at Catherby")
    elif thieving < 53:
        next_actions.append(f"Train Thieving to 53 (currently {thieving}) - pickpocket Master Farmers")
    elif firemaking < 50:
        next_actions.append(f"Train Firemaking to 50 (currently {firemaking}) - burn Logs at Grand Exchange")
    elif magic < 59:
        next_actions.append(f"Train Magic to 59 (currently {magic}) - cast High Alchemy")
    else:
        next_actions.append("Complete Cook's Assistant quest - talk to Cook in Lumbridge Castle")
        next_actions.append("Complete prerequisite quests: Big Chompy Bird Hunting, Fishing Contest")
        next_actions.append("Start Recipe for Disaster - talk to Culinaromancer in Lumbridge Castle basement")
    
    next_actions = next_actions[:3]
    
    if cooking < 40 or fishing < 53 or thieving < 53 or firemaking < 50 or magic < 59:
        title = "Work Towards Recipe for Disaster Requirements"
        why_now = f"With {combat_level} combat, start working towards Recipe for Disaster requirements for Barrows Gloves (best-in-slot gloves)."
    else:
        title = "Complete Recipe for Disaster for Barrows Gloves"
        why_now = f"With {combat_level} combat and required skills, complete Recipe for Disaster to unlock Barrows Gloves (best-in-slot gloves: +12 all combat stats)."
    
    steps = [
        "Complete all prerequisite quests (Cook's Assistant, Big Chompy Bird Hunting, etc.)",
        "Complete each Recipe for Disaster subquest one by one",
        "Purchase Barrows Gloves from Culinaromancer's Chest for 130K GP"
    ]
    
    return AdviceItem(
        title=title,
        why_now=why_now,
        steps=steps,
        requirements=requirements,
        rewards=rewards,
        next_actions=next_actions,
        why_over_alternatives="Recipe for Disaster unlocks best-in-slot gloves, unlike other quests that only provide temporary XP or gear unlocks. Barrows Gloves are required for optimal DPS in all combat scenarios."
    )


def get_gear_recommendation(bracket: dict, membership: str, combat_level: int, attack: int, strength: int, defence: int, game_mode: str = "main") -> Optional[AdviceItem]:
    """Generate loadout-based gear recommendation with acquisition options"""
    if not bracket:
        return None
    
    # Load data
    items_metadata = load_items_metadata()
    loadouts_data = load_loadouts()
    
    # Determine context based on combat level
    if combat_level >= 70:
        context = "nmz_melee" if membership == "p2p" else "general_melee"
    else:
        context = "general_melee"
    
    # Get appropriate loadout
    loadout = get_loadout_for_level(loadouts_data, membership, combat_level, context, tier="mid")
    if not loadout:
        return None
    
    tier = loadout.get("tier", "mid")
    context_name = loadout.get("context", "general_melee")
    
    # Build full gear list
    gear_list = []
    key_items = ["weapon", "offhand", "gloves", "cape", "ring"]  # Items that typically need acquisition
    
    for slot in ["weapon", "offhand", "helm", "body", "legs", "gloves", "boots", "cape", "amulet", "ring"]:
        item = loadout.get(slot, "None")
        if item and item != "None":
            gear_list.append(f"{slot.capitalize()}: {item}")
    
    # Build steps: start with full gear list
    steps = []
    if gear_list:
        steps.append("Loadout: " + ", ".join(gear_list))
    
    for slot in key_items:
        item = loadout.get(slot, "None")
        if not item or item == "None":
            continue
        
        req = loadout.get("requirements", {}).get(slot)
        
        # Get acquisition options
        item_sources = get_item_acquisition(item, items_metadata, membership, game_mode)
        
        if item_sources:
            # Get 2 options (prefer non-GE, then GE)
            non_ge = [s for s in item_sources if s.get("type") != "GE"][:2]
            ge_source = next((s for s in item_sources if s.get("type") == "GE"), None)
            
            options = []
            
            # Option 1: Non-GE if available
            if non_ge:
                source = non_ge[0]
                if source.get("type") == "Quest":
                    options.append(f"Complete {source.get('name')} quest")
                elif source.get("type") == "Drop":
                    options.append(f"Kill {source.get('name')} ({source.get('description', '')})")
                elif source.get("type") == "Shop":
                    options.append(f"Buy from {source.get('name')} in {source.get('location', '')}")
                elif source.get("type") == "Craft":
                    options.append(f"Craft (requires {source.get('level', '')} {source.get('skill', '')})")
            
            # Option 2: GE or second non-GE
            if ge_source and game_mode == "main":
                options.append("Buy from Grand Exchange")
            elif len(non_ge) > 1:
                source = non_ge[1]
                if source.get("type") == "Quest":
                    options.append(f"Complete {source.get('name')} quest")
                elif source.get("type") == "Drop":
                    options.append(f"Kill {source.get('name')} ({source.get('description', '')})")
                elif source.get("type") == "Shop":
                    options.append(f"Buy from {source.get('name')} in {source.get('location', '')}")
            elif ge_source and game_mode == "iron":
                options.append("Buy from Grand Exchange (last resort)")
            
            if options:
                step_text = f"{item}: {options[0]}" + (f" or {options[1]}" if len(options) > 1 else "")
                if req:
                    step_text += f" (requires: {req})"
                steps.append(step_text)
    
    # Build why_over_alternatives
    if tier == "budget":
        why_over = f"Budget {context_name} loadout provides good stats for cost. Better than lower-tier gear, more affordable than mid tier."
    elif tier == "mid":
        why_over = f"Mid-tier {context_name} loadout balances cost and effectiveness. Better than budget tier for DPS, more cost-effective than best tier."
    else:
        why_over = f"Best {context_name} loadout provides maximum stats. Better than mid-tier for DPS and defence, essential for high-level content."
    
    return AdviceItem(
        title=f"Recommended loadout: {tier} {context_name}",
        why_now=f"At {combat_level} combat, use {tier} {context_name} loadout for optimal combat effectiveness.",
        steps=steps,
        why_over_alternatives=why_over
    )


def get_training_recommendation(bracket: dict, membership: str, combat_level: int, attack: int, strength: int, defence: int) -> Optional[AdviceItem]:
    """Generate training method recommendation"""
    if not bracket:
        return None
    
    training_spots = bracket.get("training_spots", [])
    if not training_spots:
        return None
    
    # Select best training spot based on membership and combat level
    spot = None
    if membership == "p2p":
        # Prefer member spots
        for s in training_spots:
            if "members" in s.get("notes", "").lower() or "P2P" in s.get("notes", ""):
                spot = s
                break
        if not spot:
            spot = training_spots[0]
    else:
        # F2P spots only
        for s in training_spots:
            if "F2P" in s.get("notes", "").upper():
                spot = s
                break
        if not spot:
            spot = training_spots[0]
    
    spot_name = spot.get("name", "Training spot")
    location = spot.get("location", "")
    
    # Determine why this training spot over alternatives
    alternatives = []
    for s in training_spots:
        if s != spot:
            alt_name = s.get("name", "")
            if alt_name:
                alternatives.append(alt_name)
    
    if combat_level < 50:
        if spot_name in ["Sand Crabs", "Ammonite Crabs"]:
            why_over = f"{spot_name} provides better XP rates than {', '.join(alternatives[:2]) if alternatives else 'other early-game spots'} and is more AFK-friendly. Better than Al Kharid Warriors for XP/hour."
        else:
            why_over = f"{spot_name} is the best training spot for your level. Better XP rates than {', '.join(alternatives[:2]) if alternatives else 'alternatives'} and safe for low-level players."
    elif combat_level < 100:
        if spot_name == "Nightmare Zone":
            why_over = f"Nightmare Zone is the best AFK training method. Better XP rates than Slayer tasks and more AFK than {', '.join(alternatives[:2]) if alternatives else 'other training methods'}."
        elif "Slayer" in spot_name:
            why_over = f"Slayer training provides variety and profit. Better long-term value than pure combat training at {', '.join(alternatives[:2]) if alternatives else 'other spots'}."
        else:
            why_over = f"{spot_name} provides efficient XP for your level. Better than {', '.join(alternatives[:2]) if alternatives else 'lower-level spots'} and more accessible than high-level methods."
    else:
        if spot_name == "Nightmare Zone":
            why_over = f"Nightmare Zone with Dharok's is the best AFK combat training. Better XP/hour than Slayer and more AFK than {', '.join(alternatives[:2]) if alternatives else 'other methods'}."
        elif "Slayer" in spot_name:
            why_over = f"High-level Slayer tasks are profitable and provide good XP. Better money than Nightmare Zone and unlocks unique content compared to {', '.join(alternatives[:2]) if alternatives else 'pure combat training'}."
        else:
            why_over = f"{spot_name} is optimal for your combat level. Better than {', '.join(alternatives[:2]) if alternatives else 'lower-level methods'}."
    
    # Determine target stats based on current levels and combat level
    current_attack = attack
    current_strength = strength
    current_defence = defence
    
    # Calculate target stats (next milestone)
    if combat_level < 50:
        target_attack = max(50, current_attack + 10)
        target_strength = max(50, current_strength + 10)
        target_defence = max(50, current_defence + 10)
        target = "Reach 50 combat level (unlocks better training spots and gear)"
    elif combat_level < 70:
        target_attack = max(70, current_attack + 10)
        target_strength = max(70, current_strength + 10)
        target_defence = max(70, current_defence + 10)
        target = "Reach 70 in all combat stats (unlocks Barrows equipment and better training)"
    elif combat_level < 100:
        target_attack = max(85, current_attack + 10)
        target_strength = max(85, current_strength + 10)
        target_defence = max(85, current_defence + 10)
        target = "Reach 85+ combat stats (unlocks high-level Slayer tasks and bossing)"
    else:
        target_attack = max(99, current_attack + 5)
        target_strength = max(99, current_strength + 5)
        target_defence = max(99, current_defence + 5)
        target = "Reach 99 in combat stats (max combat level)"
    
    target_stats = f"{target_attack}/{target_strength}/{target_defence}"
    
    # Determine recommended food based on combat level
    if combat_level < 50:
        recommended_food = "Lobsters"
    elif combat_level < 70:
        recommended_food = "Swordfish"
    else:
        recommended_food = "Sharks"
    
    # Build steps (no filler, actionable only)
    steps = []
    
    # Check if access is needed
    if "Nightmare Zone" in spot_name:
        steps.append("Complete Dream Mentor quest (required for Nightmare Zone)")
        steps.append("Unlock Nightmare Zone by talking to Dominic Onion in Yanille")
    elif "Slayer" in spot_name:
        steps.append(f"Get Slayer task from Slayer Master (requires appropriate Slayer level)")
    
    steps.append(f"Travel to {location}")
    steps.append(f"Train at {spot_name} until reaching {target_stats} (Attack/Strength/Defence)")
    steps.append(f"Target: {target}")
    steps.append(f"Bring food: {recommended_food} (click for details on how to obtain)")
    
    return AdviceItem(
        title=f"Train at {spot_name} until {target_stats}",
        why_now=f"At {combat_level} combat with {current_attack}/{current_strength}/{current_defence}, train at {spot_name} ({location}) to reach {target_stats} for {target}.",
        steps=steps,
        why_over_alternatives=why_over
    )


def get_quest_recommendation(profile: Profile, combat_level: int, total_level: int) -> AdviceItem:
    """Generate quest/unlock recommendation"""
    if profile.membership == "p2p" and total_level >= 500:
        return get_recipe_for_disaster_advice(profile, combat_level, total_level)
    
    if profile.membership == "f2p":
        quest = "Dragon Slayer"
        why_over = "Dragon Slayer unlocks Rune Platebody (best F2P body armor) and provides significant combat XP. Better than other F2P quests for combat progression."
        steps = [
            "Complete Lost City quest (prerequisite)",
            "Complete Merlin's Crystal quest (prerequisite)",
            "Train Magic to 33+ for Fire Blast spell",
            "Defeat Elvarg the Dragon in Karamja volcano",
            "Claim Rune Platebody unlock and 18,650 XP in Attack, Strength, Defence, Hitpoints"
        ]
        requirements = ["Lost City quest", "Merlin's Crystal quest", "Magic 33+"]
        rewards = ["Rune Platebody unlock", "18,650 XP in Attack, Strength, Defence, Hitpoints"]
        next_actions = [
            "Complete Lost City quest" if profile.skills.get("crafting", 1) < 31 else "Complete Merlin's Crystal quest",
            "Train Magic to 33+" if profile.skills.get("magic", 1) < 33 else "Start Dragon Slayer quest",
            "Travel to Karamja volcano to fight Elvarg"
        ][:3]
    else:
        quest = "Waterfall Quest"
        why_over = "Waterfall Quest provides 13,750 Attack and Strength XP with minimal requirements. Better than training manually for early combat levels."
        steps = [
            "Train Attack to 30+ (if not already)",
            "Train Strength to 30+ (if not already)",
            "Start quest by talking to Almera in Baxtorian Falls",
            "Navigate through the waterfall dungeon and defeat Fire Giants and Moss Giants",
            "Claim 13,750 XP in Attack and Strength"
        ]
        requirements = ["30+ Attack recommended", "30+ Strength recommended"]
        rewards = ["13,750 Attack XP", "13,750 Strength XP", "Access to Baxtorian Falls"]
        next_actions = [
            "Train Attack to 30+" if profile.skills.get("attack", 1) < 30 else "Train Strength to 30+" if profile.skills.get("strength", 1) < 30 else "Start Waterfall Quest",
            "Travel to Baxtorian Falls (north of Seers' Village)",
            "Complete Waterfall Quest objectives"
        ][:3]
    
    return AdviceItem(
        title=f"Complete {quest}",
        why_now=f"With {combat_level} combat, complete {quest} for combat XP and gear unlocks.",
        steps=steps,
        requirements=requirements,
        rewards=rewards,
        next_actions=next_actions,
        why_over_alternatives=why_over
    )


def get_primary_action(item: AdviceItem) -> str:
    """Extract primary action from advice item for de-duplication"""
    title_lower = item.title.lower()
    
    # Check for training location
    if "train at" in title_lower:
        # Extract location name
        for word in title_lower.split():
            if word in ["sand", "ammonite", "nightmare", "slayer", "al", "kharid", "lumbridge"]:
                return f"train_{word}"
        return "train_location"
    
    # Check for quest
    if "complete" in title_lower and "quest" in title_lower:
        if "recipe" in title_lower or "disaster" in title_lower:
            return "quest_rfd"
        elif "dragon" in title_lower or "slayer" in title_lower:
            return "quest_dragon_slayer"
        elif "waterfall" in title_lower:
            return "quest_waterfall"
        return "quest"
    
    # Check for gear upgrade
    if "upgrade" in title_lower or "equip" in title_lower:
        # Extract gear type
        for word in ["rune", "dragon", "barrows", "whip", "scimitar"]:
            if word in title_lower:
                return f"gear_{word}"
        return "gear_upgrade"
    
    return "unknown"


def is_beginner_player(combat_level: int, total_level: int) -> bool:
    """Detect if player is a beginner (combat <= 10 OR total level <= 100)"""
    return combat_level <= 10 or total_level <= 100


def get_barrows_gloves_strategy(profile: Profile, combat_level: int) -> StrategyCard:
    """Generate strategy card for preparing for Barrows Gloves"""
    cooking = profile.skills.get("cooking", 1)
    fishing = profile.skills.get("fishing", 1)
    thieving = profile.skills.get("thieving", 1)
    firemaking = profile.skills.get("firemaking", 1)
    magic = profile.skills.get("magic", 1)
    
    why = "Barrows Gloves are best-in-slot gloves for most combat builds. They provide +12 to all combat stats (Attack, Strength, Defence, Ranged, Magic) and are required for optimal DPS in PvM, PvP, and bossing. Unlocking them early sets up your account for efficient progression."
    
    unlocks = [
        "Barrows Gloves (+12 all combat stats)",
        "Access to Culinaromancer's Chest (130K GP to purchase gloves)",
        "Best-in-slot gloves for melee, magic, and ranged builds",
        "Required for optimal DPS in all combat scenarios",
        "Combat XP rewards from each Recipe for Disaster subquest"
    ]
    
    next_actions = []
    if cooking < 40:
        next_actions.append(f"Train Cooking to 40 (currently {cooking})")
    if fishing < 53:
        next_actions.append(f"Train Fishing to 53 (currently {fishing})")
    if thieving < 53:
        next_actions.append(f"Train Thieving to 53 (currently {thieving})")
    if firemaking < 50:
        next_actions.append(f"Train Firemaking to 50 (currently {firemaking})")
    if magic < 59:
        next_actions.append(f"Train Magic to 59 (currently {magic})")
    if len(next_actions) == 0:
        next_actions.append("Complete prerequisite quests (Cook's Assistant, Big Chompy Bird Hunting, Fishing Contest)")
        next_actions.append("Start Recipe for Disaster quest line")
    
    return StrategyCard(
        title="Prepare for Barrows Gloves",
        why=why,
        unlocks=unlocks,
        next_actions=next_actions[:3],
        unlock_path_context="barrows_gloves",
        build_context="general_melee"
    )


def get_mid_game_combat_training_strategy(profile: Profile, combat_level: int) -> StrategyCard:
    """Generate strategy card for efficient mid-game combat training"""
    attack = profile.skills.get("attack", 1)
    strength = profile.skills.get("strength", 1)
    defence = profile.skills.get("defence", 1)
    
    why = "Mid-game combat training (70-85 stats) unlocks access to Barrows equipment, high-level Slayer tasks, and efficient bossing. Reaching 70+ in all combat stats opens up significantly better training methods and gear options, making future progression much faster."
    
    unlocks = [
        "Access to Barrows equipment (best mid-game armor)",
        "Unlock high-level Slayer tasks (profitable and efficient)",
        "Access to better training spots (NMZ, Slayer, bossing)",
        "Ability to use Abyssal Whip and Dragon equipment",
        "Foundation for reaching 85+ stats (high-level content)"
    ]
    
    next_actions = []
    if attack < 70:
        next_actions.append(f"Reach 70 Attack (currently {attack})")
    if strength < 70:
        next_actions.append(f"Reach 70 Strength (currently {strength})")
    if defence < 70:
        next_actions.append(f"Reach 70 Defence (currently {defence})")
    if len(next_actions) == 0:
        next_actions.append("Aim for 85+ in all combat stats")
        next_actions.append("Unlock Barrows equipment")
    
    return StrategyCard(
        title="Efficient Combat Training Path (Mid-game)",
        why=why,
        unlocks=unlocks,
        next_actions=next_actions[:3],
        unlock_path_context="mid_game_combat",
        build_context="general_melee"
    )


def get_nmz_efficiency_strategy(profile: Profile, combat_level: int) -> StrategyCard:
    """Generate strategy card for unlocking Nightmare Zone efficiency"""
    attack = profile.skills.get("attack", 1)
    strength = profile.skills.get("strength", 1)
    defence = profile.skills.get("defence", 1)
    magic = profile.skills.get("magic", 1)
    
    why = "Nightmare Zone (NMZ) is the most AFK and efficient combat training method in the game. Unlocking NMZ efficiency requires completing Dream Mentor quest and setting up proper gear. This enables hours of AFK training with excellent XP rates, making it essential for reaching high combat levels."
    
    unlocks = [
        "Access to Nightmare Zone (best AFK combat training)",
        "Ability to use Dharok's set for maximum XP rates",
        "Access to NMZ rewards (imbued rings, herb boxes)",
        "Efficient path to 99 combat stats",
        "Foundation for high-level PvM and bossing"
    ]
    
    next_actions = []
    if combat_level < 70:
        next_actions.append(f"Reach 70+ combat level (currently {combat_level})")
    if attack < 70 or strength < 70 or defence < 70:
        next_actions.append("Reach 70+ in Attack, Strength, and Defence")
    if magic < 50:
        next_actions.append(f"Train Magic to 50+ (currently {magic}) for Dream Mentor quest")
    if len(next_actions) == 0:
        next_actions.append("Complete Dream Mentor quest")
        next_actions.append("Obtain Dharok's set or best available melee gear")
    
    return StrategyCard(
        title="Unlock Nightmare Zone Efficiency",
        why=why,
        unlocks=unlocks,
        next_actions=next_actions[:3],
        unlock_path_context="nmz_setup",
        build_context="nmz_melee"
    )


def get_strategies(profile: Profile) -> List[StrategyCard]:
    """Generate strategy cards based on player profile"""
    combat_level = calculate_combat_level(profile.skills)
    total_level = sum(profile.skills.values())
    
    # Check if beginner - return empty (beginners use beginner advice)
    if is_beginner_player(combat_level, total_level):
        return []
    
    strategies = []
    
    # Strategy 1: Barrows Gloves (if not already obtained and combat >= 50)
    cooking = profile.skills.get("cooking", 1)
    fishing = profile.skills.get("fishing", 1)
    thieving = profile.skills.get("thieving", 1)
    firemaking = profile.skills.get("firemaking", 1)
    magic = profile.skills.get("magic", 1)
    
    # Check if player needs Barrows Gloves (if any requirement is not met)
    needs_barrows_gloves = (
        combat_level >= 50 and 
        (cooking < 40 or fishing < 53 or thieving < 53 or firemaking < 50 or magic < 59)
    )
    
    if needs_barrows_gloves:
        strategies.append(get_barrows_gloves_strategy(profile, combat_level))
    
    # Strategy 2: Mid-game Combat Training (if combat 50-100)
    attack = profile.skills.get("attack", 1)
    strength = profile.skills.get("strength", 1)
    defence = profile.skills.get("defence", 1)
    
    needs_mid_game_training = (
        50 <= combat_level < 100 and
        (attack < 85 or strength < 85 or defence < 85)
    )
    
    if needs_mid_game_training:
        strategies.append(get_mid_game_combat_training_strategy(profile, combat_level))
    
    # Strategy 3: NMZ Efficiency (if combat >= 70 and P2P)
    if profile.membership == "p2p" and combat_level >= 70:
        strategies.append(get_nmz_efficiency_strategy(profile, combat_level))
    
    # Ensure at least one strategy is returned
    if len(strategies) == 0:
        # Fallback: return mid-game training if no specific strategy matches
        if combat_level >= 50:
            strategies.append(get_mid_game_combat_training_strategy(profile, combat_level))
    
    return strategies[:3]  # Return up to 3 strategies


def get_beginner_cards(profile: Profile, combat_level: int) -> List[BeginnerCard]:
    """Generate beginner power path cards in linear sequence"""
    membership = profile.membership
    attack = profile.skills.get("attack", 1)
    strength = profile.skills.get("strength", 1)
    defence = profile.skills.get("defence", 1)
    
    cards = []
    
    # Card 1: Primary Unlock - First combat power spike (quest-based XP)
    if membership == "f2p":
        cards.append(BeginnerCard(
            title="Complete Cook's Assistant",
            why_now="Unlocks early Cooking XP and is a prerequisite for Recipe for Disaster later. Fastest completion time with no combat required.",
            action="Talk to the Cook in Lumbridge Castle kitchen and complete the quest by collecting ingredients.",
            next_unlock="300 Cooking XP, access to cooking, prerequisite for Recipe for Disaster",
            optional=False,
            details="Location: Lumbridge Castle kitchen. Ingredients needed: Bucket of milk (from cow field), Egg (from chicken coop), Flour (use wheat on windmill). Alternative: You can skip this if you plan to train Cooking manually, but it's required for later content."
        ))
    else:
        cards.append(BeginnerCard(
            title="Complete Waterfall Quest",
            why_now="Unlocks first combat power spike: 13,750 Attack and Strength XP (brings you to ~30/30). Better than hours of manual training.",
            action="Talk to Almera in Barbarian Village to start the quest. Requires 30 Agility or 30 Strength (train at Draynor agility course if needed).",
            next_unlock="13,750 Attack XP, 13,750 Strength XP, access to Waterfall Dungeon",
            optional=False,
            details="Location: Barbarian Village. Requirements: 30 Agility OR 30 Strength. If you don't have these, train at Draynor Village agility course or Al Kharid Warriors first. Alternative: You can skip this quest and train manually, but it will take much longer to reach level 30."
        ))
    
    # Card 2: Required Follow-up - Equip gear AFTER quest XP
    if membership == "p2p":
        cards.append(BeginnerCard(
            title="Equip Iron Gear",
            why_now="After Waterfall Quest XP brings you to level 30, Iron gear enables effective early training. Better stats than Bronze for minimal cost.",
            action="Purchase Iron equipment from shops: Scimitar from Zeke's in Al Kharid (224 GP), armor from Horvik's in Varrock (~528 GP total).",
            next_unlock="Iron Scimitar, Iron Full Helm, Iron Chainbody, Iron Platelegs (enables efficient training loop)",
            optional=False,
            details="Locations: Zeke's Scimitar Shop in Al Kharid, Horvik's Armour Shop in Varrock. Total cost: ~750 GP. Alternative: You can use Bronze gear, but Iron provides significantly better stats for minimal cost increase."
        ))
    else:
        cards.append(BeginnerCard(
            title="Equip Iron Gear",
            why_now="Iron gear is the best F2P starter equipment. Enables safe early training with minimal cost investment.",
            action="Purchase Iron equipment from shops: Scimitar from Zeke's in Al Kharid (224 GP), armor from Horvik's in Varrock (~528 GP total).",
            next_unlock="Iron Scimitar, Iron Full Helm, Iron Chainbody, Iron Platelegs (enables efficient training loop)",
            optional=False,
            details="Locations: Zeke's Scimitar Shop in Al Kharid, Horvik's Armour Shop in Varrock. Total cost: ~750 GP. Alternative: You can use Bronze gear, but Iron provides significantly better stats for minimal cost increase."
        ))
    
    # Card 3: Primary Unlock - Mobility power spike (P2P only)
    if membership == "p2p":
        cards.append(BeginnerCard(
            title="Complete Tree Gnome Village",
            why_now="Unlocks first mobility power spike: Spirit Tree network access. Enables efficient travel for future quests and training.",
            action="Talk to King Bolren in Tree Gnome Village to start the quest. Requires 10+ Attack recommended.",
            next_unlock="Spirit Tree network access, combat XP rewards, efficient transportation",
            optional=False,
            details="Location: Tree Gnome Village (west of Ardougne). Requirements: 10+ Attack recommended. Alternative: You can skip this and walk everywhere, but Spirit Trees save significant time for future questing."
        ))
    
    # Card 4: Optional stat balancing (only if uneven)
    needs_training = False
    if membership == "p2p":
        if attack < 25 or strength < 25:
            needs_training = True
            cards.append(BeginnerCard(
                title="Balance Combat Stats",
                why_now="If you skipped Waterfall Quest or your stats are uneven, training balances them for efficient progression.",
                action="Train at Lumbridge Cows (north of Lumbridge) until reaching balanced stats (15/15/15 minimum).",
                next_unlock="Balanced combat stats (15/15/15 minimum), profitable cowhide drops",
                optional=True,
                details="Location: Lumbridge cow field (north of Lumbridge). Target: 15 Attack, 15 Strength, 15 Defence minimum. Alternative: If you completed Waterfall Quest and stats are balanced, you can skip this step entirely."
            ))
    else:
        if attack < 15 or strength < 15 or defence < 15:
            needs_training = True
            cards.append(BeginnerCard(
                title="Balance Combat Stats",
                why_now="If your combat stats are below 15/15/15, training balances them for efficient progression.",
                action="Train at Al Kharid Warriors (Al Kharid Palace, ground floor) until reaching balanced stats (20/20/20).",
                next_unlock="Balanced combat stats (20/20/20), safe training location",
                optional=True,
                details="Location: Al Kharid Palace (ground floor). Target: 20 Attack, 20 Strength, 20 Defence. Alternative: If your stats are already balanced, you can skip this step entirely."
            ))
    
    return cards


def get_beginner_advice(profile: Profile, combat_level: int) -> list[AdviceItem]:
    """Legacy function - kept for backward compatibility, but beginners should use get_beginner_cards()"""
    # Return empty list - beginners should use card-based flow
    return []


def get_advice(profile: Profile) -> list[AdviceItem]:
    """
    Get advice for beginners only (returns AdviceItem list).
    For non-beginners, use get_strategies() instead which returns Strategy Cards.
    """
    # Calculate metrics
    combat_level = calculate_combat_level(profile.skills)
    total_level = sum(profile.skills.values())
    
    # Check if beginner - return beginner path
    if is_beginner_player(combat_level, total_level):
        return get_beginner_advice(profile, combat_level)
    
    # Non-beginners should use strategies, not advice items
    return []

