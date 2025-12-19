from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from models import Profile, AdviceResponse
from database import init_db, get_profile, save_profile
from advisor_engine import get_advice
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


# Mount static files at root (after all API routes)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

