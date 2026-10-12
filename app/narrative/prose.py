"""Plain-text scene writing in bounded chunks. World-state JSON is a separate call."""

import json
import re

from app.core.config import Settings
from app.core.disclaimer import DISCLAIMER
from app.core.text import word_count
from app.inference.base import ChatBackend, GenerationResult, GenerationSettings
from app.inference.structured import generate_model
from app.knowledge.schemas import DraftOutput, SceneSpec, StateDiff


def _tail(text: str, words: int = 180) -> str:
    parts = text.split()
    return " ".join(parts[-words:])


def _long_sentences(text: str) -> set[str]:
    parts = re.split(r"[.!?…]\s+", text)
    return {" ".join(part.split()) for part in parts if len(part.split()) >= 8}


def _rejects(previous: str, piece: str) -> bool:
    if re.search(r"[\u4e00-\u9fff]", piece):
        return True
    if not previous:
        return False
    return bool(_long_sentences(previous) & _long_sentences(piece))


def _duplicate_paragraphs(chunks: list[str]) -> bool:
    seen: set[str] = set()
    for chunk in chunks:
        for paragraph in chunk.split("\n\n"):
            key = " ".join(paragraph.split())
            if len(key) < 80:
                continue
            if key in seen:
                return True
            seen.add(key)
    return False


def write_scene_chunks(
    backend: ChatBackend,
    spec: SceneSpec,
    context_pack: dict,
    settings: Settings,
    *,
    revise: bool = False,
    previous_prose: str = "",
    recommendations: list[str] | None = None,
    preference_notes: str = "",
) -> DraftOutput:
    """Several short completions. A truncated chunk is continued, not stored as a finished scene."""
    target = max(1, spec.target_word_count)
    floor = int(target * 0.90)
    chunks: list[str] = []
    reasons: list[str] = []
    advice = " ".join(recommendations or [])
    if preference_notes:
        advice = (advice + " " + preference_notes).strip()
    context_lines = [section["text"] for section in (context_pack.get("sections") or [])[:6]]
    limit = max(4, (target + 149) // 150)
    for index in range(1, limit + 1):
        so_far = "\n\n".join(chunks).strip()
        remaining = target - word_count(so_far)
        if so_far and remaining <= 40 and word_count(so_far) >= floor:
            break
        ask_words = min(280, max(140, remaining))
        covered = bool(so_far) and all(event in so_far for event in spec.required_events)
        system = (
            "Bạn viết fanfiction dark fantasy bằng tiếng Việt, giọng riêng. "
            f"{DISCLAIMER} "
            "Chỉ viết tiếp văn xuôi. Không JSON. Không tiêu đề. Không chữ Hán. "
            "Không bịa sức mạnh mới. Không lặp câu đã có trong đoạn trước."
        )
        if covered:
            task_line = (
                "Câu bắt buộc đã có trong đoạn trước. Cấm viết lại câu đó. "
                "Viết hành động mới: một người trong danh sách bước vào và nhận một giới hạn cụ thể."
            )
        else:
            task_line = f"Việc bắt buộc phải xuất hiện đúng một lần: {' '.join(spec.required_events)}"
        user = (
            f"Cảnh: {spec.scene_objective}\n"
            f"Điểm nhìn: {spec.viewpoint_character}. Địa điểm: {spec.location}. Giọng: {spec.emotional_tone}.\n"
            f"Người có thể xuất hiện: {', '.join(spec.participating_characters)}\n"
            f"{task_line}\n"
            f"Không được viết: {'; '.join(spec.prohibited_contradictions[:6])}\n"
            f"Tư liệu: {' | '.join(context_lines)}\n"
            f"Đoạn đã viết, hãy viết tiếp chứ đừng lặp: {_tail(so_far) if so_far else (previous_prose[-800] if revise else '')}\n"
            f"Gợi ý sửa: {advice}\n"
            f"Viết khoảng {ask_words} từ tiếng Việt cho phần này."
        )
        result = backend.generate(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            GenerationSettings(
                temperature=settings.temperature_write,
                seed=settings.seed + index,
                max_tokens=min(1400, max(400, ask_words * 2)),
                task="write_chunk",
                json_object=False,
            ),
        )
        piece = _clean_chunk(result.text)
        reasons.append(result.finish_reason or "stop")
        if not piece or _rejects(so_far, piece) or _duplicate_paragraphs(chunks + [piece]):
            continue
        chunks.append(piece)
        if (result.finish_reason or "") not in {"length", "truncation"} and word_count("\n\n".join(chunks)) >= floor:
            break
    prose = "\n\n".join(chunks).strip()
    diff = _state_diff(backend, spec, prose, settings)
    draft = DraftOutput(prose=prose, state_diff=diff)
    return draft


def _clean_chunk(text: str) -> str:
    cleaned = (text or "").strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.removeprefix("json").strip()
    if cleaned.startswith("{") and '"prose"' in cleaned[:80]:
        return ""
    return cleaned.strip()


def _state_diff(backend: ChatBackend, spec: SceneSpec, prose: str, settings: Settings) -> StateDiff:
    try:
        parsed = generate_model(
            backend,
            [
                {
                    "role": "system",
                    "content": "Trả JSON mô tả thay đổi trạng thái truyện. Không sửa chính sử. canon_mutation phải là false.",
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "scene": spec.scene_objective,
                            "required_events": spec.required_events,
                            "prose_tail": prose[-1500:],
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
            GenerationSettings(settings.temperature_validate, settings.seed, 220, "state_diff", json_object=True),
            StateDiff,
            attempts=1,
        )
        return parsed
    except Exception:
        return StateDiff(recent_events=list(spec.required_events), notes="State diff fallback from required events.")


def result_from_text(text: str, finish_reason: str = "stop") -> GenerationResult:
    return GenerationResult(text=text, finish_reason=finish_reason, model="test")
