import json
import os
from models import Profile, AdviceItem


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
    # Default to highest bracket if level exceeds all
    if brackets:
        return brackets[-1]
    return None


def get_fallback_gear_upgrade(bracket: dict, membership: str) -> AdviceItem:
    """Fallback: Gear upgrade suggestion based on combat bracket"""
    if not bracket:
        return None
    
    weapons = bracket.get("weapons", [])
    armor = bracket.get("armor", "Appropriate armor")
    weapons_text = " or ".join(weapons) if weapons else "Appropriate weapon"
    
    return AdviceItem(
        title=f"Upgrade Your Equipment",
        why_now=f"Upgrade to {weapons_text} and {armor} for better combat effectiveness.",
        steps=[
            f"Purchase {weapons_text} from Grand Exchange or shops",
            f"Equip {armor} for optimal defence stats",
            f"Buy {weapons_text.split(' or ')[0]} if you can't afford both weapons",
            "Complete Dragon Slayer quest to unlock Rune Platebody (F2P)",
            "Complete Lost City quest to unlock Dragon Dagger (members)" if membership == "p2p" else "Train at Al Kharid Warriors to earn GP for upgrades"
        ]
    )


def get_fallback_training_spot(bracket: dict, membership: str) -> AdviceItem:
    """Fallback: Training spot suggestion based on bracket"""
    if not bracket:
        return None
    
    training_spots = bracket.get("training_spots", [])
    if not training_spots:
        return None
    
    spot = training_spots[0]
    spot_name = spot.get("name", "Training spot")
    location = spot.get("location", "")
    
    return AdviceItem(
        title=f"Train at {spot_name}",
        why_now=f"Train at {spot_name} ({location}) for efficient combat XP.",
        steps=[
            f"Travel to {location}",
            f"Kill {spot_name} repeatedly for combat XP",
            f"Bank at nearest bank when inventory is full",
            "Bring food (Lobsters or better) for healing",
            f"Use {spot.get('notes', '')}" if spot.get('notes') else "Repeat until desired combat level"
        ]
    )


def get_recipe_for_disaster_advice(profile: Profile, combat_level: int, total_level: int) -> AdviceItem:
    """Generate detailed Recipe for Disaster advice with requirements, rewards, and next actions"""
    cooking = profile.skills.get("cooking", 1)
    fishing = profile.skills.get("fishing", 1)
    agility = profile.skills.get("agility", 1)
    thieving = profile.skills.get("thieving", 1)
    firemaking = profile.skills.get("firemaking", 1)
    magic = profile.skills.get("magic", 1)
    
    # Core requirements
    requirements = [
        "Cook's Assistant quest (prerequisite)",
        "Cooking 40+ (for subquests)",
        "Fishing 53+ (for Evil Dave subquest)",
        "Agility 25+ (for Pirate Pete subquest)",
        "Thieving 53+ (for Evil Dave subquest)",
        "Firemaking 50+ (for Evil Dave subquest)",
        "Magic 59+ (for Evil Dave subquest)",
        "175 Quest Points (for final subquest)"
    ]
    
    # Rewards breakdown
    rewards = [
        "Barrows Gloves (best-in-slot gloves): +12 Attack, +12 Strength, +12 Defence, +12 Magic, +12 Ranged",
        "Barrows Gloves are best-in-slot for most combat builds (melee, magic, ranged)",
        "Required for optimal DPS in PvM, PvP, and bossing",
        "Unlocks access to Culinaromancer's Chest (130K GP to purchase gloves)",
        "Combat XP rewards from each subquest",
        "Access to Culinaromancer's Chest for other gloves (upgrade path)"
    ]
    
    # Determine which subquests to focus on based on current stats
    next_actions = []
    
    # Check prerequisites
    if cooking < 40:
        next_actions.append(f"Train Cooking to 40 (currently {cooking}) - cook Lobsters at Cooking Guild or use Cooking Gauntlets")
    elif fishing < 53:
        next_actions.append(f"Train Fishing to 53 (currently {fishing}) - fish Lobsters at Catherby or Karamja")
    elif thieving < 53:
        next_actions.append(f"Train Thieving to 53 (currently {thieving}) - pickpocket Master Farmers or train at Pyramid Plunder")
    elif firemaking < 50:
        next_actions.append(f"Train Firemaking to 50 (currently {firemaking}) - burn Logs at Grand Exchange or use Wintertodt")
    elif magic < 59:
        next_actions.append(f"Train Magic to 59 (currently {magic}) - cast High Alchemy or train at Magic Training Arena")
    elif agility < 25:
        next_actions.append(f"Train Agility to 25 (currently {agility}) - complete Agility courses at Gnome Stronghold or Draynor")
    else:
        # All skill requirements met, focus on quest prerequisites
        next_actions.append("Complete Cook's Assistant quest (if not done) - talk to Cook in Lumbridge Castle")
        next_actions.append("Complete prerequisite quests: Big Chompy Bird Hunting, Fishing Contest, Goblin Diplomacy")
        next_actions.append("Start Recipe for Disaster by talking to the Culinaromancer in Lumbridge Castle basement")
    
    # Limit to 3 most relevant next actions
    next_actions = next_actions[:3]
    
    # Determine progress status
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
        "Equip Barrows Gloves for best-in-slot gloves (+12 Attack, Strength, Defence, Magic, Ranged)",
        "Use Barrows Gloves for optimal DPS in all combat scenarios"
    ]
    
    return AdviceItem(
        title=title,
        why_now=why_now,
        steps=steps,
        requirements=requirements,
        rewards=rewards,
        next_actions=next_actions
    )


