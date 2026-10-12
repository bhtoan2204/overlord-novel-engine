"""Heuristic validators. They score separate dimensions and keep disagreements intact."""

import re

from sqlalchemy.orm import Session

from app.core.text import word_count
from app.db.models import Assertion, Character
from app.knowledge.schemas import SceneSpec

HUMAN_CLAIMS = ("nông dân loài người", "là một con người bình thường", "không biết phép thuật", "chỉ là nông dân")
UNDEAD_MARKERS = ("undead", "xác sống", "overlord", "lich", "vampire", "ma cà rồng")


def _score(issues: list[dict], key: str) -> dict[str, int]:
    high = any(issue["severity"] == "high" for issue in issues)
    medium = any(issue["severity"] == "medium" for issue in issues)
    value = 2 if high else 3 if medium else 5
    return {key: value}


def validate_canon(session: Session, spec: SceneSpec, prose: str) -> dict:
    issues = []
    lowered = prose.lower()
    characters = session.query(Character).all()
    for character in characters:
        race = (character.race or "").lower()
        name = character.name
        if name.lower() not in lowered:
            continue
        if any(marker in race for marker in UNDEAD_MARKERS) and any(claim in lowered for claim in HUMAN_CLAIMS):
            issues.append(
                {
                    "severity": "high",
                    "message": f"{name} bị viết như một con người thường, trái với hồ sơ chủng loài ({character.race}).",
                    "evidence": character.evidence_source_id or character.current_status,
                    "character": name,
                }
            )
        if character.alive is False and re.search(rf"{re.escape(name)}.{{0,40}}(nói|bước|cười|ra lệnh)", prose, re.I):
            issues.append(
                {
                    "severity": "high",
                    "message": f"{name} đang hành động dù hồ sơ ghi nhận người này đã chết.",
                    "evidence": character.current_status,
                    "character": name,
                }
            )
    for phrase in spec.prohibited_contradictions:
        if phrase and phrase.lower() in lowered:
            issues.append(
                {
                    "severity": "high",
                    "message": f"Bản thảo chứa mâu thuẫn đã bị cấm: {phrase}",
                    "evidence": phrase,
                    "character": spec.viewpoint_character,
                }
            )
    for assertion in session.query(Assertion).filter(Assertion.timeline == "alternate").all():
        if len(assertion.value) > 24 and assertion.value.lower() in lowered:
            issues.append(
                {
                    "severity": "high",
                    "message": "Một sự kiện vũ trụ song song bị viết như chính sử.",
                    "evidence": assertion.evidence_source_id or assertion.value,
                    "character": assertion.subject_name,
                }
            )
    return {
        "validator": "canon",
        "scores": _score(issues, "consistency"),
        "issues": issues,
        "recommendations": [issue["message"] for issue in issues],
    }


def validate_character(session: Session, spec: SceneSpec, prose: str) -> dict:
    issues = []
    character = session.query(Character).filter(Character.name == spec.viewpoint_character).one_or_none()
    if character:
        secret = (character.knowledge_state or {}).get("does_not_know") or []
        for item in secret:
            if item and len(item) > 12 and item.lower() in prose.lower() and spec.viewpoint_character.lower() in prose.lower():
                issues.append(
                    {
                        "severity": "high",
                        "message": f"{character.name} bộc lộ điều hồ sơ ghi là nhân vật này không biết: {item}",
                        "evidence": character.evidence_source_id or "",
                        "character": character.name,
                    }
                )
        if character.personality and "bỗng nhiên hóa điên" in prose.lower():
            issues.append(
                {
                    "severity": "medium",
                    "message": "Nhân vật đổi tính cách không có nguyên nhân.",
                    "evidence": character.personality,
                    "character": character.name,
                }
            )
    return {
        "validator": "character",
        "scores": _score(issues, "consistency"),
        "issues": issues,
        "recommendations": ["Giữ đúng những gì nhân vật điểm nhìn được phép biết."] if issues else [],
    }


