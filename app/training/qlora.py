"""Optional QLoRA entry point.

Training is off unless OVERLORD_TRAINING_ENABLED=1 and the CLI flag --enable-training
are both present. This module does not download a base model and does not start
training on import. Sources are eligible only when training_allowed is true and
the license is on the allowlist.
"""

import json
from pathlib import Path

from app.core.errors import EngineError

TRAINING_LICENSES = {"apache-2.0", "mit", "cc-by-4.0", "original-notes-with-training-rights"}


def assert_training_allowed(enabled: bool, cli_flag: bool) -> None:
    if not enabled or not cli_flag:
        raise EngineError(
            "Fine-tuning is disabled. Set OVERLORD_TRAINING_ENABLED=true and pass --enable-training. "
            "Do not enable it just because the command exists."
        )


def eligible_records(records: list[dict]) -> list[dict]:
    accepted = []
    for record in records:
        if not record.get("training_allowed"):
            continue
        if record.get("copyright_or_license_status") not in TRAINING_LICENSES:
            continue
        accepted.append(record)
    return accepted


def split_records(records: list[dict], seed: int = 17) -> dict[str, list[dict]]:
    import random

    items = list(records)
    random.Random(seed).shuffle(items)
    count = len(items)
    train_end = max(1, int(count * 0.8)) if count else 0
    valid_end = max(train_end, int(count * 0.9)) if count else 0
    if count >= 3:
        train_end = max(1, count - 2)
        valid_end = count - 1
    return {"train": items[:train_end], "validation": items[train_end:valid_end], "evaluation": items[valid_end:]}


def write_splits(records: list[dict], directory: Path, seed: int = 17) -> dict:
    chosen = eligible_records(records)
    if len(chosen) < 3:
        raise EngineError("Need at least three records with training rights before a split can be written.")
    parts = split_records(chosen, seed)
    directory.mkdir(parents=True, exist_ok=True)
    for name, rows in parts.items():
        path = directory / f"{name}.jsonl"
        path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")
    return {name: len(rows) for name, rows in parts.items()}


def qlora_config() -> dict:
    return {
        "method": "qlora",
        "load_in_4bit": True,
        "per_device_train_batch_size": 1,
        "gradient_accumulation_steps": 8,
        "gradient_checkpointing": True,
        "max_seq_length": 1024,
        "learning_rate": 1e-4,
        "lora_r": 8,
        "lora_alpha": 16,
        "lora_dropout": 0.05,
        "single_process": True,
    }


def memory_stop(available_ram_mb: int, free_vram_mb: int | None, floor_ram_mb: int = 4000, floor_vram_mb: int = 1500) -> str | None:
    if available_ram_mb < floor_ram_mb:
        return f"Stop: only {available_ram_mb} MB RAM available."
    if free_vram_mb is not None and free_vram_mb < floor_vram_mb:
        return f"Stop: only {free_vram_mb} MB VRAM free."
    return None


def run_training(enabled: bool, cli_flag: bool) -> None:
    assert_training_allowed(enabled, cli_flag)
    try:
        import peft  # noqa: F401
        import transformers  # noqa: F401
    except ImportError as exc:
        raise EngineError(
            "Training dependencies are not installed. Use: uv sync --extra train. Training was not started."
        ) from exc
    raise EngineError(
        "The QLoRA configuration is available, but this command refuses to launch a training job automatically. "
        "Review qlora_config(), the license split, and GPU headroom, then wire a supervised run explicitly."
    )
