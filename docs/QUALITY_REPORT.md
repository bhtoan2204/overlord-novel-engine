# Quality report

Fanfiction. Not canon. Measured 2026-10-13.

## Part that was generated

`data/generated/volume17/part-1.md`

| Item | Measured |
| --- | --- |
| Title | Phòng làm việc sau cơn giận |
| Target | 4,000 Vietnamese words |
| Accepted words | 5,845 |
| Exported words | 5,845 |
| Status after the range gate | NEEDS_REVIEW |
| Requests | 34 (32 accepted, 2 rejected as repetition) |
| Wall time | 1,428 seconds |

The beats were all written, and the count is above 90 percent of 4,000. It is not an accepted part. 5,845 is above the 120 percent ceiling (4,800), and the prose adds a northern army, a golden hairpin, a vanished squad, and a sword. The gate now records that as NEEDS_REVIEW. A later chunk for a beat asks only for the words still missing, instead of another full chunk. The volume stays incomplete, and it cannot be marked complete while Volumes 1–16 have no ingested full text.

One repetition was rejected and the beat continued. The rejected text is stored and is not in the export.

## What the prose does badly

The model keeps Ainz in the office and invents threats that are not in the outline: a northern army, a golden hairpin, a vanished southern squad, and an unnamed ally. It also gives him a sword and calls the tomb’s forces “Dark Lord.” Those are not verified Volume 16 facts. The part gate checks structure and length. It does not yet block invented factions.

The earlier 629-word file remains at `prologue-scene-1.md`. It is not this part and it is not a finished volume.

## Tests

34 tests passed, including budget sums, migration of an old scene draft, resume without duplicating a chunk, repetition not completing a part, truncation and a too-small context pausing, a failed call leaving the previous chunk in place, a stored part above 10,000 words, and volume status staying incomplete when no scene is left.

## Not started

The other 51 parts. A full 200,000-word run. Fine-tuning. GPU offload, which still fails because `libcudart.so.12` and `libcublas.so.12` are missing. See `docs/GPU_BENCHMARK.md`.
