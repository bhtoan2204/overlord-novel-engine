# Overlord Novel Engine

Local-first tool for an **unofficial** Vietnamese continuation of Overlord after Volume 16. It is fan fiction. It is not a new volume by Kugane Maruyama and it is not canon.

The app imports notes you are allowed to use, keeps evidence next to every extracted claim, plans a Volume 17 outline, and writes one scene at a time. Canonical source rows are never overwritten by generated events.

## What this machine was checked against

- WSL2, Python 3.12.15, 16 logical CPUs, 15 GB RAM
- NVIDIA GeForce RTX 5070, 12227 MB VRAM
- Driver 581.08, CUDA 13.0 as reported by `nvidia-smi`
- llama.cpp `b11574` (`0.6.0-dev`), Ubuntu CUDA 12.8 build
- `Qwen/Qwen3-8B-GGUF` file `Qwen3-8B-Q4_K_M.gguf` (5027783488 bytes)
- Fallback `Qwen/Qwen3-4B-GGUF` file `Qwen3-4B-Q4_K_M.gguf` (2497280256 bytes)

GPU utilization is not the same thing as VRAM allocation. The launch plan estimates weight, KV cache, and overhead, then lowers context, KV cache type, GPU layers, and batch size. That is not a hard ceiling inside the driver. On this WSL session, `nvidia-smi` also did not show the llama.cpp process's memory (compute processes reported no per-process figure), so a measured allocation cannot be claimed from that tool alone.

## Setup

```bash
cd /home/toan/overlord-novel-engine
uv sync --extra dev --python 3.12
# Models are already in data/models/ on this machine.
# On a fresh machine:
bash scripts/download_models.sh
bash scripts/run.sh
```

Open http://127.0.0.1:8765 . The server binds to localhost only.

Optional multilingual embeddings (CPU, downloads `intfloat/multilingual-e5-small`):

```bash
uv sync --extra embed --python 3.12
# then set OVERLORD_EMBEDDING_BACKEND=e5
```

The default embedder is a local hashing embedder so tests and first run do not download Torch.

## Import authorized notes

1. Open **Library**.
2. Either load the bundled original study notes, or upload TXT, Markdown, EPUB, JSON, or PDF.
3. Set the canon level and a license or permission note. The importer refuses a file with no license field.
4. Full text is never downloaded from the web. **Discovery** stores titles and links from an index page only when `robots.txt` allows it.

The bundled file `data/seed/volume_16_study_notes.json` is an original structured summary, classified `USER_INTERPRETATION`, license `original-structured-notes`. It is not primary canon and it is not cleared for training.

## Generate the unofficial Volume 17

1. **Planner → Verify canon.** Conflicts are recorded. Alternate-universe facts stay off the main timeline. AI-generated text cannot replace a source fact.
2. **Create Volume 17 outline.** The default planner is deterministic and builds the outline from unresolved plotlines. Switch to `llm` in Settings only when you want the local model to propose a different outline.
3. Read the alternatives. Edit chapter summaries if you want.
4. **Approve outline.** Scene generation is refused before this.
5. **Generate → Generate next scene.** One scene is written, checked by four validators, revised up to three times, and checkpointed. A background start is capped at three scenes so one click cannot run the whole volume.
6. Rate the scene under **Feedback**. Ratings change later instructions. They do not fine-tune the model.
7. **Export** Markdown, EPUB, or PDF. Each file carries the unofficial-work notice.

Pause, resume, and cancel are on the generation page. If the process dies during a scene, the next startup marks that job paused and leaves approved scenes in place.

## Tests

```bash
uv run --python 3.12 pytest
```

The last full run in this workspace was 21 passed. See `TESTING.md` and `docs/READINESS.md`.

## Layout

`app/` holds the FastAPI UI, ingestion, retrieval, knowledge, narrative pipeline, and llama.cpp client. `data/` holds the database, uploads, models, and exports. `config/models.yaml` is the model registry.
