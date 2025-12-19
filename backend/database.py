import json
import os
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from models import Profile

Base = declarative_base()


class ProfileModel(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    player_name = Column(String, default="")
    game_mode = Column(String, default="main")
    membership = Column(String, default="f2p")
    goals = Column(Text, nullable=True)  # JSON array as string
    playtime_minutes = Column(Integer, default=0)
    skills = Column(Text, nullable=True)  # JSON dict as string


# Database setup
DATABASE_PATH = os.getenv("DATABASE_PATH", "/data/app.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


def get_default_profile() -> Profile:
    """Return a default profile"""
    return Profile(
        player_name="",
        game_mode="main",
        membership="f2p",
        goals=[],
        playtime_minutes=0,
        skills={
            "attack": 1,
            "strength": 1,
            "defence": 1,
            "hitpoints": 10,
            "ranged": 1,
            "magic": 1,
            "prayer": 1
        }
    )


def get_profile() -> Profile:
    """Get the stored profile or return default"""
    db = SessionLocal()
    try:
        profile_row = db.query(ProfileModel).first()
        if not profile_row:
            default = get_default_profile()
            save_profile(default)
            return default
        
        return Profile(
            player_name=profile_row.player_name or "",
            game_mode=profile_row.game_mode,
            membership=profile_row.membership,
            goals=json.loads(profile_row.goals) if profile_row.goals else [],
            playtime_minutes=profile_row.playtime_minutes,
            skills=json.loads(profile_row.skills) if profile_row.skills else {}
        )
    finally:
        db.close()


def save_profile(profile: Profile):
    """Save or update the profile"""
    db = SessionLocal()
    try:
        profile_row = db.query(ProfileModel).first()
        
        if profile_row:
            # Update existing
            profile_row.player_name = profile.player_name
            profile_row.game_mode = profile.game_mode
            profile_row.membership = profile.membership
            profile_row.goals = json.dumps(profile.goals)
            profile_row.playtime_minutes = profile.playtime_minutes
            profile_row.skills = json.dumps(profile.skills)
        else:
            # Create new
            profile_row = ProfileModel(
                player_name=profile.player_name,
                game_mode=profile.game_mode,
                membership=profile.membership,
                goals=json.dumps(profile.goals),
                playtime_minutes=profile.playtime_minutes,
                skills=json.dumps(profile.skills)
            )
            db.add(profile_row)
        
        db.commit()
    finally:
        db.close()

