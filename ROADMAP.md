# Roadmap

Done in this MVP:

- Local app, SQLite, migrations, source import, discovery that honors `robots.txt`
- Knowledge records with evidence, canon ranks, and viewpoint-limited retrieval
- Deterministic Volume 17 outline, approval gate, scene writer, four validators, revisions, story snapshots
- Pause, resume, cancel, crash recovery, Markdown, EPUB, and PDF export
- llama.cpp client for the verified Qwen3 GGUF files, with a VRAM launch plan
- Feedback that only changes prompts
- A QLoRA guard that refuses to train unless explicitly enabled, and still does not launch a job

Not done, and not claimed:

- A measured hard VRAM cap. The planner estimates. `nvidia-smi` on this WSL host did not show llama.cpp's allocation.
- SHA-256 of the GGUF files. Sizes were checked. Hashes were not.
- Multilingual E5 embeddings in the default install. The code path exists; Torch is an optional extra and was not installed here.
- LLM validators as the default. Heuristics are the default because they can be tested. Set `OVERLORD_USE_LLM_VALIDATORS=true` only after you want the extra calls.
- Fine-tuning and an A/B comparison against a fine-tuned checkpoint. The splitter and the QLoRA settings exist. No training run was started, and no comparison numbers exist.
- Authentication. The server is localhost-only.
- A full 45–65 thousand word volume. The pipeline can continue scene by scene after you approve the outline. It was not launched.

Reasonable next work, in order:

1. Compute and store SHA-256 for both GGUF files.
2. Install the embed extra and compare hash retrieval with E5 on the imported notes.
3. Read a generated chapter yourself and tighten the validators where they miss a real contradiction.
4. Only then consider QLoRA, and only on text whose license is on the allowlist.
