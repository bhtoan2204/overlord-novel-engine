"""SQLite tables. Canonical rows are never updated by generated-story commits."""

from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Source(Base):
    __tablename__ = "sources"
    __table_args__ = (UniqueConstraint("content_checksum", name="uq_source_checksum"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(400))
    source_url: Mapped[str | None] = mapped_column(String(1000))
    source_type: Mapped[str] = mapped_column(String(80))
    volume_number: Mapped[int | None] = mapped_column(Integer)
    chapter_number: Mapped[int | None] = mapped_column(Integer)
    segment_order: Mapped[int] = mapped_column(Integer, default=0)
    timeline: Mapped[str] = mapped_column(String(40), default="main")
    canon_level: Mapped[str] = mapped_column(String(40))
    copyright_or_license_status: Mapped[str] = mapped_column(String(200))
    language: Mapped[str] = mapped_column(String(16), default="vi")
    ingestion_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    content_checksum: Mapped[str] = mapped_column(String(64))
    storage_path: Mapped[str | None] = mapped_column(String(1000))
    processing_state: Mapped[str] = mapped_column(String(40), default="imported")
    training_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    word_count: Mapped[int] = mapped_column(Integer, default=0)

    segments: Mapped[list["Segment"]] = relationship(back_populates="source")


class Segment(Base):
    __tablename__ = "segments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"))
    ordinal: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    canon_level: Mapped[str] = mapped_column(String(40))
    timeline: Mapped[str] = mapped_column(String(40), default="main")
    volume_number: Mapped[int | None] = mapped_column(Integer)
    source: Mapped[Source] = relationship(back_populates="segments")


class Character(Base):
    __tablename__ = "characters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    aliases: Mapped[list] = mapped_column(JSON, default=list)
    faction: Mapped[str] = mapped_column(String(200), default="")
    race: Mapped[str] = mapped_column(String(200), default="")
    abilities: Mapped[list] = mapped_column(JSON, default=list)
    known_limitations: Mapped[list] = mapped_column(JSON, default=list)
    personality: Mapped[str] = mapped_column(Text, default="")
    motivations: Mapped[list] = mapped_column(JSON, default=list)
    relationships: Mapped[dict] = mapped_column(JSON, default=dict)
    knowledge_state: Mapped[dict] = mapped_column(JSON, default=dict)
    current_status: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    canon_level: Mapped[str] = mapped_column(String(40))
    evidence_source_id: Mapped[str | None] = mapped_column(String(36))
    alive: Mapped[bool] = mapped_column(Boolean, default=True)


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    region: Mapped[str] = mapped_column(String(200), default="")
    controlling_faction: Mapped[str] = mapped_column(String(200), default="")
    history: Mapped[str] = mapped_column(Text, default="")
    important_events: Mapped[list] = mapped_column(JSON, default=list)
    canon_level: Mapped[str] = mapped_column(String(40))
    evidence_source_id: Mapped[str | None] = mapped_column(String(36))
    confidence: Mapped[float] = mapped_column(Float, default=0.5)


class Faction(Base):
    __tablename__ = "factions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    members: Mapped[list] = mapped_column(JSON, default=list)
    leadership: Mapped[list] = mapped_column(JSON, default=list)
    objectives: Mapped[list] = mapped_column(JSON, default=list)
    alliances: Mapped[list] = mapped_column(JSON, default=list)
    enemies: Mapped[list] = mapped_column(JSON, default=list)
    military_capabilities: Mapped[list] = mapped_column(JSON, default=list)
    canon_level: Mapped[str] = mapped_column(String(40))
    evidence_source_id: Mapped[str | None] = mapped_column(String(36))
    confidence: Mapped[float] = mapped_column(Float, default=0.5)