def validate_plot(spec: SceneSpec, prose: str) -> dict:
    issues = []
    lowered = prose.lower()
    for event in spec.required_events:
        if event.lower() not in lowered:
            issues.append(
                {
                    "severity": "high",
                    "message": f"Thiếu sự kiện bắt buộc: {event}",
                    "evidence": event,
                    "character": "",
                }
            )
    if lowered.count("tình cờ") >= 3:
        issues.append(
            {
                "severity": "medium",
                "message": "Tình tiết dựa vào quá nhiều sự trùng hợp.",
                "evidence": "tình cờ",
                "character": "",
            }
        )
    count = word_count(prose)
    if spec.target_word_count >= 600 and count < int(spec.target_word_count * 0.6):
        issues.append(
            {
                "severity": "high",
                "message": "Cảnh chưa đủ dài so với kế hoạch và không được xem là đã xong.",
                "evidence": f"{count}/{spec.target_word_count}",
                "character": "",
            }
        )
    elif spec.target_word_count and count < int(spec.target_word_count * 0.25):
        issues.append(
            {
                "severity": "medium",
                "message": "Cảnh ngắn hơn nhiều so với nhịp đã định.",
                "evidence": f"{count}/{spec.target_word_count}",
                "character": "",
            }
        )
    paragraphs = [" ".join(part.split()) for part in prose.split("\n\n") if len(part.split()) > 20]
    if len(paragraphs) != len(set(paragraphs)):
        issues.append(
            {
                "severity": "medium",
                "message": "Có đoạn văn bị lặp nguyên văn.",
                "evidence": "duplicate paragraph",
                "character": "",
            }
        )
    return {
        "validator": "plot",
        "scores": _score(issues, "causality"),
        "issues": issues,
        "recommendations": [issue["message"] for issue in issues],
    }


def validate_language(spec: SceneSpec, prose: str) -> dict:
    issues = []
    sentences = [part.strip() for part in re.split(r"[.!?。]\s+", prose) if part.strip()]
    seen = {}
    for sentence in sentences:
        key = sentence.lower()
        seen[key] = seen.get(key, 0) + 1
    repeated = [sentence for sentence, count in seen.items() if count >= 3 and len(sentence) > 40]
    if repeated:
        issues.append(
            {
                "severity": "medium",
                "message": "Có câu lặp lại nhiều lần.",
                "evidence": repeated[0][:160],
                "character": "",
            }
        )
    if "đối thoại" in spec.scene_objective.lower() and not any(mark in prose for mark in ("—", "「", "“", '"')):
        issues.append(
            {
                "severity": "medium",
                "message": "Cảnh cần đối thoại nhưng chưa có lời thoại.",
                "evidence": spec.scene_objective,
                "character": spec.viewpoint_character,
            }
        )
    return {
        "validator": "language",
        "scores": _score(issues, "language"),
        "issues": issues,
        "recommendations": [issue["message"] for issue in issues],
    }


def validate_strategy(spec: SceneSpec, prose: str) -> dict:
    issues = []
    lowered = prose.lower()
    for phrase in ("thức tỉnh sức mạnh mới", "mạnh gấp mười lần", "phép mới chưa từng có"):
        if phrase in lowered:
            issues.append(
                {
                    "severity": "high",
                    "message": "Sức mạnh tăng mà không có cơ chế đã biết.",
                    "evidence": phrase,
                    "character": spec.viewpoint_character,
                }
            )
    return {"validator": "strategy", "scores": _score(issues, "causality"), "issues": issues, "recommendations": [i["message"] for i in issues]}


def validate_narrative(spec: SceneSpec, prose: str) -> dict:
    issues = []
    if spec.desired_outcome and len(spec.desired_outcome) > 20 and spec.desired_outcome.lower() not in prose.lower() and word_count(prose) > 800:
        issues.append(
            {
                "severity": "medium",
                "message": "Cảnh chưa chạm kết cục đã định.",
                "evidence": spec.desired_outcome,
                "character": "",
            }
        )
    return {"validator": "narrative", "scores": {"pacing": 3 if issues else 5}, "issues": issues, "recommendations": [i["message"] for i in issues]}


def validate_continuity(spec: SceneSpec, prose: str) -> dict:
    issues = []
    if spec.previous_scene_summary and "như chưa có chuyện gì" in prose.lower():
        issues.append(
            {
                "severity": "high",
                "message": "Cảnh xóa hệ quả của cảnh trước.",
                "evidence": spec.previous_scene_summary[:180],
                "character": "",
            }
        )
    return {"validator": "continuity", "scores": _score(issues, "consistency"), "issues": issues, "recommendations": [i["message"] for i in issues]}


def run_heuristics(session: Session, spec: SceneSpec, prose: str) -> list[dict]:
    return [
        validate_canon(session, spec, prose),
        validate_character(session, spec, prose),
        validate_plot(spec, prose),
        validate_language(spec, prose),
        validate_strategy(spec, prose),
        validate_narrative(spec, prose),
        validate_continuity(spec, prose),
    ]


def disagreement(reports: list[dict]) -> bool:
    values = []
    for report in reports:
        if "consistency" in report["scores"]:
            values.append(report["scores"]["consistency"])
    return bool(values) and max(values) - min(values) >= 3


def blocking(reports: list[dict]) -> list[dict]:
    found = []
    for report in reports:
        for issue in report["issues"]:
            if issue["severity"] == "high":
                found.append(issue)
    return found
