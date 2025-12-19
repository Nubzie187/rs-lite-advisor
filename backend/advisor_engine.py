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


def get_advice(profile: Profile) -> list[AdviceItem]:
    """
    Advisor engine with quality enforcement:
    - Exactly 3 items: 1 Gear/Upgrade, 1 Training Method, 1 Quest/Unlock
    - No duplicate primary actions
    - No filler steps (all steps change account state)
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
    
    # Enforce 3 slots: Gear, Training, Quest
    items = []
    primary_actions = set()
    
    # Slot 1: Gear/Upgrade (always include)
    gear_item = get_gear_recommendation(bracket, profile.membership, combat_level, attack, strength, defence, profile.game_mode)
    if gear_item:
        primary_action = get_primary_action(gear_item)
        items.append(gear_item)
        primary_actions.add(primary_action)
    
    # Slot 2: Training Method (always include)
    training_item = get_training_recommendation(bracket, profile.membership, combat_level, attack, strength, defence)
    if training_item:
        primary_action = get_primary_action(training_item)
        # Check for duplicate with gear
        if primary_action not in primary_actions:
            items.append(training_item)
            primary_actions.add(primary_action)
        else:
            # Use alternative training spot
            if bracket and bracket.get("training_spots") and len(bracket["training_spots"]) > 1:
                spot = bracket["training_spots"][1]
                spot_name = spot.get("name", "Training spot")
                location = spot.get("location", "")
                if spot_name and location:
                    # Determine target for alternative spot
                    if combat_level < 50:
                        target_stats = "50 Attack, 50 Strength, 50 Defence"
                        target = "Reach 50 combat level"
                    elif combat_level < 70:
                        target_stats = "70 Attack, 70 Strength, 70 Defence"
                        target = "Reach 70 in all combat stats"
                    else:
                        target_stats = "85 Attack, 85 Strength, 85 Defence"
                        target = "Reach 85+ combat stats"
                    
                    alt_training = AdviceItem(
                        title=f"Train at {spot_name} until {target_stats}",
                        why_now=f"At {combat_level} combat, train at {spot_name} ({location}) to reach {target_stats} for {target}.",
                        steps=[
                            f"Travel to {location}",
                            f"Unlock access to {spot_name} (complete required quests if needed)",
                            f"Kill monsters at {spot_name} to gain combat XP until reaching {target_stats}",
                            f"Achieve target: {target}"
                        ],
                        why_over_alternatives=f"{spot_name} is an alternative training spot. Better than lower-level spots and provides good XP rates."
                    )
                    primary_action = get_primary_action(alt_training)
                    if primary_action not in primary_actions:
                        items.append(alt_training)
                        primary_actions.add(primary_action)
    
    # Slot 3: Quest/Unlock (always include)
    quest_item = get_quest_recommendation(profile, combat_level, total_level)
    if quest_item:
        primary_action = get_primary_action(quest_item)
        # Check for duplicate
        if primary_action not in primary_actions:
            items.append(quest_item)
            primary_actions.add(primary_action)
        else:
            # Use alternative quest
            if profile.membership == "f2p":
                alt_quest = AdviceItem(
                    title="Complete Lost City Quest",
                    why_now=f"Complete Lost City quest to unlock Dragon weapons and unlock prerequisite for Dragon Slayer.",
                    steps=[
                        "Train Crafting to 31+",
                        "Start quest by talking to the Shanty Pass guard",
                        "Navigate through the Lost City",
                        "Claim quest rewards and Dragon weapon unlocks"
                    ],
                    requirements=["Crafting 31+"],
                    rewards=["Dragon Dagger unlock", "Dragon Longsword unlock", "Access to Lost City"],
                    why_over_alternatives="Lost City is a prerequisite for Dragon Slayer and unlocks Dragon weapons. Better than other early quests for combat progression."
                )
            else:
                alt_quest = AdviceItem(
                    title="Complete Tree Gnome Village Quest",
                    why_now=f"Complete Tree Gnome Village quest for combat XP and Spirit Tree access.",
                    steps=[
                        "Meet requirements: 10+ Attack recommended",
                        "Start quest by talking to King Bolren in Tree Gnome Village",
                        "Complete quest objectives",
                        "Claim combat XP rewards and Spirit Tree unlock"
                    ],
                    requirements=["10+ Attack recommended"],
                    rewards=["Combat XP", "Spirit Tree transportation unlock"],
                    why_over_alternatives="Tree Gnome Village provides early combat XP and unlocks Spirit Tree transportation. Better than other early quests for utility."
                )
            primary_action = get_primary_action(alt_quest)
            if primary_action not in primary_actions:
                items.append(alt_quest)
                primary_actions.add(primary_action)
    
    # Ensure exactly 3 items
    return items[:3]

