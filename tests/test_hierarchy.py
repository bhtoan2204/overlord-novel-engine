import uuid

from app.core.text import word_count
from app.db.models import OutlineNode, PreservedDraft, Project, ProseChunk, SceneDraft
from app.inference.base import GenerationResult, GenerationSettings
from app.narrative.completion import refresh_rollup
from app.narrative.export import part_text
from app.narrative.longform import generate_next_chunk
from app.narrative.planner import build_deterministic_tree, migrate_legacy_scenes, replace_outline
from app.narrative.volume17_budget import budget_audit, planned_volume


def test_word_budget_sums_and_reaches_the_volume_target():
    tree = planned_volume()
    assert budget_audit(tree) == []
    assert tree["target_words"] == 200_000
    chapters = [chapter for arc in tree["arcs"] for chapter in arc["chapters"]]
    assert sum(chapter["target_words"] for chapter in chapters) == 200_000
    assert any(chapter["target_words"] >= 20_000 for chapter in chapters)
    assert any(part["target_words"] >= 10_000 for chapter in chapters for part in chapter["parts"])
    assert {chapter["kind"] for chapter in chapters} >= {"prologue", "chapter", "interlude", "epilogue"}


def _node(session, project, parent, level, ordinal, title, words=0, kind=None):
    row = OutlineNode(
        id=str(uuid.uuid4()),
        project_id=project.id,
        parent_id=parent,
        level=level,
        ordinal=ordinal,
        title=title,
        target_words=words,
        completion_status="PLANNED",
        payload={"kind": kind} if kind else {},
    )
    session.add(row)
    session.flush()
    return row


class _Words:
    name = "fake"

    def __init__(self, text, finish="stop"):
        self.text = text
        self.finish = finish
        self.calls = 0

    def generate(self, messages, settings: GenerationSettings) -> GenerationResult:
        self.calls += 1
        body = self.text if isinstance(self.text, str) else self.text[self.calls - 1]
        return GenerationResult(text=body, finish_reason=self.finish, prompt_tokens=20, completion_tokens=30)


def test_migration_keeps_the_draft_on_the_same_scene(app, session):
    project = Project(id=str(uuid.uuid4()), title="cũ", disclaimer="fanfiction", workflow_state="OUTLINE_APPROVED")
    session.add(project)
    session.flush()
    chapter = _node(session, project, None, "chapter", 1, "Chương cũ")
    scene = _node(session, project, chapter.id, "scene", 1, "Cảnh cũ", 40)
    draft = SceneDraft(
        id=str(uuid.uuid4()),
        project_id=project.id,
        node_id=scene.id,
        iteration=1,
        prose="Văn đã duyệt không được xóa.",
        spec={"word_count": 6},
        selected=True,
    )
    session.add(draft)
    session.commit()
    assert migrate_legacy_scenes(session, project) == 1
    session.commit()
    session.refresh(scene)
    assert session.get(OutlineNode, scene.parent_id).level == "part"
    assert session.get(SceneDraft, draft.id).prose == "Văn đã duyệt không được xóa."


def test_chunk_resume_does_not_duplicate_and_repetition_does_not_finish(app, session, settings):
    project = Project(id=str(uuid.uuid4()), title="thử", disclaimer="fanfiction", workflow_state="OUTLINE_APPROVED", config={})
    session.add(project)
    session.flush()
    volume = _node(session, project, None, "volume", 17, "Tập", 400)
    arc = _node(session, project, volume.id, "arc", 1, "Arc")
    chapter = _node(session, project, arc.id, "chapter", 1, "Chương", 400, kind="chapter")
    part = _node(session, project, chapter.id, "part", 1, "Phần", 500)
    scene = _node(session, project, part.id, "scene", 1, "Cảnh", 500)
    beat = _node(session, project, scene.id, "beat", 1, "Nhịp", 500)
    beat.payload = {"action": "hành động riêng một", "purpose": "mở", "new_information": "tin một", "objective": "xong nhịp"}
    session.commit()
    words = " ".join(f"tu{i}" for i in range(200))
    backend = _Words(words)
    first = generate_next_chunk(session, project, settings, backend, context_tokens=4096)
    session.commit()
    assert first["status"] == "accepted"
    again = generate_next_chunk(session, project, settings, _Words(words), context_tokens=4096)
    session.commit()
    assert again["status"] == "rejected"
    accepted = session.query(ProseChunk).filter(ProseChunk.status == "ACCEPTED").all()
    assert len(accepted) == 1
    assert session.get(OutlineNode, part.id).completion_status != "COMPLETED"


