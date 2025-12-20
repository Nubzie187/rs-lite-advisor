from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from models import Profile, AdviceResponse, DetailsResponse, StrategyResponse, StrategyCard, BeginnerPathResponse, BeginnerCard, PlayerSetup, BuildCard, NextStrategyResponse, AdviceCard, AdviceOptionsResponse, AdviceOption, AlternateSpot
from spot_rotation import get_alternate_spots
from database import init_db, get_profile, save_profile, get_setup, save_setup
from advisor_engine import get_advice, get_strategies, get_beginner_cards, is_beginner_player, calculate_combat_level
from hiscores import fetch_hiscores
from items_db import load_items_db  # Load items DB at startup
from build_synergy import validate_gear_tier, get_tier_description  # Synergy validation
from build_constructor import auto_construct_nmz_melee_build  # Auto-construct builds
import os
import json
from typing import List, Optional, Dict

# Initialize database
init_db()

# Load items database at startup
load_items_db()

app = FastAPI(title="RuneScape Lite Advisor API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok"}


@app.get("/profile", response_model=Profile)
async def get_user_profile():
    """Get the current user profile (creates default if none exists)"""
    return get_profile()


@app.put("/profile")
async def update_profile(profile: Profile):
    """Update and save the user profile"""
    try:
        save_profile(profile)
        return {"message": "Profile updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/advice", response_model=AdviceResponse)
async def get_advice_endpoint():
    """Get advice based on the current stored profile (beginners only)"""
    profile = get_profile()
    advice_items = get_advice(profile)
    return AdviceResponse(items=advice_items)


@app.get("/strategies", response_model=StrategyResponse)
async def get_strategies_endpoint():
    """Get strategy cards based on the current stored profile"""
    profile = get_profile()
    strategies = get_strategies(profile)
    return StrategyResponse(strategies=strategies)


