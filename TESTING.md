# Testing

```bash
uv sync --extra dev --python 3.12
uv run --python 3.12 pytest
```

Tests use a temporary SQLite file, the hashing embedder, and the scripted model. They do not download weights and they do not call the GPU.

Covered:

- Canon rank, including the rule that alternate-universe and AI-generated claims do not override main-timeline facts
- Workflow transitions
- TXT, Markdown, PDF, and EPUB import, and a second import of the same checksum
- `robots.txt` refusal and index-link parsing that ignores body text
- VRAM plan: context is reduced before the GPU is abandoned; a nearly full GPU falls back to CPU
- Hybrid retrieval of the Shalltear note, exclusion of an alternate-universe chunk, and withholding Albedo's secret from Ainz's context pack
- The canon validator flags an injected sentence that calls Ainz a human farmer
- A bad draft is revised and the canonical character row is unchanged
- Interrupted jobs return to `PAUSED` and keep their checkpoint
- Preference text is added when dialogue scores are low
- JSON that is not JSON is retried once
- Training stays off, and unlicensed notes are excluded
- HTTP smoke test: import sample notes, verify canon, create and approve an outline, refuse generation before approval, write one scene, export Markdown, EPUB, and PDF

Last run during implementation: `21 passed`.

The scripted backend is what makes those tests deterministic. A separate manual run loaded `Qwen3-8B-Q4_K_M.gguf` and received a short JSON reply. That run is not part of pytest. Do not treat the pytest count as a measure of prose quality.
