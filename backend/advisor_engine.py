from models import Profile, AdviceItem


def get_advice(profile: Profile) -> list[AdviceItem]:
    """
    Simple rule-based advisor engine.
    Returns exactly 3 advice items based on profile.
    """
    items = []
    
    # Rule 1: Membership-based recommendation
    if profile.membership == "f2p":
        items.append(AdviceItem(
            title="Upgrade to Membership",
            why_now="You're currently on free-to-play. Membership unlocks 20+ skills, hundreds of quests, and much more content.",
            steps=[
                "Complete all F2P quests first to maximize value",
                "Save up 3-5M GP for initial membership expenses",
                "Plan your first week: unlock transportation (fairy rings, spirit trees)",
                "Focus on member-exclusive skills (Herblore, Farming, Construction)",
                "Join a clan for member benefits and community"
            ]
        ))
    else:
        # P2P recommendation
        total_level = sum(profile.skills.values())
        if total_level < 500:
            items.append(AdviceItem(
                title="Level Up Core Combat Skills",
                why_now="Your total level is low. Focus on combat to unlock better money-making methods and quest requirements.",
                steps=[
                    "Train Attack, Strength, and Defence to 40+",
                    "Complete Waterfall Quest for quick combat XP",
                    "Train at Sand Crabs or Ammonite Crabs",
                ]
            ))
        else:
            items.append(AdviceItem(
                title="Unlock Key Transportation Methods",
                why_now="With your current levels, efficient travel will save hours of gameplay.",
                steps=[
                    "Complete Fairy Tale Part 1 for fairy ring access",
                    "Unlock Spirit Trees by completing Tree Gnome Village",
                    "Get 30 Agility for shortcuts",
                    "Complete The Grand Tree for gnome glider access"
                ]
            ))
    
    # Rule 2: Goal-based recommendations
    if "questing" in profile.goals:
        items.append(AdviceItem(
            title="Complete Recipe for Disaster",
            why_now="This quest series unlocks the best gloves in the game and provides excellent rewards.",
            steps=[
                "Complete all prerequisite quests (Cook's Assistant, etc.)",
                "Level up required skills (Cooking, Fishing, etc.)",
                "Complete each subquest one by one",
                "Save up for Barrows Gloves (130K from Culinaromancer's Chest)"
            ]
        ))
    elif "combat" in profile.goals:
        combat_level = calculate_combat_level(profile.skills)
        if combat_level < 50:
            items.append(AdviceItem(
                title="Reach 50 Combat for Better Training",
                why_now="50 combat unlocks better training spots and access to more content.",
                steps=[
                    "Train all combat stats evenly",
                    "Complete Dragon Slayer for better gear",
                    "Unlock the Warriors' Guild at 130 combined Attack + Strength",
                    "Start training at Slayer tasks"
                ]
            ))
        else:
            items.append(AdviceItem(
                title="Start Slayer Training",
                why_now="Slayer provides variety, good money, and unlocks unique monsters and rewards.",
                steps=[
                    "Get a Slayer task from a Slayer Master",
                    "Train Slayer alongside combat skills",
                    "Unlock Slayer rewards (helmets, rings, blocks)",
                    "Aim for 50+ Slayer for profitable tasks"
                ]
            ))
    elif "skilling" in profile.goals:
        items.append(AdviceItem(
            title="Achieve Base 50 Skills",
            why_now="Base 50 unlocks most quest requirements and provides a solid foundation for all content.",
            steps=[
                "Focus on one skill at a time for efficiency",
                "Use quest rewards to skip early levels",
                "Complete Achievement Diaries for XP lamps",
                "Join a skilling clan for tips and motivation"
            ]
        ))
    elif "gp" in profile.goals or "money_making" in profile.goals:
        items.append(AdviceItem(
            title="Start Consistent Money Making",
            why_now="Building a steady income early allows you to afford better gear and training methods.",
            steps=[
                "Complete Varrock Easy Diary for daily battlestaff profit",
                "Train Fishing and Cooking for sustainable food income",
                "Complete Throne of Miscellania for passive income",
                "Unlock High Alchemy for consistent profit from items"
            ]
        ))
    else:
        # Default if no specific goals
        items.append(AdviceItem(
            title="Complete Achievement Diaries",
            why_now="Diaries provide excellent rewards, XP lamps, and unlock useful features.",
            steps=[
                "Start with Easy diaries in each region",
                "Complete quest prerequisites",
                "Level up required skills gradually",
                "Work towards Medium diaries for better rewards"
            ]
        ))
    
    # Rule 3: Skill level-based recommendation
    attack = profile.skills.get("attack", 1)
    strength = profile.skills.get("strength", 1)
    defence = profile.skills.get("defence", 1)
    
    if attack < 40 or strength < 40 or defence < 40:
        items.append(AdviceItem(
            title="Reach 40 in All Combat Stats",
            why_now="Level 40 unlocks Rune equipment, significantly improving your combat effectiveness.",
            steps=[
                "Train at Sand Crabs (if members) or Al Kharid Warriors (F2P)",
                "Complete quests that give combat XP (Waterfall Quest, etc.)",
                "Use XP lamps from Achievement Diaries",
                "Equip the best gear you can afford for faster training"
            ]
        ))
    elif max(profile.skills.values(), default=1) < 50:
        items.append(AdviceItem(
            title="Diversify Your Skills",
            why_now="Having balanced skills unlocks more quests, diaries, and money-making methods.",
            steps=[
                "Train each skill to at least level 20",
                "Complete quests that give XP in multiple skills",
                "Use daily XP lamps from Achievement Diaries",
                "Focus on skills needed for your goals"
            ]
        ))
    else:
        items.append(AdviceItem(
            title="Work Towards Quest Point Cape",
            why_now="Quests provide the best XP rewards and unlock essential content.",
            steps=[
                "Complete all F2P quests first",
                "Work through quest series (Elf, Myreque, etc.)",
                "Level up skills as needed for quest requirements",
                "Use quest guides for efficiency"
            ]
        ))
    
    # Ensure we always return exactly 3 items
    if len(items) < 3:
        # Fallback items if somehow we have fewer than 3
        while len(items) < 3:
            items.append(AdviceItem(
                title="Continue Your Journey",
                why_now="Keep progressing towards your goals and exploring new content.",
                steps=[
                    "Set daily or weekly goals",
                    "Track your progress",
                    "Join a community for support",
                    "Have fun and enjoy the game"
                ]
            ))
    return items[:3]


def calculate_combat_level(skills: dict) -> int:
    """Calculate combat level from skills"""
    attack = skills.get("attack", 1)
    strength = skills.get("strength", 1)
    defence = skills.get("defence", 1)
    hitpoints = skills.get("hitpoints", 10)
    ranged = skills.get("ranged", 1)
    magic = skills.get("magic", 1)
    prayer = skills.get("prayer", 1)
    
    base = 0.25 * (defence + hitpoints + (prayer // 2))
    melee = 0.325 * (attack + strength)
    ranged_cb = 0.325 * ((ranged * 1.5) + (prayer // 2))
    magic_cb = 0.325 * ((magic * 1.5) + (prayer // 2))
    
    combat = base + max(melee, ranged_cb, magic_cb)
    return int(combat)

