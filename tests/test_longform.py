import json

from app.core.errors import InferenceError
from app.inference.base import GenerationResult, GenerationSettings
from app.inference.budget import completion_budget
from app.knowledge.coverage import coverage_report
from app.knowledge.schemas import SceneSpec
from app.narrative.prose import write_scene_chunks
from app.narrative.validators import validate_plot
from app.core.config import Settings


def test_completion_budget_uses_remaining_context_not_a_fixed_cap():
    assert completion_budget(8192, 1000, 2000) == 2000
    assert completion_budget(4096, 3000, 2000) == 1064
    try:
        completion_budget(4096, 4080, 500)
        raise AssertionError("expected overflow")
    except InferenceError:
        pass


class _ChunkBackend:
    name = "llama.cpp"

    def __init__(self):
        self.calls = 0

    def generate(self, messages, settings: GenerationSettings) -> GenerationResult:
        self.calls += 1
        if settings.json_object:
            return GenerationResult(
                text=json.dumps({"recent_events": ["Sự kiện bắt buộc của cảnh thử."], "notes": "ok", "canon_mutation": False}),
                finish_reason="stop",
            )
        words = " ".join(f"c{self.calls}w{i}" for i in range(220))
        words += " Sự kiện bắt buộc của cảnh thử."
        return GenerationResult(text=words, finish_reason="stop", completion_tokens=220)


def test_scene_is_several_plain_text_calls():
    spec = SceneSpec(
        scene_id="s1",
        viewpoint_character="Ainz Ooal Gown",
        location="phòng",
        timestamp="sau tập 16",
        scene_objective="Viết tiếp",
        required_events=["Sự kiện bắt buộc của cảnh thử."],
        target_word_count=400,
    )
    backend = _ChunkBackend()
    draft = write_scene_chunks(backend, spec, {"sections": []}, Settings(cooldown_seconds=0))
    assert backend.calls >= 3
    assert "c1w0" in draft.prose
    assert draft.prose.strip().startswith("{") is False


def test_short_scene_is_blocked_when_a_long_scene_was_planned():
    spec = SceneSpec(
        scene_id="s2",
        viewpoint_character="Ainz Ooal Gown",
        location="phòng",
        timestamp="sau tập 16",
        target_word_count=1000,
        required_events=["một việc"],
        scene_objective="mục tiêu",
    )
    report = validate_plot(spec, "một việc và vài câu ngắn")
    assert any(issue["severity"] == "high" for issue in report["issues"])


def test_coverage_does_not_treat_notes_as_sixteen_volumes(app, session):
    report = coverage_report(session)
    assert report["full_text_volumes"] == 0
    assert all(item["status"] == "missing" for item in report["volumes"])
    assert "not ingested" in report["note"]
