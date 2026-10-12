# Generation audit

The 629-word file was an incomplete scene, not a volume. The causes in the code at that time:

- `write_scene_chunks` stopped after seven model calls.
- A repeated chunk ended the loop once the draft had reached 60 percent of a 900-word scene target.
- The outline had 52 scenes and no part level, so a scene was the largest unit the writer knew.
- Scene targets were about 900–1,200 words because the volume target was 60,000.
- `next_scene()` returning no scene could set the workflow to VOLUME_COMPLETED.
- The length validator treated 60 percent of target as the failure line, so anything above that could be approved.
- CUDA was requested with `-ngl 36`, but `libcudart.so.12` and `libcublas.so.12` are not on the library path, so generation stayed near 5 tokens/second. The launch plan still labeled the mode `gpu`.

Changes that address those causes:

- Chunk count follows the remaining beats and the job cap, not a fixed seven.
- A repeated or truncated chunk is rejected and stored. It does not complete the part.
- The acceptance line for a standard part is 90 percent of its own target.
- Parts, scenes, and beats have targets that sum to 200,000 words.
- Volume completion goes through `refresh_rollup`, which checks every chapter kind.
- Replacing an outline copies selected drafts into `preserved_drafts` before the old nodes are removed.

Still true:

- Volumes 1–16 are not ingested.
- The hash embedder is still the default. The E5 class exists and is not installed as the default.
- GPU offload is not happening on this machine.
- The full volume has not been generated.
