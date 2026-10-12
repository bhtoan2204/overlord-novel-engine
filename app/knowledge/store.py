"""Persist extracted entities. Generated fiction is not written back into these tables."""

import uuid

from sqlalchemy.orm import Session

from app.db.models import Assertion, Character, Event, Faction, Location, Plotline, WorldRule
from app.knowledge.schemas import Extraction


def _id() -> str:
    return str(uuid.uuid4())


def upsert_extraction(session: Session, extraction: Extraction, source_id: str, canon_level: str, timeline: str) -> dict:
    counts = {"characters": 0, "locations": 0, "factions": 0, "events": 0, "plotlines": 0, "rules": 0, "assertions": 0}
    for item in extraction.characters:
        row = session.query(Character).filter(Character.name == item.name).one_or_none()
        if row is None:
            row = Character(id=_id(), name=item.name, canon_level=canon_level, evidence_source_id=source_id)
            session.add(row)
        row.aliases = item.aliases
        row.faction = item.faction
        row.race = item.race
        row.abilities = item.abilities
        row.known_limitations = item.known_limitations
        row.personality = item.personality
        row.motivations = item.motivations
        row.relationships = item.relationships
        row.knowledge_state = item.knowledge_state or {"knows": [], "does_not_know": []}
        row.current_status = item.current_status
        row.alive = item.alive
        row.confidence = item.confidence
        row.canon_level = canon_level
        row.evidence_source_id = source_id
        counts["characters"] += 1
    for item in extraction.locations:
        row = session.query(Location).filter(Location.name == item.name).one_or_none()
        if row is None:
            row = Location(id=_id(), name=item.name, canon_level=canon_level, evidence_source_id=source_id)
            session.add(row)
        row.region = item.region
        row.controlling_faction = item.controlling_faction
        row.history = item.history
        row.important_events = item.important_events
        row.confidence = item.confidence
        row.canon_level = canon_level
        row.evidence_source_id = source_id
        counts["locations"] += 1
    for item in extraction.factions:
        row = session.query(Faction).filter(Faction.name == item.name).one_or_none()
        if row is None:
            row = Faction(id=_id(), name=item.name, canon_level=canon_level, evidence_source_id=source_id)
            session.add(row)
        row.members = item.members
        row.leadership = item.leadership
        row.objectives = item.objectives
        row.alliances = item.alliances
        row.enemies = item.enemies
        row.military_capabilities = item.military_capabilities
        row.confidence = item.confidence
        row.canon_level = canon_level
        row.evidence_source_id = source_id
        counts["factions"] += 1
    for item in extraction.events:
        row = session.query(Event).filter(Event.event_key == item.event_key).one_or_none()
        if row is None:
            row = Event(id=_id(), event_key=item.event_key, canon_level=canon_level, evidence_source_id=source_id)
            session.add(row)
        row.title = item.title
        row.chronological_order = item.chronological_order
        row.participants = item.participants
        row.location = item.location
        row.consequences = item.consequences
        row.summary = item.summary
        row.timeline = item.timeline or timeline
        row.confidence = item.confidence
        row.canon_level = canon_level
        row.evidence_source_id = source_id
        counts["events"] += 1
    for item in extraction.plotlines:
        row = session.query(Plotline).filter(Plotline.plotline_key == item.plotline_key).one_or_none()
        if row is None:
            row = Plotline(id=_id(), plotline_key=item.plotline_key, canon_level=canon_level)
            session.add(row)
        row.title = item.title
        row.originating_volume = item.originating_volume
        row.current_status = item.current_status
        row.unresolved_questions = item.unresolved_questions
        row.affected_characters = item.affected_characters
        row.supporting_evidence = item.supporting_evidence or [source_id]
        row.priority = item.priority
        row.uncertainties = item.uncertainties
        row.timeline = item.timeline or timeline
        row.canon_level = canon_level
        counts["plotlines"] += 1
    for item in extraction.rules:
        row = WorldRule(
            id=_id(),
            category=item.category,
            statement=item.statement,
            canon_level=canon_level,
            evidence_source_id=source_id,
            confidence=item.confidence,
        )
        session.add(row)
        counts["rules"] += 1
    for item in extraction.assertions:
        if not source_id:
            raise ValueError("Every assertion needs an evidence source.")
        session.add(
            Assertion(
                id=_id(),
                subject_type=item.subject_type,
                subject_name=item.subject_name,
                predicate=item.predicate,
                value=item.value,
                kind=item.kind,
                canon_level=canon_level,
                timeline=item.timeline or timeline,
                confidence=item.confidence,
                evidence_source_id=source_id,
                audience=item.audience,
                knowers=item.knowers,
                believer=item.believer,
                as_of_order=item.as_of_order,
            )
        )
        counts["assertions"] += 1
    return counts
