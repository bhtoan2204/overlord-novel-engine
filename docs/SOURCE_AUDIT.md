# Source audit

Date: 2026-10-13. The engine was not rebuilt. The defects below were in the running code.

## Critical

`app/inference/llama_cpp.py` set `max_tokens = min(settings.max_tokens, 512, max(128, context_limit // 6))` and always sent `response_format: json_object`. A scene could not grow, and prose was forced through JSON. Completion length is now `completion_budget(context, prompt_tokens, requested)` in `app/inference/budget.py`. Prompt size comes from llama-server `/tokenize` when that call works, otherwise from a word estimate. JSON mode is only set for structured calls. Prose uses several plain-text calls in `app/narrative/prose.py`. A `finish_reason` of `length` is stored as `truncation` and is not treated as a finished chapter by itself.

A live log line remains from the earlier failure: a request of 4101 tokens exceeded a context of 4096. The budget function refuses a prompt that leaves fewer than 32 tokens of room.

## Outline and mock prose

The previous deterministic outline ended with the Theocracy still standing and postponed the war. `app/narrative/volume17_plan.py` replaces that plan with 52 scenes. The central government falls in this volume. The already approved mock scene in the existing project database was not overwritten.

`app/inference/mock_content.py` wrote a few paragraphs. The mock path still exists only when the backend is the scripted/mock backend. A llama.cpp failure does not switch to it. When a scene target is at least 600 words, the mock expands with distinct sentences so tests can pass the length gate. That text is test filler, not the novel.

## Retrieval and data

The default embedder is still the hashing backend. `E5Embedder` already applies `query:` and `passage:` prefixes, but `sentence-transformers` is an optional extra and is not the default until it is installed and checked. Hybrid FTS5 and FAISS were already in the retrieval path.

Local full text is the original Volume 16 study notes. Volumes 1–16 of the novels are not ingested. Discovered URLs are catalog links, not chapter text. `app/knowledge/coverage.py` reports that distinction. The coverage page is `/coverage`.

## Validation

Plot validation now marks a scene as a high-severity failure when the plan asks for at least 600 words and the draft is under 60 percent of that target. Short scripted tests set a low target so they still check contradictions rather than length. Added checks cover invented power jumps, duplicate paragraphs, and a continuity phrase that erases the previous scene. These are heuristics, not a full editorial staff.

## What is still not done

A complete 60,000-word volume has not been generated. Fine-tuning has not been run. GPU offload has not been declared healthy; see `docs/INFERENCE_BENCHMARK.md` after the measurement run.
