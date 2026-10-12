import json

from app.inference.base import GenerationSettings, ScriptedBackend
from app.inference.structured import generate_model
from app.knowledge.schemas import DraftOutput


def test_malformed_json_is_retried_once():
    good = json.dumps({"prose": "Một câu.", "state_diff": {"recent_events": ["Việc xảy ra."]}}, ensure_ascii=False)
    backend = ScriptedBackend(["không phải json", good])
    result = generate_model(
        backend,
        [{"role": "user", "content": json.dumps({"task": "write", "spec": {"required_events": ["Việc xảy ra."]}})}],
        GenerationSettings(0.1, 1, 200, "write"),
        DraftOutput,
        attempts=2,
    )
    assert result.prose == "Một câu."
    assert len(backend.calls) == 2
