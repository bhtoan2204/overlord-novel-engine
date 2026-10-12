"""One real Qwen scene. Writes prose and a measurement file. Does not fall back to mock."""

import json
import time
from pathlib import Path

from app.core.config import Settings
from app.core.text import word_count
from app.inference.llama_cpp import LlamaCppBackend
from app.knowledge.schemas import SceneSpec
from app.narrative.prose import write_scene_chunks
from app.narrative.validators import validate_plot
from app.narrative.volume17_plan import BLUEPRINT

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "generated" / "volume17"


def main() -> None:
    scene = BLUEPRINT[0]["chapters"][0]["scenes"][0]
    spec = SceneSpec(
        scene_id="prologue-1",
        viewpoint_character=scene["viewpoint"],
        location=scene["location"],
        timestamp="ngay sau Tập 16",
        scene_objective=scene["objective"],
        participating_characters=scene["participants"],
        required_events=scene["events"],
        desired_outcome=scene["outcome"],
        emotional_tone=scene["tone"],
        target_word_count=900,
        prohibited_contradictions=["Ainz là người sống", "nhịp tim", "Shalltear chết"],
    )
    settings = Settings(cooldown_seconds=1, context_tokens=4096)
    backend = LlamaCppBackend(settings)
    records = []
    original = backend.generate

    def wrapped(messages, generation):
        started = time.monotonic()
        result = original(messages, generation)
        elapsed = time.monotonic() - started
        records.append(
            {
                "task": generation.task,
                "json": generation.json_object,
                "prompt_tokens": result.prompt_tokens,
                "completion_tokens": result.completion_tokens,
                "finish_reason": result.finish_reason,
                "elapsed_s": round(elapsed, 2),
                "tokens_per_second": round(result.completion_tokens / elapsed, 2) if elapsed else 0,
            }
        )
        return result

    backend.generate = wrapped
    started = time.monotonic()
    try:
        draft = write_scene_chunks(
            backend,
            spec,
            {"sections": [{"text": "Sau Tập 16, Ainz biết Thần quyền quốc Slane dùng Bảo vật thế giới để điều khiển Shalltear và đã ra lệnh chuẩn bị tiêu diệt họ."}]},
            settings,
        )
        plan = backend.plan
    finally:
        backend.stop()
    prose = draft.prose
    report = validate_plot(spec, prose)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "prologue-scene-1.md").write_text(
        "Fanfiction không chính thức. Không phải chính sử.\n\n" + prose + "\n",
        encoding="utf-8",
    )
    payload = {
        "title": scene["title"],
        "vietnamese_words": word_count(prose),
        "target_words": spec.target_word_count,
        "elapsed_s": round(time.monotonic() - started, 2),
        "requests": records,
        "high_issues": [issue for issue in report["issues"] if issue["severity"] == "high"],
        "launch": None
        if plan is None
        else {
            "context": plan.context_tokens,
            "gpu_layers": plan.gpu_layers,
            "mode": plan.mode,
            "reason": plan.reason,
        },
    }
    (OUT / "prologue-scene-1.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"words": payload["vietnamese_words"], "requests": len(records), "high": len(payload["high_issues"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
