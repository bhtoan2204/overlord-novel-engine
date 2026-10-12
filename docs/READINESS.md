# Readiness

Checked on 12 October 2026 in this workspace. Figures below are from commands that were actually run.

## Automated tests

`uv run --python 3.12 pytest` → **21 passed**.

The suite uses the scripted model and a temporary database. It imports the original study notes, builds and approves an outline, blocks generation before approval, writes one scene, revises an injected continuity error, exports Markdown, EPUB, and PDF, and recovers a crashed job to `PAUSED`.

## App

`uvicorn` starts with `OVERLORD_INFERENCE_BACKEND=mock` and serves the dashboard on `127.0.0.1:8765`.

In the browser, the dashboard reported the RTX 5070 (2699 / 12227 MB used, 9157 MB free) and 16 cores. Loading the study notes filled the knowledge explorer (Ainz, Albedo, Shalltear, the war order, the World Item rule, each with an evidence source). Verify, outline creation, and approval succeeded. The reader then showed the approved scene "Phòng làm việc sau cơn giận". That scene was produced by the scripted writer, not by Qwen.

`alembic upgrade head` completed against the local SQLite file.

## Models and GPU

Both GGUF files are on disk at the published sizes:

- `Qwen3-8B-Q4_K_M.gguf`, 5027783488 bytes
- `Qwen3-4B-Q4_K_M.gguf`, 2497280256 bytes

llama.cpp `b11574`, CUDA 12.8 Ubuntu build, starts and answers.

A short call returned JSON `{"prose": "Ainz ra lệnh đình chỉ mọi hoạt động không phục vụ phòng thủ Đại Lăng Nazarick.", "state_diff": ...}` in about 17 seconds, including model load.

A longer scene call generated at about **4.5 tokens/s** with `nvidia-smi` showing roughly **11–15%** GPU utilization. Used memory stayed near **2700–2800 MB** of 12227 MB, the same band as before the process started. Per-process GPU memory was not reported. So this host is not showing a real VRAM allocation for llama.cpp, and the speed is in the CPU range even with `-ngl 36`. The launch plan still estimated several gigabytes and selected context 4096 or 8192 with Q8 KV cache depending on free memory at startup. That estimate was not confirmed by `nvidia-smi`.

One full scene attempt then failed: a JSON retry appended the draft and the next prompt was 4101 tokens against a 4096 context. The retry no longer resends the draft, completion is capped at 512 tokens, and `response_format` is `json_object`. The short call after that change succeeded. A second full multi-validator scene was not re-run after the fix.

## Discovery

`https://meobietbay.com/robots.txt` allows the index (it disallows `/wp-admin/` only). No chapter text was downloaded.

## Outline

`docs/VOLUME_17_OUTLINE.md` is the deterministic outline from the bundled study notes. It is unofficial and it is waiting for a person to approve it in the Planner page. Generation of the whole volume was not started.
