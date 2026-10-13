import uuid
from pathlib import Path

from app.db.models import OutlineNode, Project, ProseChunk
from app.inference.base import GenerationResult, GenerationSettings
from app.narrative.coordinator import run_campaign


def _node(session, project, parent, level, ordinal, title, words=0, kind=None, status="PLANNED"):
    row = OutlineNode(
        id=str(uuid.uuid4()),
        project_id=project.id,
        parent_id=parent,
        level=level,
        ordinal=ordinal,
        title=title,
        summary=title,
        target_words=words,
        completion_status=status,
        payload={"kind": kind} if kind else {},
    )
    session.add(row)
    session.flush()
    return row


class _Words:
    name = "fake"

    def generate(self, messages, settings: GenerationSettings) -> GenerationResult:
        text = " ".join(f"moi{i}" for i in range(30))
        return GenerationResult(text=text, finish_reason="stop", prompt_tokens=10, completion_tokens=30)


def test_repair_keeps_the_original_and_moves_to_the_next_part(app, session, settings, tmp_path: Path):
    project = Project(id=str(uuid.uuid4()), title="Tập", disclaimer="fanfiction", workflow_state="OUTLINE_APPROVED", config={})
    session.add(project)
    session.flush()
    volume = _node(session, project, None, "volume", 17, "Tập", 40)
    arc = _node(session, project, volume.id, "arc", 1, "Arc")
    chapter = _node(session, project, arc.id, "chapter", 1, "Chương", 40, kind="chapter")
    part = _node(session, project, chapter.id, "part", 1, "Phần một", 5, status="NEEDS_REVIEW")
    part.summary = "Ainz giữ lệnh tiêu diệt"
    scene = _node(session, project, part.id, "scene", 1, "Cảnh", 5, status="COMPLETED")
    beat = _node(session, project, scene.id, "beat", 1, "Nhịp", 5, status="COMPLETED")
    session.add(
        ProseChunk(
            id=str(uuid.uuid4()),
            project_id=project.id,
            beat_id=beat.id,
            scene_id=scene.id,
            part_id=part.id,
            ordinal=1,
            prose="Ainz giữ lệnh tiêu diệt. Dark Lord cầm chuôi kiếm.",
            word_count=8,
            status="ACCEPTED",
        )
    )
    part2 = _node(session, project, chapter.id, "part", 2, "Phần hai", 30)
    scene2 = _node(session, project, part2.id, "scene", 1, "Cảnh hai", 30)
    beat2 = _node(session, project, scene2.id, "beat", 1, "Nhịp hai", 30)
    beat2.payload = {"action": "việc mới", "purpose": "mở", "new_information": "tin", "objective": "xong"}
    session.commit()
    result = run_campaign(
        session,
        project,
        settings,
        _Words(),
        until_complete=True,
        repair_reviews=True,
        export_on_completion=False,
        progress_path=tmp_path / "progress.json",
        max_slices=3,
    )
    session.expire_all()
    assert session.get(OutlineNode, part.id).completion_status == "COMPLETED"
    assert session.query(ProseChunk).filter(ProseChunk.status == "SUPERSEDED").count() == 1
    assert session.query(ProseChunk).filter(ProseChunk.part_id == part2.id, ProseChunk.status == "ACCEPTED").count() >= 1
    assert "Dark Lord" not in session.query(ProseChunk).filter(ProseChunk.part_id == part.id, ProseChunk.status == "ACCEPTED").one().prose
    assert result["parts_completed"] >= 1
    assert (tmp_path / "progress.json").exists()