def get_next_strategy(profile: Profile, path_id: str = "fast_xp") -> NextStrategyResponse:
    """Get a single next strategy recommendation based on selected path
    
    Args:
        profile: Player profile
        path_id: Path ID (fast_xp, quest_progression, money_making)
    """
    attack = profile.skills.get("attack", 1)
    strength = profile.skills.get("strength", 1)
    ranged = profile.skills.get("ranged", 1)
    magic = profile.skills.get("magic", 1)
    combat_level = calculate_combat_level(profile.skills)
    total_level = sum(profile.skills.values())
    
    # Path-specific logic
    if path_id == "quest_progression":
        # Quest-focused advice
        if total_level < 300:
            do_this = "Complete Waterfall Quest for instant 13,750 Attack and Strength XP"
            why_bullets = [
                "Waterfall Quest provides massive early combat XP with minimal requirements",
                "Unlocks access to new areas and is a prerequisite for Recipe for Disaster"
            ]
            prep_bullets = ["Get 10 Agility (can be done at Gnome Stronghold)"]
        elif total_level < 750:
            if profile.membership == "p2p":
                do_this = "Work toward Recipe for Disaster subquests to unlock Barrows Gloves"
                why_bullets = [
                    "Barrows Gloves are best-in-slot melee gloves for most builds",
                    "Recipe for Disaster unlocks many other quests and content"
                ]
                prep_bullets = ["Complete prerequisite quests: Cook's Assistant, Goblin Diplomacy"]
            else:
                do_this = "Complete Dragon Slayer I for Rune Platebody and access to Elvarg"
                why_bullets = [
                    "Dragon Slayer unlocks a powerful F2P armor piece",
                    "Engages with F2P bossing content"
                ]
                prep_bullets = ["Reach 32 Quest Points and complete required quests"]
        else:
            if profile.membership == "p2p":
                do_this = "Focus on Grandmaster quests or quest cape for max rewards"
                why_bullets = [
                    "High-level quests unlock powerful items and areas",
                    "Quest completion provides significant XP lamps and utility"
                ]
                prep_bullets = []
            else:
                do_this = "Complete all remaining F2P quests for quest points and rewards"
                why_bullets = [
                    "Maximizes F2P content completion",
                    "Prepares for potential membership benefits"
                ]
                prep_bullets = []
        
        # For quest path, use generic location
        location = "Quest locations"
        lane = "quest"
        target_level = None
        
    elif path_id == "money_making":
        # Money-making focused advice
        if profile.membership == "f2p":
            if combat_level < 30:
                do_this = "Collect Cowhides in Lumbridge or mine Clay in Varrock"
                why_bullets = [
                    "Low requirements, consistent income",
                    "Funds early gear and supplies"
                ]
                prep_bullets = []
            else:
                do_this = "Kill Hill Giants for Limpwurt Roots and Big Bones in Edgeville Dungeon"
                why_bullets = [
                    "Good F2P combat XP and drops",
                    "Consistent GP for mid-level F2P players"
                ]
                prep_bullets = []
        else:  # P2P
            if combat_level < 60:
                do_this = "Collect Snape Grass on Waterbirth Island or do early Slayer tasks"
                why_bullets = [
                    "Low-level P2P money maker",
                    "Slayer provides combat XP and drops"
                ]
                prep_bullets = []
            else:
                do_this = "Farm herbs, do high-level Slayer, or run Barrows"
                why_bullets = [
                    "High-profit methods for mid-to-high level players",
                    "Funds expensive gear and supplies"
                ]
                prep_bullets = []
        
        location = "Money-making locations"
        lane = "money"
        target_level = None
        
    else:  # fast_xp (default)
        # Determine lane by lowest combat stat
        # Melee = average of Attack and Strength
        melee_avg = (attack + strength) / 2
        lane_stats = {
            "melee": melee_avg,
            "ranged": ranged,
            "magic": magic
        }
        
        # Find the lane with the lowest stat
        lowest_lane = min(lane_stats.items(), key=lambda x: x[1])
        lane = lowest_lane[0]
        lane_level = int(lowest_lane[1])
        
        # Determine target level and training spot based on lane and current level
        if lane == "melee":
            # Use the lower of Attack or Strength for recommendations
            primary_stat = min(attack, strength)
            stat_name = "Attack" if attack <= strength else "Strength"
            
            if primary_stat < 20:
                target_level = 20
                location = "Al Kharid Warriors" if profile.membership == "f2p" else "Lumbridge Cows"
                gear = "using a scimitar"
                primary_location = location
                why_bullets = [
                    f"Reaching 20 {stat_name} unlocks better weapons and faster training",
                    "Scimitar is the fastest weapon type for melee XP"
                ]
                stop_doing = None
            elif primary_stat < 40:
                target_level = 40
                if profile.membership == "p2p":
                    location = "Rock Crabs"
                    gear = "using a scimitar"
                else:
                    location = "Al Kharid Warriors"
                    gear = "using a scimitar"
                why_bullets = [
                    f"Your melee stats ({attack} Attack, {strength} Strength) are your lowest combat stats",
                    f"Reaching 40 {stat_name} unlocks better training spots and gear"
                ]
                stop_doing = None
            elif primary_stat < 60:
                target_level = 60
                if profile.membership == "p2p":
                    location = "Sand Crabs"
                    gear = "using a scimitar"
                else:
                    location = "Hill Giants"
                    gear = "using a scimitar"
                why_bullets = [
                    f"Your melee stats ({attack} Attack, {strength} Strength) are your lowest combat stats",
                    f"Reaching 60 {stat_name} unlocks mid-game training methods"
                ]
                stop_doing = None
            else:
                target_level = min(primary_stat + 10, 99)
                if profile.membership == "p2p":
                    location = "Sand Crabs" if primary_stat < 70 else "Nightmare Zone"
                    gear = "using a scimitar"
                else:
                    location = "Hill Giants"
                    gear = "using a scimitar"
                why_bullets = [
                    f"Your melee stats ({attack} Attack, {strength} Strength) are your lowest combat stats",
                    f"Balancing combat stats improves overall account progression"
                ]
                stop_doing = None
            
            do_this = f"Train {stat_name} to {target_level} at {location} {gear}"
            
        elif lane == "ranged":
            if ranged < 20:
                target_level = 20
                location = "Lumbridge Cows"
                gear = "using a shortbow"
                why_bullets = [
                    "Ranged is your lowest combat stat and unlocks safe training methods",
                    "Shortbow is the fastest early-game ranged weapon"
                ]
                stop_doing = None
            elif ranged < 40:
                target_level = 40
                if profile.membership == "p2p":
                    location = "Rock Crabs"
                else:
                    location = "Al Kharid Warriors"
                gear = "using a shortbow"
                why_bullets = [
                    f"Ranged ({ranged}) is your lowest combat stat",
                    f"Reaching 40 Ranged unlocks better training spots and gear"
                ]
                stop_doing = None
            elif ranged < 60:
                target_level = 60
                if profile.membership == "p2p":
                    location = "Sand Crabs"
                else:
                    location = "Hill Giants"
                gear = "using a shortbow"
                why_bullets = [
                    f"Ranged ({ranged}) is your lowest combat stat",
                    f"Reaching 60 Ranged unlocks mid-game training methods"
                ]
                stop_doing = None
            else:
                target_level = min(ranged + 10, 99)
                if profile.membership == "p2p":
                    location = "Sand Crabs" if ranged < 70 else "Nightmare Zone"
                else:
                    location = "Hill Giants"
                gear = "using a shortbow"
                why_bullets = [
                    f"Ranged ({ranged}) is your lowest combat stat",
                    "Balancing combat stats improves overall account progression"
                ]
                stop_doing = None
            
            do_this = f"Train Ranged to {target_level} on {location} {gear}"
            
        else:  # magic
            if magic < 20:
                target_level = 20
                location = "Chickens (Lumbridge)"
                gear = "using Wind Strike"
                why_bullets = [
                    "Magic is your lowest combat stat and unlocks utility spells",
                    "Wind Strike is the fastest early-game magic training method"
                ]
                stop_doing = None
            elif magic < 40:
                target_level = 40
                if profile.membership == "p2p":
                    location = "Rock Crabs"
                else:
                    location = "Al Kharid Warriors"
                gear = "using Fire Strike"
                why_bullets = [
                    f"Magic ({magic}) is your lowest combat stat",
                    f"Reaching 40 Magic unlocks better spells and training methods"
                ]
                stop_doing = None
            elif magic < 60:
                target_level = 60
                if profile.membership == "p2p":
                    location = "Sand Crabs"
                else:
                    location = "Hill Giants"
                gear = "using Fire Bolt"
                why_bullets = [
                    f"Magic ({magic}) is your lowest combat stat",
                    f"Reaching 60 Magic unlocks mid-game training methods"
                ]
                stop_doing = None
            else:
                target_level = min(magic + 10, 99)
                if profile.membership == "p2p":
                    location = "Sand Crabs" if magic < 70 else "Nightmare Zone"
                else:
                    location = "Hill Giants"
                gear = "using Fire Bolt"
                why_bullets = [
                    f"Magic ({magic}) is your lowest combat stat",
                    "Balancing combat stats improves overall account progression"
                ]
                stop_doing = None
            
            do_this = f"Train Magic to {target_level} {gear} on {location}"
        
        # Determine prep bullets for fast_xp path (only things required to start, max 2, no gear sets)
        prep_bullets = []
        if lane == "melee":
            if primary_stat < 20:
                prep_bullets = ["Get a scimitar (buy from Varrock or Al Kharid)"]
            else:
                # Only mention if it's a significant upgrade or required
                prep_bullets = []
        elif lane == "ranged":
            if ranged < 20:
                prep_bullets = ["Get a shortbow and arrows"]
            else:
                prep_bullets = []
        else:  # magic
            if magic < 20:
                prep_bullets = ["Get runes: air and mind"]
            elif magic < 40:
                prep_bullets = ["Get runes: fire and mind"]
            else:
                prep_bullets = ["Get runes: fire and chaos"]
        
        # Limit prep bullets to 2
        prep_bullets = prep_bullets[:2]
    
    # Build response
    primary_card = AdviceCard(
        title=path_id.replace("_", " ").title() if path_id != "fast_xp" else f"Train {lane.capitalize()}",
        do_this_next=do_this
    )
    
    why_card = AdviceCard(
        title="Why this is best",
        bullets=why_bullets[:2]  # Max 2 bullets
    )
    
    # For quest and money paths, skip alternates
    alternates = None
    if path_id == "fast_xp" and 'target_level' in locals() and target_level is not None:
        # Extract primary location name for spot rotation
        primary_location = location
        
        # Get alternate spots
        alternates_data = get_alternate_spots(
            primary_spot=primary_location,
            membership=profile.membership,
            style=lane,
            target_level=target_level,
            max_alternates=4
        )
        
        # Convert to AlternateSpot objects
        alternates = [AlternateSpot(**alt) for alt in alternates_data] if alternates_data else None
    
    # Build response - conditionally include prep
    primary_card_with_alternates = AdviceCard(
        title=primary_card.title,
        do_this_next=do_this,
        alternates=alternates
    )
    
    response_data = {
        "primary": primary_card_with_alternates,
        "why": why_card
    }
    
    # Only include prep if it has content
    # Remove prep if do_this_next is falsy AND bullets is empty/None
    prep_has_bullets = prep_bullets and len(prep_bullets) > 0
    if prep_has_bullets:
        prep_card = AdviceCard(
            title="Prep (optional)",
            bullets=prep_bullets
        )
        response_data["prep"] = prep_card
    
    return NextStrategyResponse(**response_data)


