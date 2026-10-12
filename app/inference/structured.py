"""JSON schema retries. Malformed model output is asked again, up to a fixed limit."""

import json

from pydantic import BaseModel, ValidationError

from app.core.errors import InferenceError
from app.core.text import extract_json_blob
from app.inference.base import ChatBackend, GenerationSettings


def generate_model(
    backend: ChatBackend,
    messages: list[dict],
    settings: GenerationSettings,
    model: type[BaseModel],
    attempts: int = 3,
) -> BaseModel:
    conversation = list(messages)
    conversation.append(
        {
            "role": "user",
            "content": (
                "Chỉ trả một JSON object, không markdown. "
                "Khóa prose là văn tiếng Việt. state_diff gồm recent_events, character_updates, "
                "political_changes, alliances, open_plot_threads, secrets_discovered, notes, "
                "canon_mutation=false, resurrection_mechanism=\"\"."
            ),
        }
    )
    last_error: Exception | None = None
    for _ in range(attempts):
        result = backend.generate(conversation, settings)
        try:
            data = json.loads(extract_json_blob(result.text))
            return model.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as exc:
            last_error = exc
            conversation = list(messages) + [
                {
                    "role": "user",
                    "content": "Lần trước không phải JSON hợp lệ. Trả duy nhất một object JSON ngắn, không giải thích.",
                }
            ]
    raise InferenceError(f"Model output did not match the schema after {attempts} attempts: {last_error}")
