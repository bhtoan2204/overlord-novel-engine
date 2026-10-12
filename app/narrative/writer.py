"""Scene writer. One scene per call. Completed scenes stay unless a rewrite is requested."""

import json

from app.core.config import Settings
from app.core.disclaimer import DISCLAIMER, GLOSSARY
from app.inference.base import ChatBackend, GenerationSettings
from app.inference.structured import generate_model
from app.knowledge.schemas import DraftOutput, SceneSpec


def write_scene(
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
    system = (
        "Bạn viết fanfiction dark fantasy bằng tiếng Việt, giọng riêng, không nhái văn của tác giả gốc. "
        f"{DISCLAIMER} "
        "Chỉ viết một cảnh. Không toàn tri. Không hồi sinh tùy tiện. Không tăng sức mạnh không nguyên nhân. "
        "Đối thoại phải phục vụ mục đích. Giữ đúng thuật ngữ. "
        f"{GLOSSARY} "
        "Trả về JSON với khóa prose và state_diff. prose là văn xuôi tiếng Việt. "
        "state_diff chỉ mô tả thay đổi của truyện đang viết, không được sửa chính sử nguồn."
    )
    if preference_notes:
        system += " Ưu tiên của người đọc: " + preference_notes
    user = {
        "task": "revise" if revise else "write",
        "spec": spec.model_dump(),
        "context": context_pack,
        "previous_prose": (previous_prose if revise else "")[:1200],
        "recommendations": recommendations or [],
    }
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
    ]
    generation = GenerationSettings(
        temperature=settings.temperature_write,
        seed=settings.seed,
        max_tokens=min(4096, max(600, spec.target_word_count * 3)),
        task="revise" if revise else "write",
    )
    return generate_model(backend, messages, generation, DraftOutput, settings.max_json_attempts)
