"""Mutable story state. Commits never update canonical knowledge rows."""

import copy

from sqlalchemy.orm import Session

from app.core.canon import MAIN_TIMELINE
from app.db.models import Character, Event, Plotline
from app.knowledge.schemas import StateDiff


def initial_state(session: Session) -> dict:
    characters = {}
    for row in session.query(Character).all():
        characters[row.name] = {
            "alive": row.alive,
            "location": row.faction,
            "status": row.current_status,
            "race": row.race,
            "knows": list((row.knowledge_state or {}).get("knows") or []),
            "does_not_know": list((row.knowledge_state or {}).get("does_not_know") or []),
        }
    events = [
        {"key": row.event_key, "title": row.title, "order": row.chronological_order, "summary": row.summary}
        for row in session.query(Event).filter(Event.timeline == MAIN_TIMELINE).order_by(Event.chronological_order)
    ]
    threads = [
        row.plotline_key
        for row in session.query(Plotline).filter(Plotline.timeline == MAIN_TIMELINE, Plotline.current_status != "resolved")
    ]
    return {
        "label": "after_volume_16",
        "characters": characters,
        "recent_events": events,
        "open_plot_threads": threads,
        "political_changes": [],
        "alliances": [],
        "secrets_discovered": [],
        "generated": True,
    }


def validate_diff(diff: StateDiff, state: dict) -> str | None:
    if diff.canon_mutation:
        return "A story diff cannot modify canonical source records."
    for update in diff.character_updates:
        current = state.get("characters", {}).get(update.name)
        if current and current.get("alive") is False and update.alive is True and not diff.resurrection_mechanism.strip():
            return f"Refusing to resurrect {update.name} without an established mechanism."
    return None


def apply_diff(state: dict, diff: StateDiff, scene_id: str) -> dict:
    updated = copy.deepcopy(state)
    updated["label"] = scene_id
    for event in diff.recent_events:
        updated["recent_events"].append({"key": f"generated:{scene_id}:{len(updated['recent_events'])}", "title": event, "summary": event, "order": 10000})
    for item in diff.open_plot_threads:
        if item not in updated["open_plot_threads"]:
            updated["open_plot_threads"].append(item)
    updated["political_changes"].extend(diff.political_changes)
    updated["alliances"].extend(diff.alliances)
    updated["secrets_discovered"].extend(diff.secrets_discovered)
    for change in diff.character_updates:
        slot = updated["characters"].setdefault(
            change.name,
            {"alive": True, "location": "", "status": "", "race": "", "knows": [], "does_not_know": []},
        )
        if change.location:
            slot["location"] = change.location
        if change.alive is not None:
            slot["alive"] = change.alive
        if change.status:
            slot["status"] = change.status
        for learned in change.learned:
            if learned not in slot["knows"]:
                slot["knows"].append(learned)
    if diff.notes:
        updated.setdefault("notes", [])
        updated["notes"].append(diff.notes)
    return updated
