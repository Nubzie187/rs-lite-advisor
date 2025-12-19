from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from models import Profile, AdviceResponse
from database import init_db, get_profile, save_profile
from advisor_engine import get_advice
from hiscores import fetch_hiscores
import os

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


# Mount static files at root (after all API routes)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

