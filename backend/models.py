from pydantic import BaseModel, Field
from typing import List, Dict, Literal


class Profile(BaseModel):
    player_name: str = Field(default="", description="RuneScape player name")
    game_mode: Literal["main", "ironman", "hcim", "gim"] = Field(default="main")
    membership: Literal["f2p", "p2p"] = Field(default="f2p")
    goals: List[str] = Field(default_factory=list)
    playtime_minutes: int = Field(default=0, ge=0)
    skills: Dict[str, int] = Field(default_factory=dict)


class AdviceItem(BaseModel):
    title: str
    why_now: str
    steps: List[str]
    requirements: List[str] = Field(default_factory=list, description="Explicit skill/quest requirements")
    rewards: List[str] = Field(default_factory=list, description="Explicit reward list and why it matters")
    next_actions: List[str] = Field(default_factory=list, description="Concrete steps tailored to current stats")
    why_over_alternatives: str = Field(default="", description="Why this recommendation over alternatives")


class AdviceResponse(BaseModel):
    items: List[AdviceItem]

