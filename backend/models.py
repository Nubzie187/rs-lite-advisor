from pydantic import BaseModel, Field
from typing import List, Dict, Literal


class Profile(BaseModel):
    game_mode: Literal["main", "ironman", "hcim", "gim"] = Field(default="main")
    membership: Literal["f2p", "p2p"] = Field(default="f2p")
    goals: List[str] = Field(default_factory=list)
    playtime_minutes: int = Field(default=0, ge=0)
    skills: Dict[str, int] = Field(default_factory=dict)


class AdviceItem(BaseModel):
    title: str
    why_now: str
    steps: List[str]


class AdviceResponse(BaseModel):
    items: List[AdviceItem]

