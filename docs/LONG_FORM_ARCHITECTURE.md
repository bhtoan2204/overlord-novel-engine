# Long-form architecture

Fanfiction generation is stored apart from canon rows.

## Hierarchy

`outline_nodes.level` is one of volume, arc, chapter, part, scene, beat. A part is the parent of scenes. A scene is not a part.

Each node stores target words, actual words, completion status, a checkpoint, revision history, and continuity facts. Prose lives in `prose_chunks`, one row per attempt, with a unique `(beat_id, ordinal)`. Accepted chunks are the only rows that count toward the word total.

## Completion

States used on nodes: PLANNED, GENERATING, PAUSED, NEEDS_REVIEW, COMPLETED. A part becomes COMPLETED only when every scene and beat under it is completed and the accepted word count is at least 90 percent of the part target. A short transition can set `short_transition` and a minimum; the Volume 17 plan does not mark any part that way.

A chapter is COMPLETED only when every part is. The volume is COMPLETED only when every chapter is, and the outline includes a prologue, at least one main chapter, and an epilogue. `next_scene()` returning nothing does not finish the volume.

A job stops at `max_chunks_per_job` (default 24, raised for a single part run) and leaves the part PAUSED, not complete.

## Writing loop

`generate_next_chunk` loads the next open beat, the structured facts on the scene, part, and chapter, and the tail of that beat. It asks for one chunk. A repeated sentence, a duplicate paragraph, an empty reply, or a truncation that does not end a sentence is stored as REJECTED and does not add words. After three rejections the beat is NEEDS_REVIEW. Earlier accepted chunks stay.

Restarting continues at the next ordinal. It does not insert the accepted text again.

## Memory

Continuity facts are appended, not replaced by a shorter summary. Generated chunks are not written into canon source tables. Retrieval for canon still excludes AI-generated assertions.

## What the 629-word file was

`data/generated/volume17/prologue-scene-1.md` is an earlier incomplete scene. It is not this part, and it is not the volume.