def test_chapter_and_volume_do_not_complete_early(app, session, settings):
    project = Project(id=str(uuid.uuid4()), title="thử", disclaimer="fanfiction", workflow_state="OUTLINE_APPROVED", config={})
    session.add(project)
    session.flush()
    volume = _node(session, project, None, "volume", 17, "Tập", 400)
    arc = _node(session, project, volume.id, "arc", 1, "Arc")
    chapter = _node(session, project, arc.id, "chapter", 1, "Chương", 400, kind="chapter")
    part = _node(session, project, chapter.id, "part", 1, "Phần một", 200)
    other = _node(session, project, chapter.id, "part", 2, "Phần hai", 200)
    scene = _node(session, project, part.id, "scene", 1, "Cảnh", 200)
    beat = _node(session, project, scene.id, "beat", 1, "Nhịp", 200)
    beat.payload = {"action": "hành động riêng hai", "purpose": "mở", "new_information": "tin hai", "objective": "xong"}
    session.commit()
    text = " ".join(f"moi{i}" for i in range(220))
    generate_next_chunk(session, project, settings, _Words(text), context_tokens=4096)
    session.commit()
    assert session.get(OutlineNode, part.id).completion_status == "COMPLETED"
    assert session.get(OutlineNode, chapter.id).completion_status != "COMPLETED"
    assert session.get(OutlineNode, volume.id).completion_status != "COMPLETED"
    assert session.get(OutlineNode, other.id).completion_status == "PLANNED"


def test_truncation_and_context_overflow_do_not_pass(app, session, settings):
    project = Project(id=str(uuid.uuid4()), title="thử", disclaimer="fanfiction", workflow_state="OUTLINE_APPROVED", config={})
    session.add(project)
    session.flush()
    volume = _node(session, project, None, "volume", 17, "Tập")
    arc = _node(session, project, volume.id, "arc", 1, "Arc")
    chapter = _node(session, project, arc.id, "chapter", 1, "Chương", kind="chapter")
    part = _node(session, project, chapter.id, "part", 1, "Phần", 200)
    scene = _node(session, project, part.id, "scene", 1, "Cảnh", 200)
    beat = _node(session, project, scene.id, "beat", 1, "Nhịp", 200)
    beat.payload = {"action": "việc", "purpose": "mở", "new_information": "tin", "objective": "xong"}
    session.commit()
    cut = generate_next_chunk(session, project, settings, _Words("câu bị cắt giữa chừng", "truncation"), context_tokens=4096)
    session.commit()
    assert cut["status"] == "rejected"
    assert session.query(ProseChunk).filter(ProseChunk.status == "ACCEPTED").count() == 0
    paused = generate_next_chunk(session, project, settings, _Words("không được gọi"), context_tokens=32)
    assert paused["status"] == "paused"


def test_failed_beat_keeps_the_committed_chunk(app, session, settings):
    project = Project(id=str(uuid.uuid4()), title="thử", disclaimer="fanfiction", workflow_state="OUTLINE_APPROVED", config={})
    session.add(project)
    session.flush()
    volume = _node(session, project, None, "volume", 17, "Tập")
    arc = _node(session, project, volume.id, "arc", 1, "Arc")
    chapter = _node(session, project, arc.id, "chapter", 1, "Chương", kind="chapter")
    part = _node(session, project, chapter.id, "part", 1, "Phần", 500)
    scene = _node(session, project, part.id, "scene", 1, "Cảnh", 500)
    beat = _node(session, project, scene.id, "beat", 1, "Nhịp", 500)
    beat.payload = {"action": "việc dài", "purpose": "mở", "new_information": "tin dài", "objective": "chưa xong"}
    session.commit()
    first = " ".join(f"giu{i}" for i in range(180))
    generate_next_chunk(session, project, settings, _Words(first), context_tokens=4096)
    session.commit()
    kept = session.query(ProseChunk).filter(ProseChunk.status == "ACCEPTED").one().prose

    class Boom:
        name = "fake"

        def generate(self, messages, settings):
            raise RuntimeError("backend failed")

    try:
        generate_next_chunk(session, project, settings, Boom(), context_tokens=4096)
    except RuntimeError:
        pass
    assert session.query(ProseChunk).filter(ProseChunk.status == "ACCEPTED").one().prose == kept


