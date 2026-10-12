# Architecture

The process is one local FastAPI app. There is no Redis, queue, or second database.

```
Browser (Jinja pages)
    → app/api/routes.py
        → library import / discovery
        → narrative pipeline
            → hybrid retrieval
            → writer (one scene)
            → four heuristic validators
            → story-state diff
        → llama.cpp server (one process) or the scripted backend
SQLite (sources, knowledge, outline, drafts, jobs, snapshots)
FAISS index + FTS5
```

## Two stores

Canonical tables (`characters`, `events`, `assertions`, and the rest) change only when a source is imported. A scene commit writes a new row in `snapshots` and `state_diffs`. Rollback deletes later snapshots. It does not edit the canonical rows.

`AI_GENERATED` and `ALTERNATE_UNIVERSE` cannot outrank a main-timeline fact. Rank order lives in `app/core/canon.py`.

## Inference

`ChatBackend` is the only generation interface. `ScriptedBackend` answers tests. `LlamaCppBackend` starts `llama-server` with the plan from `app/inference/resources.py`. A process-wide gate refuses to run embeddings, inference, and training at the same time.

Server logs go to `data/logs/llama-server.log`. They are not left on a pipe, because a full pipe stalls the process.

Thinking mode is off (`--reasoning off` and `enable_thinking: false`). `<think>` blocks are stripped if one still appears. They are not stored as story text.

## Retrieval

A scene context pack is a budgeted set of sections: the viewpoint profile, facts that character is allowed to know, world rules, unresolved plotlines that do not leak a hidden fact, and a few retrieved source chunks. Restricted assertions are withheld from other viewpoints and added to the prohibited list.

Lexical search is SQLite FTS5. Vectors are FAISS inner product. Scores are fused, then a token-overlap pass reranks. The default vectors are hashed bag-of-words so the app runs offline. `intfloat/multilingual-e5-small` is the CPU multilingual option.

## Jobs

Workflow names match the requested state machine, including `FAILED`, `PAUSED`, and `CANCELLED`. Startup calls `recover_interrupted()`. A scene left in `SCENE_GENERATING`, `SCENE_VALIDATING`, or `SCENE_REVISING` becomes `PAUSED`. Approved scenes stay approved. Retries stop at three attempts.

## UI

Server-rendered pages. One small script toggles the mobile navigation. The app listens on `127.0.0.1` and has no login, because it is a single-user local tool. Do not expose it on a network.
