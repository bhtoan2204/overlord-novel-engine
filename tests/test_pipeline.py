import json
from pathlib import Path

from app.core.workflow import WorkflowState
from app.db.models import Character, Job, OutlineNode, Snapshot
from app.inference.base import ScriptedBackend
from app.narrative.pipeline import create_outline, generate_scene, recover_interrupted, rollback_state, verify_canon
from app.narrative.preferences import preference_instructions
from app.services.library import import_file


def _prepare(app, session):
    notes = Path(__file__).resolve().parents[1] / "data" / "seed" / "volume_16_study_notes.json"
    from app.narrative.pipeline import create_project
    from app.core.disclaimer import DISCLAIMER

    project = create_project(session, "Tập 17", DISCLAIMER)
    import_file(
        session,
        app.state.settings,
        app.state.embedder,
        app.state.index,
        notes,
        title="notes",
        source_type="user_notes",
        canon_level="USER_INTERPRETATION",
        license_status="original-structured-notes",
        project=project,
    )
    session.commit()
    return project


def test_revision_fixes_an_injected_contradiction(app, session):
    project = _prepare(app, session)
    verify_canon(session, project)
    create_outline(session, project, app.state.settings)
    from app.narrative.pipeline import approve_outline

    approve_outline(session, project)
    session.commit()
    scene = session.query(OutlineNode).filter(OutlineNode.level == "scene").first()
    scene.payload = {**scene.payload, "target_word_count": 40}
    event = scene.payload["required_events"][0]
    bad = {
        "prose": f"Ainz Ooal Gown là một nông dân loài người, không biết phép thuật.\n\n{event}",
        "state_diff": {"recent_events": [event], "notes": "bad"},
    }
    good = {
        "prose": f"Ainz Ooal Gown không nâng giọng.\n\n{event}\n\n— Giữ lăng, — ông nói.",
        "state_diff": {"recent_events": [event], "notes": "revised"},
    }
    backend = ScriptedBackend([json.dumps(bad, ensure_ascii=False), json.dumps(good, ensure_ascii=False)])
    result = generate_scene(session, project, app.state.settings, backend, app.state.embedder, app.state.index)
    session.commit()
    assert result["status"] == "approved"
    assert result["iterations"] == 2
    canon = session.get(Character, session.query(Character).filter(Character.name == "Ainz Ooal Gown").one().id)
    assert "Undead" in canon.race
    assert "nông dân" not in canon.current_status
    snapshot = session.query(Snapshot).filter(Snapshot.version == project.snapshot_version).one()
    assert event in [item.get("title") or item.get("summary") for item in snapshot.state["recent_events"]]


def test_checkpoint_recovery_keeps_approved_work(app, session):
    project = _prepare(app, session)
    job = Job(
        id="job-1",
        project_id=project.id,
        kind="generate_scenes",
        state=WorkflowState.SCENE_GENERATING.value,
        checkpoint={"approved_scene_id": "scene-kept"},
    )
    project.workflow_state = WorkflowState.SCENE_GENERATING.value
    session.add(job)
    session.commit()
    assert recover_interrupted(session) == 1
    session.commit()
    session.refresh(job)
    assert job.state == WorkflowState.PAUSED.value
    assert job.checkpoint["approved_scene_id"] == "scene-kept"


def test_rollback_does_not_touch_canon_rows(app, session):
    project = _prepare(app, session)
    verify_canon(session, project)
    session.commit()
    before = session.query(Character).filter(Character.name == "Decem Hougan").one().current_status
    rollback_state(session, project, 1)
    session.commit()
    after = session.query(Character).filter(Character.name == "Decem Hougan").one().current_status
    assert before == after


def test_preferences_become_writing_instructions(app, session):
    project = _prepare(app, session)
    from app.db.models import Feedback

    session.add(
        Feedback(
            id="f1",
            project_id=project.id,
            node_id="n",
            ratings={"dialogue": 2, "plot_quality": 5, "character_accuracy": 5, "emotional_impact": 5, "worldbuilding": 5, "suspense": 5, "overall": 5},
            comment="Lời thoại còn chung.",
        )
    )
    session.commit()
    notes = preference_instructions(session, project.id)
    assert "lời thoại" in notes.lower() or "thoại" in notes.lower()
    assert "Lời thoại còn chung" in notes