class Event(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    event_key: Mapped[str] = mapped_column(String(120), unique=True)
    title: Mapped[str] = mapped_column(String(300))
    chronological_order: Mapped[int] = mapped_column(Integer)
    participants: Mapped[list] = mapped_column(JSON, default=list)
    location: Mapped[str] = mapped_column(String(200), default="")
    consequences: Mapped[list] = mapped_column(JSON, default=list)
    summary: Mapped[str] = mapped_column(Text, default="")
    evidence_source_id: Mapped[str | None] = mapped_column(String(36))
    canon_level: Mapped[str] = mapped_column(String(40))
    timeline: Mapped[str] = mapped_column(String(40), default="main")
    confidence: Mapped[float] = mapped_column(Float, default=0.5)


class Plotline(Base):
    __tablename__ = "plotlines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    plotline_key: Mapped[str] = mapped_column(String(120), unique=True)
    title: Mapped[str] = mapped_column(String(300))
    originating_volume: Mapped[int | None] = mapped_column(Integer)
    current_status: Mapped[str] = mapped_column(String(80), default="unresolved")
    unresolved_questions: Mapped[list] = mapped_column(JSON, default=list)
    affected_characters: Mapped[list] = mapped_column(JSON, default=list)
    supporting_evidence: Mapped[list] = mapped_column(JSON, default=list)
    priority: Mapped[int] = mapped_column(Integer, default=3)
    uncertainties: Mapped[list] = mapped_column(JSON, default=list)
    canon_level: Mapped[str] = mapped_column(String(40))
    timeline: Mapped[str] = mapped_column(String(40), default="main")


class WorldRule(Base):
    __tablename__ = "world_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    category: Mapped[str] = mapped_column(String(80))
    statement: Mapped[str] = mapped_column(Text)
    canon_level: Mapped[str] = mapped_column(String(40))
    evidence_source_id: Mapped[str | None] = mapped_column(String(36))
    confidence: Mapped[float] = mapped_column(Float, default=0.5)


class Assertion(Base):
    __tablename__ = "assertions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    subject_type: Mapped[str] = mapped_column(String(40))
    subject_name: Mapped[str] = mapped_column(String(200))
    predicate: Mapped[str] = mapped_column(String(120))
    value: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(String(40))
    canon_level: Mapped[str] = mapped_column(String(40))
    timeline: Mapped[str] = mapped_column(String(40), default="main")
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    evidence_source_id: Mapped[str | None] = mapped_column(String(36))
    audience: Mapped[str] = mapped_column(String(40), default="public")
    knowers: Mapped[list] = mapped_column(JSON, default=list)
    believer: Mapped[str | None] = mapped_column(String(200))
    as_of_order: Mapped[int] = mapped_column(Integer, default=0)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(300))
    language: Mapped[str] = mapped_column(String(16), default="vi")
    disclaimer: Mapped[str] = mapped_column(Text)
    workflow_state: Mapped[str] = mapped_column(String(40), default="NOT_STARTED")
    resume_state: Mapped[str | None] = mapped_column(String(40))
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    snapshot_version: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class OutlineNode(Base):
    __tablename__ = "outline_nodes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    parent_id: Mapped[str | None] = mapped_column(String(36))
    level: Mapped[str] = mapped_column(String(20))
    ordinal: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(300))
    summary: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(40), default="draft")
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    target_words: Mapped[int] = mapped_column(Integer, default=0)
    actual_words: Mapped[int] = mapped_column(Integer, default=0)
    completion_status: Mapped[str] = mapped_column(String(40), default="PLANNED")
    checkpoint: Mapped[dict] = mapped_column(JSON, default=dict)
    revision_history: Mapped[list] = mapped_column(JSON, default=list)
    continuity: Mapped[dict] = mapped_column(JSON, default=dict)


class ProseChunk(Base):
    """One committed piece of generated prose. Generated fiction, not a canon source."""

    __tablename__ = "prose_chunks"
    __table_args__ = (UniqueConstraint("beat_id", "ordinal", name="uq_chunk_beat_ordinal"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    beat_id: Mapped[str] = mapped_column(String(36))
    scene_id: Mapped[str] = mapped_column(String(36))
    part_id: Mapped[str] = mapped_column(String(36))
    ordinal: Mapped[int] = mapped_column(Integer)
    prose: Mapped[str] = mapped_column(Text)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    finish_reason: Mapped[str] = mapped_column(String(40), default="stop")
    status: Mapped[str] = mapped_column(String(40), default="ACCEPTED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class PreservedDraft(Base):
    """Copy of an older approved draft kept when an outline is replaced."""

    __tablename__ = "preserved_drafts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    original_node_id: Mapped[str] = mapped_column(String(36))
    title: Mapped[str] = mapped_column(String(300), default="")
    prose: Mapped[str] = mapped_column(Text)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SceneDraft(Base):
    __tablename__ = "scene_drafts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    node_id: Mapped[str] = mapped_column(ForeignKey("outline_nodes.id", ondelete="CASCADE"))
    iteration: Mapped[int] = mapped_column(Integer)
    prose: Mapped[str] = mapped_column(Text)
    spec: Mapped[dict] = mapped_column(JSON, default=dict)
    selected: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ValidationReport(Base):
    __tablename__ = "validation_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    draft_id: Mapped[str] = mapped_column(ForeignKey("scene_drafts.id", ondelete="CASCADE"))
    validator: Mapped[str] = mapped_column(String(40))
    scores: Mapped[dict] = mapped_column(JSON, default=dict)
    issues: Mapped[list] = mapped_column(JSON, default=list)
    recommendations: Mapped[list] = mapped_column(JSON, default=list)
    human_review: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Snapshot(Base):
    __tablename__ = "snapshots"
    __table_args__ = (UniqueConstraint("project_id", "version", name="uq_snapshot_version"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    version: Mapped[int] = mapped_column(Integer)
    node_id: Mapped[str | None] = mapped_column(String(36))
    state: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class StateDiff(Base):
    __tablename__ = "state_diffs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    node_id: Mapped[str] = mapped_column(String(36))
    diff: Mapped[dict] = mapped_column(JSON)
    validated: Mapped[bool] = mapped_column(Boolean, default=False)
    committed: Mapped[bool] = mapped_column(Boolean, default=False)
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(40))
    state: Mapped[str] = mapped_column(String(40))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    checkpoint: Mapped[dict] = mapped_column(JSON, default=dict)
    error: Mapped[str | None] = mapped_column(Text)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    node_id: Mapped[str] = mapped_column(String(36))
    ratings: Mapped[dict] = mapped_column(JSON)
    comment: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class CatalogEntry(Base):
    __tablename__ = "catalog_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(400))
    url: Mapped[str] = mapped_column(String(1000))
    source_type: Mapped[str] = mapped_column(String(80), default="index_link")
    volume_number: Mapped[int | None] = mapped_column(Integer)
    classification: Mapped[str] = mapped_column(String(40), default="SECONDARY_REFERENCE")
    robots_status: Mapped[str] = mapped_column(String(40))
    notes: Mapped[str] = mapped_column(Text, default="")
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class CanonReview(Base):
    __tablename__ = "canon_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    report: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
