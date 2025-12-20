from pydantic import BaseModel, Field
from typing import List, Dict, Literal, Optional


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


class StrategyCard(BaseModel):
    title: str
    why: str = Field(description="Why this strategy matters - unlock, efficiency, future value")
    unlocks: List[str] = Field(description="What this unlocks - stats, access, builds")
    next_actions: List[str] = Field(default_factory=list, description="High-level next actions (not step-by-step)")
    unlock_path_context: str = Field(default="", description="Context for unlock path (e.g., 'barrows_gloves', 'nmz_setup')")
    build_context: str = Field(default="", description="Context for recommended build (e.g., 'nmz_melee', 'general_melee')")


class StrategyResponse(BaseModel):
    strategies: List[StrategyCard]


class AlternateSpot(BaseModel):
    name: str
    reason: str
    requirements: Optional[str] = None
    tags: Optional[List[str]] = None


class AdviceCard(BaseModel):
    title: str
    bullets: Optional[List[str]] = None
    do_this_next: Optional[str] = None
    alternates: Optional[List[AlternateSpot]] = None


class NextStrategyResponse(BaseModel):
    primary: AdviceCard
    why: AdviceCard
    prep: Optional[AdviceCard] = None


class DetailsResponse(BaseModel):
    title: str
    steps: List[str]
    sources: List[str]


class BeginnerCard(BaseModel):
    title: str = Field(description="Short, imperative action (e.g., 'Complete Waterfall Quest')")
    why_now: str = Field(description="1-2 sentences explaining the power spike or efficiency gain")
    action: str = Field(description="Exactly what the player should do next")
    next_unlock: str = Field(description="What this step enables (stats, gear, mobility, access)")
    optional: bool = Field(default=False, description="True only if skippable")
    details: str = Field(default="", description="Expandable section: how to do it, alternatives, locations")


class BeginnerPathResponse(BaseModel):
    cards: List[BeginnerCard]
    current_index: int = Field(default=0, description="Current card index in the flow")


class PlayerSetup(BaseModel):
    style: Literal["melee", "ranged", "mage", ""] = Field(default="", description="Combat style preference")
    priority: Literal["fast", "safe", "cheap", ""] = Field(default="", description="Progress priority")
    effort: Literal["afk", "normal", "sweaty", ""] = Field(default="", description="Effort level preference")


class BuildCard(BaseModel):
    context: str
    name: str
    gear_options: List[Dict] = Field(description="List of gear options with id and gear arrays")
    default_gear_option_id: str = Field(default="progression", description="Default gear option ID")
    inventory: List[str]
    prayers: List[str]
    notes: List[str]


class AdviceOption(BaseModel):
    id: str
    title: str
    summary: str = Field(description="1-2 line summary")
    do_this_next: str
    why_bullets: List[str] = Field(description="2 bullets explaining why")
    tags: Optional[List[str]] = Field(default=None, description="Optional tags like 'combat', 'quest', 'money'")


class AdviceOptionsResponse(BaseModel):
    options: List[AdviceOption]
    recommended_id: str

