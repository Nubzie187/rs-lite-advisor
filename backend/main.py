from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from models import Profile, AdviceResponse, DetailsResponse
from database import init_db, get_profile, save_profile
from advisor_engine import get_advice
from hiscores import fetch_hiscores
import os
import json
from typing import List, Optional

# Initialize database
init_db()

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
    """Get advice based on the current stored profile"""
    profile = get_profile()
    advice_items = get_advice(profile)
    return AdviceResponse(items=advice_items)


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


class BuildCard(BaseModel):
    context: str
    name: str
    gear: List[str]
    inventory: List[str]
    prayers: List[str]
    notes: List[str]


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


@app.get("/builds", response_model=BuildsResponse)
async def get_builds(context: Optional[str] = Query(None, description="Filter builds by context (e.g., 'nmz_melee', 'general_melee')")):
    """Get build cards for specified context"""
    builds_data = load_builds()
    all_builds = builds_data.get("builds", [])
    
    if context:
        # Filter by context
        filtered_builds = [b for b in all_builds if b.get("context") == context]
        if not filtered_builds:
            raise HTTPException(status_code=404, detail=f"No builds found for context: {context}")
        return BuildsResponse(builds=[BuildCard(**build) for build in filtered_builds])
    else:
        # Return all builds
        return BuildsResponse(builds=[BuildCard(**build) for build in all_builds])


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

