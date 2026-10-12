# Generation quality

Fanfiction. Not canon. Measured on 2026-10-13 with Qwen3-8B Q4_K_M through llama.cpp. Mock prose was not substituted.

The scene is the prologue beat “Phòng làm việc sau cơn giận”. Target: 900 Vietnamese words. Files are under `data/generated/volume17/`.

| Version | Words | Requests | Result |
| --- | --- | --- | --- |
| v1 | 840 | 5 | Over the 60 percent length gate. The required sentence is repeated, and later paragraphs restate the same decision. Kept as `prologue-scene-1.v1.md`. |
| v2 | 351 | 9 | Later chunks repeated long sentences and were discarded. Marked incomplete: 351/900. |
| v3 | 629 | 6 | Latest file, `prologue-scene-1.md`. Length is above 60 percent of 900 and under the 85 percent stop used by the chunker. |

v3 measurements, from `prologue-scene-1.json`:

- Vietnamese words: 629
- Prompt tokens on the five prose calls: 295, 539, 539, 531, 532
- Completion tokens: 278, 265, 294, 274, 341
- Speed: 4.33 to 6.93 tokens/second
- Wall time: 317.83 seconds, plus one state-diff call
- State diff finished `truncation` at 220 tokens. The stored diff is the fallback built from required events, not a parsed model object.
- Launch plan: context 4096, 36 GPU layers, mode label `gpu`, estimate 5782 MB. That label is the VRAM planner’s choice. The benchmark in `docs/INFERENCE_BENCHMARK.md` shows the same `-ngl 36` does not move VRAM and runs at about 5 tokens/second because `libcudart.so.12` and `libcublas.so.12` are missing.

Validation of v3:

- High: the exact required sentence is absent: “Ainz giữ nguyên lệnh chuẩn bị tiêu diệt Thần quyền quốc Slane.”
- The draft still states that Ainz orders a campaign to destroy Slane, in other wording.
- Albedo is referred to with “anh”. That does not match the character.
- Closing lines restate “Slane sẽ không tồn tại nữa.”
- No Chinese characters in v3. v1 contained one.

This scene is not approved prose and is not a finished chapter. The other 51 scenes have not been generated. A 60,000-word run at about 5 tokens/second is several hours and is not started. The outline in `docs/VOLUME_17_OUTLINE.md` is the plan awaiting approval. The older approved mock scene in the project database was left in place.

Automated tests: 25 passed, including completion budget, multi-call plain text, the length gate, and coverage that does not treat notes as sixteen ingested volumes.
