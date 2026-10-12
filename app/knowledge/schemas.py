"""Schemas for extracted knowledge and generated scene contracts."""

from pydantic import BaseModel, Field


class CharacterIn(BaseModel):
    name: str
    aliases: list[str] = Field(default_factory=list)
    faction: str = ""
    race: str = ""
    abilities: list[str] = Field(default_factory=list)
    known_limitations: list[str] = Field(default_factory=list)
    personality: str = ""
    motivations: list[str] = Field(default_factory=list)
    relationships: dict[str, str] = Field(default_factory=dict)
    knowledge_state: dict = Field(default_factory=dict)
    current_status: str = ""
    alive: bool = True
    confidence: float = 0.5


class LocationIn(BaseModel):
    name: str
    region: str = ""
    controlling_faction: str = ""
    history: str = ""
    important_events: list[str] = Field(default_factory=list)
    confidence: float = 0.5


class FactionIn(BaseModel):
    name: str
    members: list[str] = Field(default_factory=list)
    leadership: list[str] = Field(default_factory=list)
    objectives: list[str] = Field(default_factory=list)
    alliances: list[str] = Field(default_factory=list)
    enemies: list[str] = Field(default_factory=list)
    military_capabilities: list[str] = Field(default_factory=list)
    confidence: float = 0.5


class EventIn(BaseModel):
    event_key: str
    title: str
    chronological_order: int
    participants: list[str] = Field(default_factory=list)
    location: str = ""
    consequences: list[str] = Field(default_factory=list)
    summary: str = ""
    timeline: str = "main"
    confidence: float = 0.5


class PlotlineIn(BaseModel):
    plotline_key: str
    title: str
    originating_volume: int | None = None
    current_status: str = "unresolved"
    unresolved_questions: list[str] = Field(default_factory=list)
    affected_characters: list[str] = Field(default_factory=list)
    supporting_evidence: list[str] = Field(default_factory=list)
    priority: int = 3
    uncertainties: list[str] = Field(default_factory=list)
    timeline: str = "main"


class RuleIn(BaseModel):
    category: str
    statement: str
    confidence: float = 0.5


class AssertionIn(BaseModel):
    subject_type: str
    subject_name: str
    predicate: str
    value: str
    kind: str = "fact"
    timeline: str = "main"
    confidence: float = 0.5
    audience: str = "public"
    knowers: list[str] = Field(default_factory=list)
    believer: str | None = None
    as_of_order: int = 0


class Extraction(BaseModel):
    characters: list[CharacterIn] = Field(default_factory=list)
    locations: list[LocationIn] = Field(default_factory=list)
    factions: list[FactionIn] = Field(default_factory=list)
    events: list[EventIn] = Field(default_factory=list)
    plotlines: list[PlotlineIn] = Field(default_factory=list)
    rules: list[RuleIn] = Field(default_factory=list)
    assertions: list[AssertionIn] = Field(default_factory=list)


class SceneSpec(BaseModel):
    scene_id: str
    viewpoint_character: str
    location: str
    timestamp: str
    scene_objective: str
    participating_characters: list[str] = Field(default_factory=list)
    known_information: list[str] = Field(default_factory=list)
    required_events: list[str] = Field(default_factory=list)
    prohibited_contradictions: list[str] = Field(default_factory=list)
    target_word_count: int = 800
    previous_scene_summary: str = ""
    emotional_tone: str = ""
    desired_outcome: str = ""


class CharacterUpdate(BaseModel):
    name: str
    location: str | None = None
    alive: bool | None = None
    status: str | None = None
    learned: list[str] = Field(default_factory=list)


class StateDiff(BaseModel):
    recent_events: list[str] = Field(default_factory=list)
    character_updates: list[CharacterUpdate] = Field(default_factory=list)
    political_changes: list[str] = Field(default_factory=list)
    alliances: list[str] = Field(default_factory=list)
    open_plot_threads: list[str] = Field(default_factory=list)
    secrets_discovered: list[str] = Field(default_factory=list)
    notes: str = ""
    canon_mutation: bool = False
    resurrection_mechanism: str = ""


class DraftOutput(BaseModel):
    prose: str
    state_diff: StateDiff


class Issue(BaseModel):
    severity: str
    message: str
    evidence: str = ""
    character: str = ""


class ValidatorOutput(BaseModel):
    scores: dict[str, int] = Field(default_factory=dict)
    issues: list[Issue] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class PlannedScene(BaseModel):
    title: str
    summary: str
    viewpoint_character: str
    location: str
    required_events: list[str] = Field(default_factory=list)
    emotional_tone: str = ""
    desired_outcome: str = ""
    participating_characters: list[str] = Field(default_factory=list)


class PlannedChapter(BaseModel):
    title: str
    summary: str
    scenes: list[PlannedScene]


class LlmOutline(BaseModel):
    premise: str
    alternatives: list[str] = Field(default_factory=list)
    chapters: list[PlannedChapter]
