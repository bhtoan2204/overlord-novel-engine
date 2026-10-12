"""Volume, arc, chapter, scene, and beat planning.

The deterministic planner composes an unofficial Volume 17 from unresolved plotlines.
It does not treat fan theories as canon. Uncertainties stay attached as alternatives.
"""

import uuid

from sqlalchemy.orm import Session

from app.core.disclaimer import DISCLAIMER
from app.db.models import OutlineNode, Plotline, PreservedDraft, Project, SceneDraft
from app.narrative.volume17_budget import budget_audit, planned_volume

def _id() -> str:
    return str(uuid.uuid4())


def _available_keys(session: Session) -> dict[str, Plotline]:
    rows = session.query(Plotline).filter(Plotline.timeline == "main", Plotline.current_status != "resolved").all()
    return {row.plotline_key: row for row in rows}


def build_deterministic_tree(session: Session, target_words: int) -> dict:
    available = _available_keys(session)
    if not available:
        raise ValueError("No unresolved main-timeline plotlines are available. Import authorized notes first.")
    plan = planned_volume()
    arcs = []
    previous_chapter = None
    for arc in plan["arcs"]:
        chapters = []
        for chapter in arc["chapters"]:
            if not all(key in available for key in chapter["requires"]):
                continue
            uncertainties = []
            for key in chapter["requires"]:
                uncertainties.extend(available[key].uncertainties or [])
            chapters.append({**chapter, "uncertainties": uncertainties, "caused_by": previous_chapter})
            previous_chapter = chapter["title"]
        if chapters:
            arcs.append({"title": arc["title"], "chapters": chapters})
    if not arcs:
        raise ValueError("Plotlines do not cover any Volume 17 chapter. Import the study notes or add the missing keys.")
    alternatives = [
        "Nhánh bị loại: dừng sau một đợt trinh sát và để Thần quyền quốc Slane còn nguyên chính quyền. Bản này kết thúc chiến dịch trong tập 17.",
        "Nhánh bị loại: xóa mọi thành phố trong một đêm. Bản này đánh sụp chính quyền trung ương, không biến dân thường thành mục tiêu.",
    ]
    for row in available.values():
        for item in row.uncertainties or []:
            if item not in alternatives:
                alternatives.append(item)
    tree = {
        "title": "Overlord — Tập 17 (fanfiction không chính thức)",
        "premise": (
            "Ngay sau Tập 16, Ainz đã biết Thần quyền quốc Slane đứng sau việc Shalltear bị điều khiển "
            "và đã ra lệnh chuẩn bị tiêu diệt họ. Bản fanfiction này đưa chiến dịch đến hồi kết: "
            "chính quyền trung ương sụp trong tập 17. Sức căng nằm ở Bảo vật thế giới, tình báo thiếu, "
            "động cơ lệch nhau và cái giá chính trị, không nằm ở việc kẻ địch bỗng mạnh ngang Nazarick."
        ),
        "disclaimer": DISCLAIMER,
        "alternatives": alternatives,
        "target_words": plan["target_words"],
        "requested_words": target_words,
        "arcs": arcs,
    }
    tree["budget_problems"] = budget_audit(tree)
    if target_words != plan["target_words"]:
        tree["budget_problems"].append(
            f"Settings ask for {target_words} words; the reconciled plan allocates {plan['target_words']}."
        )
    return tree


def _archive_selected_drafts(session: Session, project: Project) -> None:
    drafts = session.query(SceneDraft).filter(SceneDraft.project_id == project.id, SceneDraft.selected.is_(True)).all()
    for draft in drafts:
        node = session.get(OutlineNode, draft.node_id)
        session.add(
            PreservedDraft(
                id=_id(),
                project_id=project.id,
                original_node_id=draft.node_id,
                title=node.title if node else "",
                prose=draft.prose,
                word_count=int((draft.spec or {}).get("word_count") or len(draft.prose.split())),
            )
        )
    session.flush()


def replace_outline(session: Session, project: Project, tree: dict) -> None:
    _archive_selected_drafts(session, project)
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
                "budget_problems": tree.get("budget_problems") or [],
                "selected_branch": "theocracy-collapse",
            },
            target_words=int(tree["target_words"]),
            completion_status="PLANNED",
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
                    target_words=int(chapter["target_words"]),
                    completion_status="PLANNED",
                )
            )
            for part_index, part in enumerate(chapter["parts"], start=1):
                part_id = _id()
                session.add(
                    OutlineNode(
                        id=part_id,
                        project_id=project.id,
                        parent_id=chapter_id,
                        level="part",
                        ordinal=part_index,
                        title=part["title"],
                        summary=part["conflict"],
                        payload={
                            "viewpoint": part["viewpoint"],
                            "location": part["location"],
                            "outcome": part["outcome"],
                            "short_transition": part.get("short_transition", False),
                        },
                        target_words=int(part["target_words"]),
                        completion_status="PLANNED",
                    )
                )
                for scene_index, scene in enumerate(part["scenes"], start=1):
                    scene_id = _id()
                    session.add(
                        OutlineNode(
                            id=scene_id,
                            project_id=project.id,
                            parent_id=part_id,
                            level="scene",
                            ordinal=scene_index,
                            title=scene["title"],
                            summary=scene["objective"],
                            payload={
                                "viewpoint_character": scene["viewpoint"],
                                "location": scene["location"],
                                "required_events": scene["events"],
                                "scene_objective": scene["objective"],
                                "desired_outcome": scene["outcome"],
                                "target_word_count": scene["target_words"],
                            },
                            target_words=int(scene["target_words"]),
                            completion_status="PLANNED",
                        )
                    )
                    for beat_index, beat in enumerate(scene["beats"], start=1):
                        session.add(
                            OutlineNode(
                                id=_id(),
                                project_id=project.id,
                                parent_id=scene_id,
                                level="beat",
                                ordinal=beat_index,
                                title=beat["title"],
                                summary=beat["action"],
                                payload={
                                    "action": beat["action"],
                                    "purpose": beat["purpose"],
                                    "new_information": beat["new_information"],
                                    "objective": beat["objective"],
                                    "required": True,
                                },
                                target_words=int(beat["target_words"]),
                                completion_status="PLANNED",
                            )
                        )


def migrate_legacy_scenes(session: Session, project: Project) -> int:
    """Put chapter-level scenes under a part. Draft rows stay on the same scene id."""
    moved = 0
    chapters = session.query(OutlineNode).filter(OutlineNode.project_id == project.id, OutlineNode.level == "chapter").all()
    for chapter in chapters:
        scenes = (
            session.query(OutlineNode)
            .filter(OutlineNode.parent_id == chapter.id, OutlineNode.level == "scene")
            .order_by(OutlineNode.ordinal)
            .all()
        )
        parts = session.query(OutlineNode).filter(OutlineNode.parent_id == chapter.id, OutlineNode.level == "part").count()
        if not scenes or parts:
            continue
        part_id = _id()
        session.add(
            OutlineNode(
                id=part_id,
                project_id=project.id,
                parent_id=chapter.id,
                level="part",
                ordinal=1,
                title=f"{chapter.title} — phần đã có",
                summary=chapter.summary,
                target_words=sum(scene.target_words or 0 for scene in scenes),
                completion_status="PLANNED",
            )
        )
        for index, scene in enumerate(scenes, start=1):
            scene.parent_id = part_id
            scene.ordinal = index
            moved += 1
    session.flush()
    return moved
