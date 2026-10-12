from app.db.models import Character
from app.knowledge.schemas import SceneSpec
from app.narrative.validators import disagreement, run_heuristics


def _spec(events: list[str]) -> SceneSpec:
    return SceneSpec(
        scene_id="s",
        viewpoint_character="Ainz Ooal Gown",
        location="Đại Lăng Nazarick",
        timestamp="sau tập 16",
        scene_objective="Một cảnh có đối thoại",
        required_events=events,
        target_word_count=200,
    )


def test_canon_validator_catches_injected_species_error(app, session):
    from app.services.library import import_file
    from pathlib import Path

    notes = Path(__file__).resolve().parents[1] / "data" / "seed" / "volume_16_study_notes.json"
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
    )
    session.commit()
    prose = (
        "Ainz Ooal Gown là một nông dân loài người, không biết phép thuật. "
        "Ainz ra lệnh đình chỉ mọi hoạt động không phục vụ phòng thủ Đại Lăng Nazarick."
    )
    reports = run_heuristics(session, _spec(["Ainz ra lệnh đình chỉ mọi hoạt động không phục vụ phòng thủ Đại Lăng Nazarick."]), prose)
    canon = next(item for item in reports if item["validator"] == "canon")
    assert any(issue["severity"] == "high" for issue in canon["issues"])
    assert disagreement(reports)


def test_clean_scene_has_no_high_severity_issue(app, session):
    from pathlib import Path

    from app.services.library import import_file

    notes = Path(__file__).resolve().parents[1] / "data" / "seed" / "volume_16_study_notes.json"
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
    )
    session.commit()
    event = "Ainz ra lệnh đình chỉ mọi hoạt động không phục vụ phòng thủ Đại Lăng Nazarick."
    prose = f"Ainz Ooal Gown đứng yên.\n\n{event}\n\n— Giữ phòng thủ, — ông nói."
    reports = run_heuristics(session, _spec([event]), prose)
    assert all(issue["severity"] != "high" for report in reports for issue in report["issues"])
    assert session.query(Character).filter(Character.name == "Ainz Ooal Gown").one().race == "Undead Overlord"
