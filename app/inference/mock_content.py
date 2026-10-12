"""Fallback prose and JSON used when no scripted response is queued and no GPU model is loaded."""

import json
import re

from app.core.text import extract_json_blob
from app.inference.base import GenerationSettings


def _payload(messages: list[dict]) -> dict:
    for message in reversed(messages):
        if message.get("role") != "user":
            continue
        try:
            data = json.loads(extract_json_blob(message["content"]))
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and any(key in data for key in ("spec", "text", "prose", "premise", "task")):
            return data
    raw = messages[-1]["content"] if messages else ""
    return {"text": raw}


def respond(messages: list[dict], settings: GenerationSettings) -> str:
    payload = _payload(messages)
    task = settings.task
    if task == "extract":
        return json.dumps(_extract(payload), ensure_ascii=False)
    if task == "plan":
        return json.dumps(_plan(payload), ensure_ascii=False)
    if task == "validate":
        return json.dumps(_validate(payload), ensure_ascii=False)
    if task in {"write", "revise"}:
        return json.dumps(_write(payload, revise=task == "revise"), ensure_ascii=False)
    return json.dumps({"note": "unsupported task", "task": task}, ensure_ascii=False)


def _extract(payload: dict) -> dict:
    text = payload.get("text") or ""
    names = re.findall(r"Nhân vật:\s*([^\n]+)", text)
    characters = []
    for name in names:
        characters.append(
            {
                "name": name.strip(),
                "aliases": [],
                "faction": "",
                "race": "",
                "abilities": [],
                "known_limitations": [],
                "personality": "",
                "motivations": [],
                "relationships": {},
                "knowledge_state": {"knows": [], "does_not_know": []},
                "current_status": "",
                "alive": True,
                "confidence": 0.4,
            }
        )
    return {
        "characters": characters,
        "locations": [],
        "factions": [],
        "events": [],
        "plotlines": [],
        "rules": [],
        "assertions": [],
    }


def _plan(payload: dict) -> dict:
    return {
        "premise": payload.get("premise")
        or "Một phương án fanfiction không chính thức: Nazarick chuẩn bị chiến dịch kiềm chế chống Thần quyền quốc Slane.",
        "alternatives": ["Tổng tấn công ngay, chấp nhận rủi ro Bảo vật thế giới."],
        "chapters": [
            {
                "title": "Hội nghị chiến tranh",
                "summary": "Ainz công bố mục tiêu nhưng Demiurge phải tính đến Bảo vật thế giới.",
                "scenes": [
                    {
                        "title": "Phòng ngai",
                        "summary": "Mệnh lệnh được nhắc lại với một ràng buộc mới.",
                        "viewpoint_character": "Ainz Ooal Gown",
                        "location": "Đại Lăng Nazarick",
                        "required_events": ["Ainz nhắc lại rằng Thần quyền quốc Slane đã dùng Bảo vật thế giới lên Shalltear."],
                        "emotional_tone": "kiềm chế",
                        "desired_outcome": "Kế hoạch nhiều giai đoạn được chấp nhận.",
                    }
                ],
            }
        ],
    }


def _write(payload: dict, revise: bool) -> dict:
    spec = payload.get("spec") or payload
    viewpoint = spec.get("viewpoint_character") or "Người kể"
    location = spec.get("location") or "một căn phòng kín"
    events = spec.get("required_events") or []
    tone = spec.get("emotional_tone") or "điềm tĩnh"
    previous = spec.get("previous_scene_summary") or ""
    recommendations = payload.get("recommendations") or []
    paragraphs = [
        f"{viewpoint} đứng trong {location}. Không khí {tone}, và không ai trong phòng nhầm sự im lặng ấy với sự bình yên.",
    ]
    if previous:
        paragraphs.append(f"Việc vừa xảy ra vẫn còn đó: {previous}")
    for event in events:
        paragraphs.append(str(event))
    if revise:
        paragraphs.append("Bản sửa bỏ những khẳng định trái với hồ sơ đã có và giữ nguyên các việc bắt buộc.")
        for item in recommendations:
            paragraphs.append(f"Điều chỉnh: {item}")
    else:
        paragraphs.append(
            f"— Nói rõ mục tiêu, — {viewpoint} bảo. — Không có chiến thắng nào đáng đổi bằng một sai lầm mà chúng ta đã trả giá một lần."
        )
    prose = "\n\n".join(paragraphs)
    diff = {
        "recent_events": events,
        "character_updates": [],
        "open_plot_threads": [],
        "notes": "Bản nháp cục bộ, chưa phải chính sử.",
    }
    return {"prose": prose, "state_diff": diff}


def _validate(payload: dict) -> dict:
    prose = payload.get("prose") or ""
    issues = []
    if "nông dân loài người" in prose:
        issues.append(
            {
                "severity": "high",
                "message": "Mâu thuẫn chủng loài của Ainz.",
                "evidence": "Hồ sơ ghi nhận Ainz không phải nông dân loài người.",
                "character": "Ainz Ooal Gown",
            }
        )
    score = 2 if issues else 5
    return {
        "scores": {"consistency": score, "causality": score, "language": 4},
        "issues": issues,
        "recommendations": ["Sửa chủng loài và vị thế của Ainz cho khớp hồ sơ."] if issues else [],
    }