@app.get("/advice/next", response_model=NextStrategyResponse)
async def get_next_advice(path_id: str = None):
    """Get a single next strategy card for the home screen
    
    Args:
        path_id: Optional path ID (fast_xp, quest_progression, money_making).
                 If not provided, uses the backend's recommended path.
    """
    profile = get_profile()
    
    # If no path_id provided, determine recommended path
    if path_id is None:
        options_response = get_advice_options(profile)
        path_id = options_response.recommended_id
    
    return get_next_strategy(profile, path_id)


def get_advice_options(profile: Profile) -> AdviceOptionsResponse:
    """Generate 3 meaningful option cards for the player"""
    attack = profile.skills.get("attack", 1)
    strength = profile.skills.get("strength", 1)
    defence = profile.skills.get("defence", 1)
    ranged = profile.skills.get("ranged", 1)
    magic = profile.skills.get("magic", 1)
    combat_level = calculate_combat_level(profile.skills)
    total_level = sum(profile.skills.values())
    
    options = []
    
    # Option 1: Fast XP (combat training)
    if combat_level < 50:
        options.append(AdviceOption(
            id="fast_xp",
            title="Fast Combat XP",
            summary="Focus on combat training to quickly level up and unlock better content.",
            do_this_next=f"Train at {'Sand Crabs' if profile.membership == 'p2p' else 'Al Kharid Warriors'} to reach 50+ combat.",
            why_bullets=[
                f"Your combat level ({combat_level}) is below 50, limiting access to mid-game content.",
                "Combat training unlocks better training spots, quests, and gear upgrades."
            ],
            tags=["combat"]
        ))
    else:
        options.append(AdviceOption(
            id="fast_xp",
            title="Efficient Combat Training",
            summary="Optimize your combat training for maximum XP rates and unlocks.",
            do_this_next=f"Train at {'Nightmare Zone' if profile.membership == 'p2p' else 'Hill Giants'} for efficient AFK training.",
            why_bullets=[
                f"At {combat_level} combat, you can access high-efficiency training methods.",
                "Focusing on combat unlocks end-game content and better money-making opportunities."
            ],
            tags=["combat"]
        ))
    
    # Option 2: Quest Progression
    if total_level < 500:
        options.append(AdviceOption(
            id="quest_progression",
            title="Quest Progression",
            summary="Complete key quests to unlock essential content and quality-of-life improvements.",
            do_this_next="Complete Waterfall Quest for instant combat XP, then work toward Recipe for Disaster subquests.",
            why_bullets=[
                "Quests provide massive XP rewards and unlock essential content like Barrows Gloves.",
                "Early quest completion saves hours of grinding and opens up better training methods."
            ],
            tags=["quest"]
        ))
    else:
        options.append(AdviceOption(
            id="quest_progression",
            title="Quest Completion",
            summary="Finish remaining quests to unlock end-game content and quality-of-life features.",
            do_this_next="Complete Recipe for Disaster for Barrows Gloves, then work on achievement diaries.",
            why_bullets=[
                "High-level quests unlock essential gear (Barrows Gloves) and access to new areas.",
                "Quest completion is required for many end-game activities and money-making methods."
            ],
            tags=["quest"]
        ))
    
    # Option 3: Money Making / GP
    if profile.membership == "p2p":
        options.append(AdviceOption(
            id="money_making",
            title="Build Your Bank",
            summary="Earn GP to fund gear upgrades and quality-of-life items for smoother progression.",
            do_this_next=f"Start with {'Slayer tasks' if combat_level >= 50 else 'low-level money makers like fishing or woodcutting'} to build initial capital.",
            why_bullets=[
                "Having GP allows you to buy convenience items and better gear without grinding.",
                "Early money-making sets you up for efficient training and quest completion later."
            ],
            tags=["money"]
        ))
    else:
        options.append(AdviceOption(
            id="money_making",
            title="F2P Money Making",
            summary="Earn GP in free-to-play to prepare for membership or buy essential items.",
            do_this_next="Mine iron ore or fish lobsters to build your bank before upgrading to membership.",
            why_bullets=[
                "F2P money-making helps you start membership with a solid financial foundation.",
                "Having GP ready makes membership more efficient and enjoyable."
            ],
            tags=["money"]
        ))
    
    # Determine recommended_id based on player state
    if combat_level < 30:
        recommended_id = "fast_xp"
    elif total_level < 500:
        recommended_id = "quest_progression"
    else:
        recommended_id = "fast_xp"
    
    return AdviceOptionsResponse(
        options=options,
        recommended_id=recommended_id
    )


