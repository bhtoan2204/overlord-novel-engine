# Model configuration

Verified on 12 October 2026. Identifiers below were read from the Hugging Face model cards and from HTTP `Content-Length`. They were not invented.

## Primary

| Field | Value |
| --- | --- |
| Repository | `Qwen/Qwen3-8B-GGUF` |
| Base model | `Qwen/Qwen3-8B` |
| File | `Qwen3-8B-Q4_K_M.gguf` |
| Bytes | 5027783488 |
| License on the model card | apache-2.0 |
| Quantization | Q4_K_M |
| Architecture used for estimates | 36 layers, 8 KV heads, head dim 128, native context 32768 |
| Chat template | Jinja template embedded in the GGUF. The server is started with `--jinja`. |
| Tokenizer | Embedded in the GGUF |
| Thinking | Disabled with `--reasoning off` and `chat_template_kwargs.enable_thinking=false` |

## Fallback

| Field | Value |
| --- | --- |
| Repository | `Qwen/Qwen3-4B-GGUF` |
| File | `Qwen3-4B-Q4_K_M.gguf` |
| Bytes | 2497280256 |
| License on the model card | apache-2.0 |

The registry is `config/models.yaml`. Replacing a model means adding a record there and setting `OVERLORD_ACTIVE_MODEL`. If the primary file is missing, the client tries `qwen3-4b-q4`.

SHA-256 files are written by `scripts/download_models.sh` after a download. This workspace received the files by a direct `curl` of those same URLs. The byte sizes match the published `Content-Length`. A SHA-256 was not computed in this session, so none is recorded here.

## Engine

llama.cpp release `b11574`, binary `llama-b11574-bin-ubuntu-cuda-12.8-x64`, version string `0.6.0-dev (build 11574)`.

The CUDA 13.4 Ubuntu build was not used. `nvidia-smi` on this machine reports CUDA 13.0, and a 13.4 runtime can require a newer driver. CUDA 12.8 is the newest Ubuntu GPU build that stays within that driver.

## Embeddings

Default: hashing embedder, 256 dimensions, CPU, no download.

Optional: `intfloat/multilingual-e5-small` via `sentence-transformers`, forced to CPU, with the `query:` and `passage:` prefixes. Install with `uv sync --extra embed` and set `OVERLORD_EMBEDDING_BACKEND=e5`.

## Generation settings

| Task | Temperature | Notes |
| --- | --- | --- |
| Planning | 0.3 | Only when `OVERLORD_PLANNER_MODE=llm` |
| Writing | 0.8 | Seed default 17 |
| Validation | 0.1 | Heuristics always run. LLM validators are off unless `OVERLORD_USE_LLM_VALIDATORS=true` |

Malformed JSON is retried up to three times, then the call fails. There is no unbounded retry.

Completion length is capped to about one sixth of the context the VRAM plan actually selected, so the prompt and the completion can share the window.

## Resource plan

Order used by `plan_launch`:

1. Smaller context (8192, then 4096, 2048, 1024), and at each size an 8-bit KV cache if 16-bit KV does not fit.
2. Fewer GPU layers (24, 16, 8).
3. Smaller batch (256, then 128).
4. CPU (`gpu_layers=0`).
5. Optional wait, only if `OVERLORD_WAIT_FOR_VRAM=true`.

The estimate is `weight * (gpu layers / layers) + KV cache + 700 MB overhead`. It is a planning figure. On this WSL host, `nvidia-smi` did not move when llama-server was running, and per-process GPU memory was not reported, so the estimate was not confirmed as a measured allocation.

A smoke call with the 8B Q4 model returned `{"status":"ok","language":"vi"}` (42 prompt tokens, 13 completion tokens). The plan for that call, with about 6118 MB usable after the 3000 MB reserve, was context 4096, 36 GPU layers, estimated 6070 MB.

CPU use is limited by `--cpu-range` to about half the cores (8 of 16 at the default 50% cap) and `--threads` matches that count. Inference concurrency is one.
