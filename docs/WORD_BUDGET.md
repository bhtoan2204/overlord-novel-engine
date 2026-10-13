# Word budget

The reconciled plan is 350,000 Vietnamese words. `budget_audit(planned_volume())` reports no mismatches. The acceptable finished range is 315,000–385,000.

| Unit | Count | How the sum is built |
| --- | --- | --- |
| Volume | 1 | 350,000 |
| Chapters, including prologue, one interlude, and epilogue | 11 | 16,500 + 38,500 × 6 + 14,000 + 39,500 + 35,000 + 14,000 |
| Parts | 52 | Each part target is 5,000–15,000 |
| Scenes | 270 | Scene targets sum to their part |
| Beats | 1,352 | Each beat is 150–350 words and the beats sum to their scene |

The six 38,500-word units are chapters 1, 2, 3, 4, 6, and 7. Chapter 5 is 39,500. Chapter 8 is 35,000. The prologue is 16,500. The interlude and epilogue are 14,000 each. They are required before the volume can be marked complete.

A stored project that was built at the earlier 200,000-word plan keeps its accepted prose. The campaign raises each matching part’s target and adds the missing scenes. It does not delete chunks, and it does not raise a target merely to clear a review failure.

If a chapter is dropped because a required plotline is missing, the allocated sum falls below 350,000 and `budget_problems` records the gap. The plan does not rescale the remaining chapters to hide that gap.

Local source text is still the Volume 16 study notes. Volumes 1–16 are not ingested. Missing full text is a coverage warning. It does not by itself block manuscript completion.
