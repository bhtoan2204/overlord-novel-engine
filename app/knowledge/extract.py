"""Knowledge extraction from structured notes or from a local model."""

import json

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.inference.base import ChatBackend, GenerationSettings
from app.inference.structured import generate_model
from app.knowledge.schemas import Extraction
from app.knowledge.store import upsert_extraction


def extraction_from_document(document: dict, notes: str) -> Extraction:
    if any(key in document for key in ("characters", "events", "plotlines", "factions", "rules", "assertions", "locations")):
        return Extraction.model_validate(document)
    return Extraction()


def extract_with_model(backend: ChatBackend, text: str, settings: Settings) -> Extraction:
    messages = [
        {
            "role": "system",
            "content": (
                "TASK: extract. Trích xuất ghi chú thành JSON. "
                "Không chép nguyên văn sách. Mỗi khẳng định phải có thể truy về nguồn người dùng cung cấp. "
                "Phân biệt fact, belief, rumor, interpretation, unknown."
            ),
        },
        {"role": "user", "content": json.dumps({"text": text[:12000]}, ensure_ascii=False)},
    ]
    generation = GenerationSettings(
        temperature=settings.temperature_validate,
        seed=settings.seed,
        max_tokens=2048,
        task="extract",
    )
    result = generate_model(backend, messages, generation, Extraction, settings.max_json_attempts)
    return result


def store_source_knowledge(
    session: Session,
    source_id: str,
    canon_level: str,
    timeline: str,
    document: dict | None,
    text: str,
    backend: ChatBackend | None,
    settings: Settings,
) -> dict:
    if document:
        extraction = extraction_from_document(document, text)
    elif backend is not None:
        extraction = extract_with_model(backend, text, settings)
    else:
        extraction = Extraction()
    return upsert_extraction(session, extraction, source_id, canon_level, timeline)