@app.get("/advice/options", response_model=AdviceOptionsResponse)
async def get_advice_options_endpoint():
    """Get 3 option cards for the player to choose from"""
    profile = get_profile()
    return get_advice_options(profile)


@app.get("/beginner-path", response_model=BeginnerPathResponse)
async def get_beginner_path_endpoint():
    """Get beginner power path cards based on the current stored profile"""
    profile = get_profile()
    combat_level = calculate_combat_level(profile.skills)
    total_level = sum(profile.skills.values())
    
    # Check if beginner
    if not is_beginner_player(combat_level, total_level):
        return BeginnerPathResponse(cards=[], current_index=0)
    
    cards = get_beginner_cards(profile, combat_level)
    return BeginnerPathResponse(cards=cards, current_index=0)


@app.get("/setup", response_model=PlayerSetup)
async def get_setup_endpoint():
    """Get the current player setup"""
    return get_setup()


@app.put("/setup")
async def update_setup_endpoint(setup: PlayerSetup):
    """Update and save the player setup"""
    try:
        save_setup(setup)
        return {"message": "Setup updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class HiscoresImportRequest(BaseModel):
    player_name: str


@app.post("/import/hiscores")
async def import_hiscores(request: HiscoresImportRequest):
    """Import skills from OSRS hiscores for a player"""
    if not request.player_name or not request.player_name.strip():
        raise HTTPException(status_code=400, detail="Player name is required")
    
    # Fetch hiscores
    skills, error_message = fetch_hiscores(request.player_name)
    
    if skills is None:
        # Use the specific error message from fetch_hiscores
        error_detail = error_message or f"Player '{request.player_name}' not found in hiscores or error fetching data"
        raise HTTPException(status_code=404, detail=error_detail)
    
    # Get current profile and update with hiscores data
    # DO NOT overwrite membership/game_mode/goals/playtime if already set
    profile = get_profile()
    profile.player_name = request.player_name.strip()
    profile.skills = skills  # Replace skills with hiscores data
    # Preserve: membership, game_mode, goals, playtime_minutes
    
    # Save updated profile
    try:
        save_profile(profile)
        return {
            "message": f"Successfully imported hiscores for {request.player_name}",
            "skills_imported": len(skills)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving profile: {str(e)}")




class BuildsResponse(BaseModel):
    builds: List[BuildCard]


def load_builds():
    """Load builds data"""
    builds_path = os.path.join(os.path.dirname(__file__), "data", "builds_v1.json")
    try:
        with open(builds_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[BUILDS WARNING] Failed to load builds: {e}")
        return {"builds": []}


def load_item_requirements() -> Dict:
    """Load item requirements"""
    requirements_path = os.path.join(os.path.dirname(__file__), "data", "item_requirements_min.json")
    try:
        with open(requirements_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[BUILDS WARNING] Failed to load item requirements: {e}")
        return {}


def meets_requirements(item_name: str, requirements: Dict, skills: Dict[str, int]) -> bool:
    """Check if player skills meet item requirements"""
    item_reqs = requirements.get(item_name, {})
    if not item_reqs:
        return True  # No requirements = always eligible
    
    for skill, min_level in item_reqs.items():
        player_level = skills.get(skill.lower(), 1)
        if player_level < min_level:
            return False
    return True


def get_fallback_weapon(requirements: Dict, skills: Dict[str, int], membership: str) -> Optional[str]:
    """Get best eligible fallback weapon from ordered list"""
    fallback_order = [
        "Scythe of Vitur",
        "Dharok's Greataxe",
        "Abyssal Whip",
        "Dragon Scimitar"
    ]
    
    for weapon in fallback_order:
        if meets_requirements(weapon, requirements, skills):
            # Check if weapon exists in requirements (basic validation)
            if weapon in requirements:
                return weapon
    return None


def filter_weapon_by_requirements(gear: List[str], requirements: Dict, skills: Dict[str, int], membership: str) -> tuple[List[str], Optional[str]]:
    """
    Filter first weapon in gear list based on requirements.
    Only replaces gear[0] (weapon), keeps all other items unchanged.
    Returns: (filtered_gear, downgrade_note)
    """
    if not gear:
        return gear, None
    
    # Preserve original length - only modify first item
    original_length = len(gear)
    
    # Assume first item is weapon (as per requirements)
    first_item = gear[0]
    
    # Check if first item has requirements
    if first_item not in requirements:
        # No requirements, keep as-is
        return gear, None
    
    # Check if player meets requirements
    if meets_requirements(first_item, requirements, skills):
        return gear, None
    
    # Player doesn't meet requirements, find fallback
    fallback = get_fallback_weapon(requirements, skills, membership)
    if not fallback:
        # No eligible fallback, keep original (will show but player can't use)
        return gear, None
    
    # Replace ONLY gear[0] with fallback, keep rest unchanged
    new_gear = [fallback] + gear[1:]
    
    # Verify length preserved
    if len(new_gear) != original_length:
        print(f"[BUILDS WARNING] Gear list length changed from {original_length} to {len(new_gear)}")
        # Fallback: return original to prevent data loss
        return gear, None
    
    # Build downgrade note
    reqs = requirements.get(first_item, {})
    req_parts = [f"{reqs[k]} {k.capitalize()}" for k in sorted(reqs.keys())]
    req_str = " / ".join(req_parts)
    note = f"Weapon adjusted based on your stats (requires {req_str})."
    
    return new_gear, note


@app.get("/builds", response_model=BuildsResponse)
async def get_builds(context: Optional[str] = Query(None, description="Filter builds by context (e.g., 'nmz_melee', 'general_melee')")):
    """Get build cards for specified context"""
    builds_data = load_builds()
    all_builds = builds_data.get("builds", [])
    
    # Get profile and setup to determine default_gear_option_id
    profile = get_profile()
    setup = get_setup()
    
    # Filter by context if provided
    if context:
        filtered_builds = [b for b in all_builds if b.get("context") == context]
        if not filtered_builds:
            raise HTTPException(status_code=404, detail=f"No builds found for context: {context}")
    else:
        filtered_builds = all_builds
    
    # Add default_gear_option_id based on logic and validate synergy rules
    result_builds = []
    for build in filtered_builds:
        build_copy = build.copy()
        
        # Keep original gear from JSON - do NOT auto-construct
        # Only apply weapon filtering for nmz_melee if needed
        if build_copy.get("context") == "nmz_melee":
            requirements = load_item_requirements()
            skills = profile.skills
            gear_options = build_copy.get("gear_options", [])
            weapon_downgraded = False
            validation_warnings = []
            
            for gear_option in gear_options:
                gear = gear_option.get("gear", [])
                if not gear:
                    continue
                
                # Store original gear (preserve all items)
                original_gear = gear.copy()
                original_length = len(gear)
                
                # Filter weapon (only gear[0]) - this preserves all other items
                filtered_gear, note = filter_weapon_by_requirements(
                    gear, requirements, skills, profile.membership
                )
                
                # Verify length preserved - if not, keep original
                if len(filtered_gear) != original_length:
                    print(f"[BUILDS WARNING] Gear list length mismatch: {original_length} -> {len(filtered_gear)}, keeping original gear")
                    filtered_gear = original_gear  # Restore original
                else:
                    # Update gear option only if length preserved
                    gear_option["gear"] = filtered_gear
                    if note:
                        weapon_downgraded = True
                
                # Validate tier rules but don't remove items
                tier = gear_option.get("id", "")
                if tier:
                    is_valid, error_msg = validate_gear_tier(filtered_gear, tier)
                    if not is_valid:
                        validation_warnings.append(f"Tier '{tier}': {error_msg}")
                        print(f"[BUILDS WARNING] Build '{build.get('name', 'Unknown')}' tier '{tier}' validation failed: {error_msg}")
                        print(f"  Tier rules: {get_tier_description(tier)}")
                        print(f"  Gear kept as-is: {filtered_gear}")
            
            # Add notes if needed
            if weapon_downgraded or validation_warnings:
                # Ensure notes list exists
                if "notes" not in build_copy:
                    build_copy["notes"] = []
                existing_notes = set(build_copy.get("notes", []))
                
                if weapon_downgraded:
                    note_text = "Weapon adjusted based on your stats."
                    if note_text not in existing_notes:
                        build_copy["notes"].append(note_text)
                
                if validation_warnings:
                    note_text = "Some items may require higher stats or violate tier rules."
                    if note_text not in existing_notes:
                        build_copy["notes"].append(note_text)
        else:
            # For non-nmz_melee builds, just validate (don't remove items)
            gear_options = build_copy.get("gear_options", [])
            for gear_option in gear_options:
                tier = gear_option.get("id", "")
                gear = gear_option.get("gear", [])
                if gear and tier:
                    is_valid, error_msg = validate_gear_tier(gear, tier)
                    if not is_valid:
                        print(f"[BUILDS WARNING] Build '{build.get('name', 'Unknown')}' tier '{tier}' validation failed: {error_msg}")
                        print(f"  Tier rules: {get_tier_description(tier)}")
                        print(f"  Gear kept as-is: {gear}")
        
        # Determine default_gear_option_id
        if profile.game_mode in ["ironman", "hcim", "gim"]:
            # Iron → progression (no GE assumptions)
            default_id = "progression"
        elif setup.effort == "afk":
            # Effort low (AFK) → budget
            default_id = "budget"
        else:
            # Default → progression
            default_id = "progression"
        
        build_copy["default_gear_option_id"] = default_id
        result_builds.append(BuildCard(**build_copy))
    
    return BuildsResponse(builds=result_builds)


def load_items_metadata():
    """Load items acquisition metadata"""
    items_path = os.path.join(os.path.dirname(__file__), "data", "items_v1.json")
    try:
        with open(items_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[DETAILS WARNING] Failed to load items metadata: {e}")
        return {"items": []}


def load_recipes():
    """Load recipes data"""
    recipes_path = os.path.join(os.path.dirname(__file__), "data", "recipes_v1.json")
    try:
        with open(recipes_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[DETAILS WARNING] Failed to load recipes: {e}")
        return {"recipes": []}


@app.get("/details", response_model=DetailsResponse)
async def get_details(
    type: str = Query(..., description="Type: 'item' or 'food'"),
    name: str = Query(..., description="Name of the item or food")
):
    """Get detailed information about an item or food"""
    if type == "item":
        items_data = load_items_metadata()
        items = items_data.get("items", [])
        
        # Find matching item (case-insensitive)
        item = next((i for i in items if i.get("name", "").lower() == name.lower()), None)
        
        if not item:
            raise HTTPException(status_code=404, detail=f"Item '{name}' not found")
        
        # Build steps and sources from item data
        steps = []
        sources = []
        
        item_sources = item.get("sources", [])
        for source in item_sources:
            source_type = source.get("type", "")
            source_name = source.get("name", "")
            source_location = source.get("location", "")
            source_description = source.get("description", "")
            
            if source_type == "Quest":
                steps.append(f"Complete {source_name} quest")
                sources.append(f"Quest: {source_name}")
            elif source_type == "Drop":
                steps.append(f"Kill {source_name} to obtain {name}")
                sources.append(f"Drop: {source_name} ({source_description})")
            elif source_type == "Shop":
                steps.append(f"Buy {name} from {source_name} in {source_location}")
                sources.append(f"Shop: {source_name} in {source_location}")
            elif source_type == "Craft":
                level = source.get("level", "")
                skill = source.get("skill", "")
                steps.append(f"Craft {name} (requires {level} {skill})")
                sources.append(f"Craft: {level} {skill}")
            elif source_type == "GE":
                steps.append(f"Buy {name} from Grand Exchange")
                sources.append("Grand Exchange")
        
        return DetailsResponse(
            title=f"{name} Acquisition",
            steps=steps,
            sources=sources
        )
    
    elif type == "food":
        recipes_data = load_recipes()
        recipes = recipes_data.get("recipes", [])
        
        # Find matching recipe (case-insensitive)
        recipe = next((r for r in recipes if r.get("name", "").lower() == name.lower()), None)
        
        if not recipe:
            raise HTTPException(status_code=404, detail=f"Food '{name}' not found")
        
        # Build steps and sources from recipe data
        steps = []
        sources = []
        
        # Ingredient acquisition
        ingredients = recipe.get("ingredients", [])
        for ingredient in ingredients:
            ingredient_name = ingredient.get("name", "")
            ingredient_sources = ingredient.get("sources", [])
            
            for source in ingredient_sources:
                source_type = source.get("type", "")
                source_location = source.get("location", "")
                source_method = source.get("method", "")
                source_notes = source.get("notes", "")
                
                if source_type == "Fish":
                    steps.append(f"{source_method}")
                    sources.append(f"Fish: {source_location} - {source_notes}")
                elif source_type == "Buy":
                    steps.append(f"{source_method}")
                    sources.append(f"Buy: {source_location} - {source_notes}")
        
        # Cooking steps
        cooking_level = recipe.get("cooking_level", 0)
        cooking_location = recipe.get("cooking_location", "")
        cooking_method = recipe.get("cooking_method", "")
        burn_chance = recipe.get("burn_chance", "")
        nmz_quantity = recipe.get("nmz_quantity", "")
        
        steps.append(f"Train Cooking to level {cooking_level}")
        steps.append(f"{cooking_method}")
        if burn_chance:
            steps.append(f"Burn chance: {burn_chance}")
        if nmz_quantity:
            steps.append(f"Bring {nmz_quantity} for NMZ training")
        
        sources.append(f"Cooking: {cooking_location} (level {cooking_level})")
        sources.append(f"Healing: {recipe.get('healing', 0)} HP")
        
        return DetailsResponse(
            title=f"{name} Recipe",
            steps=steps,
            sources=sources
        )
    
    else:
        raise HTTPException(status_code=400, detail=f"Invalid type '{type}'. Must be 'item' or 'food'")


# Mount static files at root (after all API routes)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