def get_fallback_quest(bracket: dict, membership: str, combat_level: int) -> AdviceItem:
    """Fallback: Quest unlock suggestion based on bracket"""
    if combat_level < 30:
        if membership == "f2p":
            return AdviceItem(
                title="Complete Dragon Slayer",
                why_now=f"Complete Dragon Slayer to unlock Rune Platebody and combat XP.",
                steps=[
                    "Complete Lost City and Merlin's Crystal quests (prerequisites)",
                    "Train Magic to 33+ for Fire Blast spell",
                    "Defeat Elvarg the Dragon in Karamja volcano",
                    "Claim Rune Platebody unlock and combat XP",
                    "Equip Rune Platebody"
                ],
                requirements=["Lost City quest", "Merlin's Crystal quest", "Magic 33+"],
                rewards=["Rune Platebody unlock", "18,650 XP in Attack, Strength, Defence, Hitpoints"],
                next_actions=["Complete Lost City quest", "Complete Merlin's Crystal quest", "Train Magic to 33+"]
            )
        else:
            return AdviceItem(
                title="Complete Waterfall Quest",
                why_now=f"Complete Waterfall Quest for 13,750 Attack and Strength XP.",
                steps=[
                    "Meet requirements: 30+ Attack and Strength recommended",
                    "Start quest by talking to Almera in Baxtorian Falls",
                    "Navigate through the waterfall dungeon",
                    "Defeat Fire Giants and Moss Giants",
                    "Claim 13,750 XP in Attack and Strength"
                ],
                requirements=["30+ Attack recommended", "30+ Strength recommended"],
                rewards=["13,750 Attack XP", "13,750 Strength XP", "Access to Baxtorian Falls"],
                next_actions=["Train Attack to 30+", "Train Strength to 30+", "Travel to Baxtorian Falls"]
            )
    elif combat_level < 70:
        if membership == "p2p":
            # Return a simplified Recipe for Disaster recommendation
            return AdviceItem(
                title="Work Towards Recipe for Disaster",
                why_now=f"At {combat_level} combat, work towards Recipe for Disaster for Barrows Gloves (best-in-slot gloves).",
                steps=[
                    "Complete Cook's Assistant quest (prerequisite)",
                    "Train Cooking to 40+, Fishing to 53+, Thieving to 53+",
                    "Complete Recipe for Disaster subquests one by one",
                    "Purchase Barrows Gloves from Culinaromancer's Chest (130K GP)",
                    "Equip Barrows Gloves for +12 all combat stats"
                ],
                requirements=["Cook's Assistant quest", "Cooking 40+", "Fishing 53+", "Thieving 53+", "Firemaking 50+", "Magic 59+", "175 Quest Points"],
                rewards=["Barrows Gloves (+12 Attack, Strength, Defence, Magic, Ranged)", "Best-in-slot gloves for most builds", "Combat XP from subquests"],
                next_actions=["Complete Cook's Assistant quest", "Train Cooking to 40+", "Train Fishing to 53+"]
            )
        else:
            return AdviceItem(
                title="Complete Dragon Slayer",
                why_now=f"Complete Dragon Slayer to unlock Rune Platebody.",
                steps=[
                    "Complete Lost City and Merlin's Crystal quests",
                    "Train Magic to 33+",
                    "Defeat Elvarg the Dragon",
                    "Claim Rune Platebody unlock",
                    "Equip Rune Platebody"
                ],
                requirements=["Lost City quest", "Merlin's Crystal quest", "Magic 33+"],
                rewards=["Rune Platebody unlock", "18,650 XP in Attack, Strength, Defence, Hitpoints"],
                next_actions=["Complete Lost City quest", "Complete Merlin's Crystal quest", "Train Magic to 33+"]
            )
    else:
        if membership == "p2p":
            # Return a simplified Recipe for Disaster recommendation
            return AdviceItem(
                title="Complete Recipe for Disaster",
                why_now=f"With {combat_level} combat, complete Recipe for Disaster for Barrows Gloves (best-in-slot gloves).",
                steps=[
                    "Complete all prerequisite quests (Cook's Assistant, etc.)",
                    "Complete all Recipe for Disaster subquests",
                    "Purchase Barrows Gloves from Culinaromancer's Chest (130K GP)",
                    "Equip Barrows Gloves for +12 all combat stats",
                    "Use Barrows Gloves for optimal DPS in all combat"
                ],
                requirements=["Cook's Assistant quest", "Cooking 40+", "Fishing 53+", "Thieving 53+", "Firemaking 50+", "Magic 59+", "175 Quest Points"],
                rewards=["Barrows Gloves (+12 Attack, Strength, Defence, Magic, Ranged)", "Best-in-slot gloves for PvM, PvP, and bossing", "Required for optimal DPS"],
                next_actions=["Complete prerequisite quests", "Complete Recipe for Disaster subquests", "Purchase Barrows Gloves (130K GP)"]
            )
        else:
            return AdviceItem(
                title="Complete Dragon Slayer",
                why_now=f"Complete Dragon Slayer for end-game F2P gear.",
                steps=[
                    "Complete all prerequisite quests",
                    "Train Magic to 33+",
                    "Defeat Elvarg the Dragon",
                    "Claim Rune Platebody unlock",
                    "Equip Rune Platebody"
                ],
                requirements=["Lost City quest", "Merlin's Crystal quest", "Magic 33+"],
                rewards=["Rune Platebody unlock", "18,650 XP in Attack, Strength, Defence, Hitpoints"],
                next_actions=["Complete Lost City quest", "Complete Merlin's Crystal quest", "Train Magic to 33+"]
            )