def test_part_export_word_count_matches_chunks(app, session):
    project = Project(id=str(uuid.uuid4()), title="thử", disclaimer="fanfiction", workflow_state="OUTLINE_CREATED", config={})
    session.add(project)
    session.flush()
    part = _node(session, project, None, "part", 1, "Phần dài", 10000)
    scene = _node(session, project, part.id, "scene", 1, "Cảnh", 10000)
    beat = _node(session, project, scene.id, "beat", 1, "Nhịp", 250)
    prose = " ".join(f"dai{i}" for i in range(10001))
    session.add(
        ProseChunk(
            id=str(uuid.uuid4()),
            project_id=project.id,
            beat_id=beat.id,
            scene_id=scene.id,
            part_id=part.id,
            ordinal=1,
            prose=prose,
            word_count=word_count(prose),
            status="ACCEPTED",
        )
    )
    session.commit()
    assert word_count(part_text(session, part.id)) == 10001
    assert word_count(part_text(session, part.id)) > 10_000


def test_outline_replacement_archives_selected_prose(app, session):
    from app.core.disclaimer import DISCLAIMER
    from app.narrative.pipeline import create_project
    from app.services.library import import_file
    from pathlib import Path

    project = create_project(session, "Tập 17", DISCLAIMER)
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
        project=project,
    )
    tree = build_deterministic_tree(session, 200_000)
    replace_outline(session, project, tree)
    scene = session.query(OutlineNode).filter(OutlineNode.level == "scene").first()
    session.add(
        SceneDraft(
            id=str(uuid.uuid4()),
            project_id=project.id,
            node_id=scene.id,
            iteration=1,
            prose="Bản đã duyệt cần được giữ khi thay dàn ý.",
            spec={},
            selected=True,
        )
    )
    session.commit()
    replace_outline(session, project, tree)
    session.commit()
    saved = session.query(PreservedDraft).one()
    assert "Bản đã duyệt" in saved.prose
    assert session.query(OutlineNode).filter(OutlineNode.level == "part").count() > 0


def test_part_above_the_range_is_not_complete(app, session):
    project = Project(id=str(uuid.uuid4()), title="thử", disclaimer="fanfiction", workflow_state="OUTLINE_APPROVED", config={})
    session.add(project)
    session.flush()
    volume = _node(session, project, None, "volume", 17, "Tập", 400)
    arc = _node(session, project, volume.id, "arc", 1, "Arc")
    chapter = _node(session, project, arc.id, "chapter", 1, "Chương", 400, kind="chapter")
    part = _node(session, project, chapter.id, "part", 1, "Phần", 200)
    scene = _node(session, project, part.id, "scene", 1, "Cảnh", 200)
    beat = _node(session, project, scene.id, "beat", 1, "Nhịp", 200)
    for row in (scene, beat):
        row.completion_status = "COMPLETED"
    part.actual_words = 300
    scene.actual_words = 300
    session.commit()
    refresh_rollup(session, project)
    assert session.get(OutlineNode, part.id).completion_status == "NEEDS_REVIEW"
    assert session.get(OutlineNode, volume.id).completion_status != "COMPLETED"


def test_missing_source_text_blocks_volume_completion(app, session):
    project = Project(id=str(uuid.uuid4()), title="thử", disclaimer="fanfiction", workflow_state="OUTLINE_APPROVED", config={})
    session.add(project)
    session.flush()
    volume = _node(session, project, None, "volume", 17, "Tập", 600)
    arc = _node(session, project, volume.id, "arc", 1, "Arc")
    for ordinal, kind, title in ((1, "prologue", "Mở"), (2, "chapter", "Giữa"), (3, "epilogue", "Kết")):
        chapter = _node(session, project, arc.id, "chapter", ordinal, title, 200, kind=kind)
        part = _node(session, project, chapter.id, "part", 1, title + " phần", 200)
        scene = _node(session, project, part.id, "scene", 1, title + " cảnh", 200)
        beat = _node(session, project, scene.id, "beat", 1, title + " nhịp", 200)
        for row in (chapter, part, scene, beat):
            row.completion_status = "COMPLETED"
            row.actual_words = 200
    session.commit()
    refresh_rollup(session, project)
    assert session.get(OutlineNode, volume.id).completion_status == "NEEDS_EXPANSION"
    assert project.workflow_state != "VOLUME_COMPLETED"


def test_missing_next_scene_does_not_finish_the_volume(app, session, settings):
    from app.narrative.pipeline import generate_scene

    project = Project(id=str(uuid.uuid4()), title="thử", disclaimer="fanfiction", workflow_state="OUTLINE_APPROVED", config={})
    session.add(project)
    session.flush()
    _node(session, project, None, "volume", 17, "Tập", 200_000)
    session.commit()
    result = generate_scene(session, project, settings, _Words("không"), app.state.embedder, app.state.index)
    assert result["status"] == "incomplete"
    assert project.workflow_state != "VOLUME_COMPLETED"
    refresh_rollup(session, project)
    assert project.workflow_state != "VOLUME_COMPLETED"
