import json
import os
from models import Profile, AdviceItem
from typing import Optional, Tuple


def load_combat_progression():
    """Load combat progression knowledge pack"""
    knowledge_path = os.path.join(os.path.dirname(__file__), "knowledge", "combat_progression.json")
    try:
        with open(knowledge_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[ADVISOR WARNING] Failed to load combat progression: {e}")
        return {"combat_brackets": []}


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
        "Purchase Barrows Gloves from Culinaromancer's Chest for 130K GP",
        "Equip Barrows Gloves for best-in-slot gloves (+12 Attack, Strength, Defence, Magic, Ranged)"
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


def get_gear_recommendation(bracket: dict, membership: str, combat_level: int, attack: int, strength: int, defence: int) -> Optional[AdviceItem]:
    """Generate gear/upgrade recommendation"""
    if not bracket:
        return None
    
    weapons = bracket.get("weapons", [])
    armor = bracket.get("armor", "Appropriate armor")
    weapons_text = " or ".join(weapons) if weapons else "Appropriate weapon"
    
    # Determine why this gear over alternatives
    if combat_level < 50:
        why_over = f"{weapons_text} and {armor} provide the best stats for your level. Upgrading from lower-tier gear significantly improves DPS and defence compared to staying with weaker equipment."
    elif combat_level < 100:
        why_over = f"{weapons_text} and {armor} are optimal for your combat level. Better than lower-tier gear for DPS, and more cost-effective than higher-tier gear you can't use yet."
    else:
        why_over = f"{weapons_text} and {armor} are best-in-slot or near best-in-slot for your level. Essential for high-level content and better than any lower-tier alternatives."
    
    steps = [
        f"Purchase {weapons_text} from Grand Exchange",
        f"Buy {armor} from Grand Exchange or shops",
        f"Equip {weapons_text} for optimal DPS",
        f"Equip {armor} for optimal defence stats"
    ]
    
    # Add quest unlock if applicable
    if combat_level < 50 and membership == "f2p":
        steps.append("Complete Dragon Slayer quest to unlock Rune Platebody")
    elif combat_level < 50 and membership == "p2p":
        steps.append("Complete Lost City quest to unlock Dragon Dagger")
    
    return AdviceItem(
        title=f"Upgrade to {weapons_text} and {armor}",
        why_now=f"At {combat_level} combat, upgrade to {weapons_text} and {armor} for better combat effectiveness.",
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
    
    steps = [
        f"Travel to {location}",
        f"Equip best available combat gear",
        f"Train at {spot_name} to gain combat XP",
        f"Level up Attack ({attack}), Strength ({strength}), and Defence ({defence})"
    ]
    
    return AdviceItem(
        title=f"Train at {spot_name}",
        why_now=f"At {combat_level} combat, train at {spot_name} ({location}) for efficient combat XP.",
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
            "Prepare combat gear and food for Elvarg"
        ][:3]
    else:
        quest = "Waterfall Quest"
        why_over = "Waterfall Quest provides 13,750 Attack and Strength XP with minimal requirements. Better than training manually for early combat levels."
        steps = [
            "Meet requirements: 30+ Attack and Strength recommended",
            "Start quest by talking to Almera in Baxtorian Falls",
            "Navigate through the waterfall dungeon",
            "Defeat Fire Giants and Moss Giants",
            "Claim 13,750 XP in Attack and Strength"
        ]
        requirements = ["30+ Attack recommended", "30+ Strength recommended"]
        rewards = ["13,750 Attack XP", "13,750 Strength XP", "Access to Baxtorian Falls"]
        next_actions = [
            "Train Attack to 30+" if profile.skills.get("attack", 1) < 30 else "Train Strength to 30+" if profile.skills.get("strength", 1) < 30 else "Start Waterfall Quest",
            "Travel to Baxtorian Falls (north of Seers' Village)",
            "Prepare combat gear"
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


def get_advice(profile: Profile) -> list[AdviceItem]:
    """
    Advisor engine with quality enforcement:
    - Exactly 3 items: 1 Gear/Upgrade, 1 Training Method, 1 Quest/Unlock
    - No duplicate primary actions
    - No filler steps
    - Comparative reasoning for each recommendation
    """
    # Load combat progression data
    progression_data = load_combat_progression()
    
    # Calculate metrics
    combat_level = calculate_combat_level(profile.skills)
    total_level = sum(profile.skills.values())
    attack = profile.skills.get("attack", 1)
    strength = profile.skills.get("strength", 1)
    defence = profile.skills.get("defence", 1)
    
    # Get combat bracket
    bracket = get_combat_bracket(combat_level, progression_data)
    
    # Generate one of each type
    gear_item = get_gear_recommendation(bracket, profile.membership, combat_level, attack, strength, defence)
    training_item = get_training_recommendation(bracket, profile.membership, combat_level, attack, strength, defence)
    quest_item = get_quest_recommendation(profile, combat_level, total_level)
    
    items = []
    primary_actions = set()
    
    # Add items in order, checking for duplicates
    for item in [gear_item, training_item, quest_item]:
        if item:
            primary_action = get_primary_action(item)
            if primary_action not in primary_actions:
                items.append(item)
                primary_actions.add(primary_action)
    
    # Ensure we have exactly 3 items
    while len(items) < 3:
        # Fallback: generate missing type
        if not gear_item or get_primary_action(gear_item) in primary_actions:
            gear_item = get_gear_recommendation(bracket, profile.membership, combat_level, attack, strength, defence)
            if gear_item and get_primary_action(gear_item) not in primary_actions:
                items.append(gear_item)
                primary_actions.add(get_primary_action(gear_item))
                continue
        
        if not training_item or get_primary_action(training_item) in primary_actions:
            training_item = get_training_recommendation(bracket, profile.membership, combat_level, attack, strength, defence)
            if training_item and get_primary_action(training_item) not in primary_actions:
                items.append(training_item)
                primary_actions.add(get_primary_action(training_item))
                continue
        
        if not quest_item or get_primary_action(quest_item) in primary_actions:
            quest_item = get_quest_recommendation(profile, combat_level, total_level)
            if quest_item and get_primary_action(quest_item) not in primary_actions:
                items.append(quest_item)
                primary_actions.add(get_primary_action(quest_item))
                continue
        
        # Last resort: add any available item
        break
    
    return items[:3]