def get_advice(profile: Profile) -> list[AdviceItem]:
    """
    Rule-based advisor engine with hard rules:
    - Each item must include concrete location, quest, or item
    - Steps must be actionable and game-specific
    - No generic self-help language
    Returns exactly 3 advice items based on profile.
    """
    items = []
    
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
    
    # Rule 1: Membership-based (only for F2P) - must include concrete quest/item
    if profile.membership == "f2p":
        items.append(AdviceItem(
            title="Complete F2P Quests Before Membership",
            why_now=f"With {combat_level} combat, complete all F2P quests to maximize membership value.",
            steps=[
                "Complete Dragon Slayer quest (unlocks Rune Platebody)",
                "Complete all F2P quests (Druidic Ritual, Lost City, etc.)",
                "Save 3-5M GP at Grand Exchange for membership expenses",
                "Complete Cook's Assistant quest (prerequisite for Recipe for Disaster)",
                "Train skills to 30+ before buying membership for better efficiency"
            ]
        ))
    
    # Rule 2: Combat level-based recommendations with knowledge pack
    if bracket:
        weapons = bracket.get("weapons", [])
        armor = bracket.get("armor", "Appropriate armor")
        training_spots = bracket.get("training_spots", [])
        
        # Format weapons list
        weapons_text = " or ".join(weapons) if weapons else "Appropriate weapon"
        
        # Get first training spot (concrete location required)
        if training_spots:
            spot = training_spots[0]
            spot_name = spot.get("name", "Training spot")
            location = spot.get("location", "")
            
            if combat_level < 50:
                items.append(AdviceItem(
                    title=f"Train at {spot_name} (Combat {combat_level})",
                    why_now=f"At {combat_level} combat, train at {spot_name} ({location}) with {weapons_text} and {armor}.",
                    steps=[
                        f"Equip {weapons_text} from Grand Exchange",
                        f"Wear {armor} for optimal defence",
                        f"Travel to {location}",
                        f"Kill {spot_name} repeatedly for combat XP",
                        f"Train Attack ({attack}), Strength ({strength}), Defence ({defence}) evenly"
                    ]
                ))
            elif combat_level < 100:
                items.append(AdviceItem(
                    title=f"Train at {spot_name} (Combat {combat_level})",
                    why_now=f"At {combat_level} combat, train at {spot_name} ({location}) with {weapons_text} and {armor}.",
                    steps=[
                        f"Upgrade to {weapons_text} from Grand Exchange",
                        f"Equip {armor} for optimal stats",
                        f"Travel to {location}",
                        f"Kill {spot_name} for efficient combat XP",
                        "Complete Waterfall Quest for quick combat XP (if not done)"
                    ]
                ))
            else:
                items.append(AdviceItem(
                    title=f"Train at {spot_name} (Combat {combat_level})",
                    why_now=f"With {combat_level} combat, train at {spot_name} ({location}) with {weapons_text} and {armor}.",
                    steps=[
                        f"Equip {weapons_text} for maximum DPS",
                        f"Wear {armor} for best defensive stats",
                        f"Travel to {location}",
                        f"Kill {spot_name} for high-level combat XP",
                        "Complete Recipe for Disaster for Barrows Gloves (if not done)"
                    ]
                ))
        else:
            # No training spots, use gear upgrade fallback
            fallback = get_fallback_gear_upgrade(bracket, profile.membership)
            if fallback:
                items.append(fallback)
    
    # Rule 3: Quest-based recommendations (concrete quest names required)
    if total_level < 500:
        if profile.membership == "f2p":
            items.append(AdviceItem(
                title="Complete Dragon Slayer",
                why_now=f"With {total_level} total level, complete Dragon Slayer to unlock Rune Platebody.",
                steps=[
                    "Complete Lost City and Merlin's Crystal quests (prerequisites)",
                    "Train Magic to 33+ for Fire Blast spell",
                    "Defeat Elvarg the Dragon in Karamja volcano",
                    "Claim Rune Platebody unlock and combat XP",
                    "Equip Rune Platebody for best F2P body armor"
                ],
                requirements=["Lost City quest", "Merlin's Crystal quest", "Magic 33+"],
                rewards=["Rune Platebody unlock", "18,650 XP in Attack, Strength, Defence, Hitpoints"],
                next_actions=[
                    "Complete Lost City quest" if profile.skills.get("crafting", 1) < 31 else "Complete Merlin's Crystal quest",
                    "Train Magic to 33+" if profile.skills.get("magic", 1) < 33 else "Start Dragon Slayer quest",
                    "Prepare food and potions for Elvarg"
                ][:3]
            ))
        else:
            items.append(AdviceItem(
                title="Complete Waterfall Quest",
                why_now=f"With {total_level} total level, complete Waterfall Quest for 13,750 combat XP.",
                steps=[
                    "Meet requirements: 30+ Attack and Strength recommended",
                    "Start quest by talking to Almera in Baxtorian Falls",
                    "Navigate through the waterfall dungeon",
                    "Defeat the Fire Giants and Moss Giants",
                    "Claim 13,750 XP in Attack and Strength"
                ],
                requirements=["30+ Attack recommended", "30+ Strength recommended"],
                rewards=["13,750 Attack XP", "13,750 Strength XP", "Access to Baxtorian Falls"],
                next_actions=[
                    "Train Attack to 30+" if attack < 30 else "Train Strength to 30+" if strength < 30 else "Start Waterfall Quest",
                    "Bring food and combat gear",
                    "Travel to Baxtorian Falls (north of Seers' Village)"
                ][:3]
            ))
    elif total_level < 1500:
        if profile.membership == "p2p":
            # Use detailed Recipe for Disaster advice
            items.append(get_recipe_for_disaster_advice(profile, combat_level, total_level))
        else:
            items.append(AdviceItem(
                title="Complete Dragon Slayer",
                why_now=f"With {total_level} total level, complete Dragon Slayer for Rune Platebody unlock.",
                steps=[
                    "Complete prerequisite quests: Lost City, Merlin's Crystal",
                    "Train Magic to 33+ for Fire Blast",
                    "Defeat Elvarg the Dragon",
                    "Claim Rune Platebody unlock",
                    "Equip Rune Platebody"
                ],
                requirements=["Lost City quest", "Merlin's Crystal quest", "Magic 33+"],
                rewards=["Rune Platebody unlock", "18,650 XP in Attack, Strength, Defence, Hitpoints"],
                next_actions=[
                    "Complete Lost City quest" if profile.skills.get("crafting", 1) < 31 else "Train Magic to 33+",
                    "Complete Merlin's Crystal quest",
                    "Prepare for Elvarg fight"
                ][:3]
            ))
    else:
        if profile.membership == "p2p":
            # Use detailed Recipe for Disaster advice
            items.append(get_recipe_for_disaster_advice(profile, combat_level, total_level))
        else:
            items.append(AdviceItem(
                title="Complete Dragon Slayer",
                why_now=f"With {total_level} total level, complete Dragon Slayer for end-game F2P gear.",
                steps=[
                    "Complete all prerequisite quests",
                    "Train Magic to 33+",
                    "Defeat Elvarg the Dragon",
                    "Claim Rune Platebody unlock",
                    "Equip Rune Platebody for best F2P body armor"
                ],
                requirements=["Lost City quest", "Merlin's Crystal quest", "Magic 33+"],
                rewards=["Rune Platebody unlock", "18,650 XP in Attack, Strength, Defence, Hitpoints"],
                next_actions=[
                    "Complete Lost City quest",
                    "Complete Merlin's Crystal quest",
                    "Train Magic to 33+ and start Dragon Slayer"
                ][:3]
            ))
    
    # Rule 4: Goal-based recommendations (concrete locations/quests/items required)
    if profile.goals:
        if "questing" in profile.goals:
            if profile.membership == "p2p":
                # Use detailed Recipe for Disaster advice
                items.append(get_recipe_for_disaster_advice(profile, combat_level, total_level))
            else:
                # F2P quest recommendation
                items.append(AdviceItem(
                    title="Complete Dragon Slayer",
                    why_now=f"With {combat_level} combat, complete Dragon Slayer to unlock Rune Platebody and combat XP.",
                    steps=[
                        "Complete prerequisite quests: Lost City, Merlin's Crystal",
                        "Train Magic to 33+ for Fire Blast spell",
                        "Defeat Elvarg the Dragon in Karamja volcano",
                        "Claim Rune Platebody unlock and combat XP rewards",
                        "Equip Rune Platebody for best F2P body armor"
                    ],
                    requirements=[
                        "Lost City quest (prerequisite)",
                        "Merlin's Crystal quest (prerequisite)",
                        "Magic 33+ (for Fire Blast)",
                        "Combat level 40+ recommended"
                    ],
                    rewards=[
                        "Rune Platebody unlock (best F2P body armor)",
                        "18,650 Attack XP",
                        "18,650 Strength XP",
                        "18,650 Defence XP",
                        "18,650 Hitpoints XP"
                    ],
                    next_actions=[
                        "Complete Lost City quest" if profile.skills.get("crafting", 1) < 31 else "Complete Merlin's Crystal quest",
                        "Train Magic to 33+" if profile.skills.get("magic", 1) < 33 else "Start Dragon Slayer quest",
                        "Prepare food and potions for Elvarg fight"
                    ][:3]
                ))
        elif "combat" in profile.goals:
            if bracket and bracket.get("training_spots"):
                spot = bracket["training_spots"][0]
                spot_name = spot.get("name", "Training spot")
                location = spot.get("location", "")
                weapons = bracket.get("weapons", [])
                weapons_text = " or ".join(weapons) if weapons else "Appropriate weapon"
                
                items.append(AdviceItem(
                    title=f"Train at {spot_name} for Combat Goals",
                    why_now=f"At {combat_level} combat, train at {spot_name} ({location}) with {weapons_text}.",
                    steps=[
                        f"Equip {weapons_text} from Grand Exchange",
                        f"Travel to {location}",
                        f"Kill {spot_name} repeatedly for combat XP",
                        f"Train Attack ({attack}), Strength ({strength}), Defence ({defence}) to 70+",
                        "Complete Waterfall Quest for quick combat XP (if members)"
                    ]
                ))
            else:
                # Fallback to quest
                fallback = get_fallback_quest(bracket, profile.membership, combat_level)
                if fallback:
                    items.append(fallback)
        elif "skilling" in profile.goals:
            # Use concrete quest for skilling
            quest = "Recipe for Disaster" if profile.membership == "p2p" else "Dragon Slayer"
            items.append(AdviceItem(
                title=f"Complete {quest} for Skill Requirements",
                why_now=f"With {total_level} total level, complete {quest} which requires multiple skills.",
                steps=[
                    f"Train Cooking to 40+ for {quest}",
                    f"Train Fishing to 53+ for {quest}",
                    f"Train other required skills for {quest}",
                    f"Complete {quest} to unlock content",
                    "Use quest rewards to boost skill levels"
                ]
            ))
        elif "gp" in profile.goals or "money_making" in profile.goals:
            items.append(AdviceItem(
                title="Complete Varrock Easy Diary",
                why_now=f"With {combat_level} combat, complete Varrock Easy Diary for daily battlestaff profit.",
                steps=[
                    "Complete Varrock Easy Diary requirements",
                    "Talk to Reldo in Varrock Palace to claim diary",
                    "Buy battlestaffs from Zaff daily (7,000 GP each)",
                    "Sell battlestaffs at Grand Exchange for profit",
                    "Repeat daily for consistent income"
                ]
            ))
    
    # Ensure we always return exactly 3 items with concrete elements
    # If we have more than 3, prioritize: membership (if F2P), combat-based, quest-based
    while len(items) < 3:
        # Use specific fallback buckets in order: gear upgrade, training spot, quest
        if len(items) == 0 or (len(items) == 1 and bracket):
            fallback = get_fallback_gear_upgrade(bracket, profile.membership)
            if fallback:
                items.append(fallback)
                continue
        
        if len(items) == 1 or (len(items) == 2 and bracket):
            fallback = get_fallback_training_spot(bracket, profile.membership)
            if fallback:
                items.append(fallback)
                continue
        
        # Final fallback: quest
        fallback = get_fallback_quest(bracket, profile.membership, combat_level)
        if fallback:
            items.append(fallback)
        else:
            # Last resort: specific gear upgrade
            items.append(AdviceItem(
                title="Upgrade to Rune Equipment",
                why_now=f"At {combat_level} combat, upgrade to Rune equipment for better stats.",
                steps=[
                    "Complete Dragon Slayer quest to unlock Rune Platebody",
                    "Purchase Rune Scimitar from Grand Exchange",
                    "Buy Rune Armor set (Platebody, Legs, Full Helm)",
                    "Equip Rune equipment for combat training",
                    "Train at Al Kharid Warriors (F2P) or Sand Crabs (members)"
                ]
            ))
    
    return items[:3]


