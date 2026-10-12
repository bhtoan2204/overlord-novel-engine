"""Volume, arc, chapter, scene, and beat planning.

The deterministic planner composes an unofficial Volume 17 from unresolved plotlines.
It does not treat fan theories as canon. Uncertainties stay attached as alternatives.
"""

import uuid

from sqlalchemy.orm import Session

from app.core.disclaimer import DISCLAIMER
from app.db.models import OutlineNode, Plotline, Project

from app.narrative.volume17_plan import BLUEPRINT

def _id() -> str:
    return str(uuid.uuid4())


def _available_keys(session: Session) -> dict[str, Plotline]:
    rows = session.query(Plotline).filter(Plotline.timeline == "main", Plotline.current_status != "resolved").all()
    return {row.plotline_key: row for row in rows}


def build_deterministic_tree(session: Session, target_words: int) -> dict:
    available = _available_keys(session)
    if not available:
        raise ValueError("No unresolved main-timeline plotlines are available. Import authorized notes first.")
    scene_blueprints = []
    arcs = []
    previous_chapter = None
    for arc in BLUEPRINT:
        chapters = []
        for chapter in arc["chapters"]:
            if not all(key in available for key in chapter["requires"]):
                continue
            uncertainties = []
            for key in chapter["requires"]:
                uncertainties.extend(available[key].uncertainties or [])
            caused_by = previous_chapter
            chapters.append({**chapter, "uncertainties": uncertainties, "caused_by": caused_by})
            previous_chapter = chapter["title"]
            scene_blueprints.extend(chapter["scenes"])
        if chapters:
            arcs.append({"title": arc["arc"], "chapters": chapters})
    if not arcs:
        raise ValueError("Plotlines do not cover any Volume 17 chapter. Import the study notes or add the missing keys.")
    count = max(1, len(scene_blueprints))
    if target_words >= 40000:
        per_scene = max(900, min(1200, target_words // count))
    else:
        per_scene = max(200, min(1200, target_words // count))
    alternatives = [
        "Nhánh bị loại: dừng sau một đợt trinh sát và để Thần quyền quốc Slane còn nguyên chính quyền. Bản này kết thúc chiến dịch trong tập 17.",
        "Nhánh bị loại: xóa mọi thành phố trong một đêm. Bản này đánh sụp chính quyền trung ương, không biến dân thường thành mục tiêu.",
    ]
    for row in available.values():
        for item in row.uncertainties or []:
            if item not in alternatives:
                alternatives.append(item)
    return {
        "title": "Overlord — Tập 17 (fanfiction không chính thức)",
        "premise": (
            "Ngay sau Tập 16, Ainz đã biết Thần quyền quốc Slane đứng sau việc Shalltear bị điều khiển "
            "và đã ra lệnh chuẩn bị tiêu diệt họ. Bản fanfiction này đưa chiến dịch đến hồi kết: "
            "chính quyền trung ương sụp trong tập 17. Sức căng nằm ở Bảo vật thế giới, tình báo thiếu, "
            "động cơ lệch nhau và cái giá chính trị, không nằm ở việc kẻ địch bỗng mạnh ngang Nazarick."
        ),
        "disclaimer": DISCLAIMER,
        "alternatives": alternatives,
        "target_words": per_scene * len(scene_blueprints),
        "words_per_scene": per_scene,
        "arcs": arcs,
    }


def replace_outline(session: Session, project: Project, tree: dict) -> None:
    session.query(OutlineNode).filter(OutlineNode.project_id == project.id).delete()
    volume_id = _id()
    session.add(
        OutlineNode(
            id=volume_id,
            project_id=project.id,
            parent_id=None,
            level="volume",
            ordinal=17,
            title=tree["title"],
            summary=tree["premise"],
            payload={
                "disclaimer": tree["disclaimer"],
                "alternatives": tree["alternatives"],
                "target_words": tree["target_words"],
                "selected_branch": "theocracy-collapse",
            },
        )
    )
    for arc_index, arc in enumerate(tree["arcs"], start=1):
        arc_id = _id()
        session.add(
            OutlineNode(
                id=arc_id,
                project_id=project.id,
                parent_id=volume_id,
                level="arc",
                ordinal=arc_index,
                title=arc["title"],
                summary=arc["chapters"][0]["summary"],
                payload={"caused_by": arc["chapters"][0].get("caused_by")},
            )
        )
        for chapter_index, chapter in enumerate(arc["chapters"], start=1):
            chapter_id = _id()
            session.add(
                OutlineNode(
                    id=chapter_id,
                    project_id=project.id,
                    parent_id=arc_id,
                    level="chapter",
                    ordinal=chapter_index,
                    title=chapter["title"],
                    summary=chapter["summary"],
                    payload={
                        "kind": chapter["kind"],
                        "caused_by": chapter.get("caused_by"),
                        "alternatives": chapter.get("uncertainties") or [],
                        "plotlines": chapter["requires"],
                    },
                )
            )
            for scene_index, scene in enumerate(chapter["scenes"], start=1):
                scene_id = _id()
                session.add(
                    OutlineNode(
                        id=scene_id,
                        project_id=project.id,
                        parent_id=chapter_id,
                        level="scene",
                        ordinal=scene_index,
                        title=scene["title"],
                        summary=scene["objective"],
                        payload={
                            "viewpoint_character": scene["viewpoint"],
                            "location": scene["location"],
                            "participating_characters": scene["participants"],
                            "required_events": scene["events"],
                            "emotional_tone": scene["tone"],
                            "scene_objective": scene["objective"],
                            "desired_outcome": scene["outcome"],
                            "target_word_count": tree["words_per_scene"],
                            "caused_by": chapter.get("caused_by"),
                        },
                    )
                )
                for beat_index, event in enumerate(scene["events"], start=1):
                    session.add(
                        OutlineNode(
                            id=_id(),
                            project_id=project.id,
                            parent_id=scene_id,
                            level="beat",
                            ordinal=beat_index,
                            title=f"Nhịp {beat_index}",
                            summary=event,
                            payload={"required": True},
                        )
                    )