def calculate_combat_level(skills: dict) -> int:
    """
    Calculate combat level using standard OSRS formula.
    Formula: Base + max(Melee, Ranged, Magic)
    """
    import math
    
    attack = skills.get("attack", 1)
    strength = skills.get("strength", 1)
    defence = skills.get("defence", 1)
    hitpoints = skills.get("hitpoints", 10)
    ranged = skills.get("ranged", 1)
    magic = skills.get("magic", 1)
    prayer = skills.get("prayer", 1)
    
    # Base = 0.25 * (Defence + Hitpoints + floor(Prayer/2))
    base = 0.25 * (defence + hitpoints + (prayer // 2))
    
    # Melee = 0.325 * (Attack + Strength)
    melee = 0.325 * (attack + strength)
    
    # Ranged = 0.325 * (floor(Ranged * 1.5) + floor(Prayer/2))
    ranged_cb = 0.325 * (math.floor(ranged * 1.5) + (prayer // 2))
    
    # Magic = 0.325 * (floor(Magic * 1.5) + floor(Prayer/2))
    magic_cb = 0.325 * (math.floor(magic * 1.5) + (prayer // 2))
    
    # Combat = Base + max(Melee, Ranged, Magic)
    combat = base + max(melee, ranged_cb, magic_cb)
    return int(combat)

