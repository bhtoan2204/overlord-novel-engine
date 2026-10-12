# Generation pipeline

Language: Vietnamese. Form: unofficial fan-fiction continuation. Start: immediately after Volume 16, as described by the imported notes. The bundled notes say Ainz has ordered preparation for war on the Slane Theocracy after learning who used a World Item on Shalltear, Antilene is imprisoned, and Decem is dead. Those notes are `USER_INTERPRETATION`, not a claim that this program holds the text of the novels.

## States

`NOT_STARTED` → `SOURCES_PREPARED` → `KNOWLEDGE_EXTRACTED` → `CANON_VERIFIED` → `OUTLINE_CREATED` → `OUTLINE_APPROVED` → scene loop (`CHAPTER_PLANNED`, `SCENE_GENERATING`, `SCENE_VALIDATING`, `SCENE_REVISING`, `SCENE_APPROVED`, `STATE_COMMITTED`) → `CHAPTER_COMPLETED` → `VOLUME_COMPLETED`.

`FAILED`, `PAUSED`, and `CANCELLED` can interrupt an active state. Resume continues from the next scene whose status is not `approved`.

## Outline

The deterministic planner (`app/narrative/planner.py`) builds:

Volume → arc → chapter → scene → beat

Chapters are skipped when their plotline keys are not in the knowledge base. Each chapter records what it is caused by. Uncertainties on the plotlines are kept as alternatives, including the rejected branch of destroying the Theocracy in a single night. That branch is not selected, because the notes treat the World Item as still unlocated. Nothing in the outline is a prediction of the unpublished book.

Target length defaults to 52000 words, split across the scenes and clamped between 700 and 2200 words per scene. The whole volume is never one model call.

Approve the outline before generation. You can edit a chapter summary until you approve it.

## One scene

The writer receives a scene specification: viewpoint, location, time, objective, participants, what that person knows, required events, prohibited contradictions, word target, previous summary, tone, and outcome.

Validators, each with its own scores:

- Canon: species and status contradictions, forbidden phrases, alternate-universe text presented as main history
- Character: viewpoint secrets, unmotivated personality breaks
- Plot: missing required events, stacked coincidence, a scene far under the target length
- Language: repeated sentences, a dialogue scene with no dialogue

A high-severity issue triggers a revision, up to three iterations. If the canon and character consistency scores differ by 3 or more, the reports are kept and the scene is flagged for a person. It is not auto-approved. There is no single score that counts as proof of quality.

The state diff may record deaths, locations, alliances, and discoveries. It is rejected if it tries to mark a canon mutation, or if it resurrects someone with no mechanism. The canonical character row stays as imported.

## Preferences

Ratings on seven axes, plus a comment, are turned into extra writing instructions when an axis averages under 3.5. They do not start training.

## Checkpoints

After a committed scene the job row and `data/checkpoints/<project>.json` store the scene id. A crash during generation is recovered on the next boot as `PAUSED`.

## Export

Markdown, EPUB (ebooklib), and PDF (fpdf2 with DejaVu Sans, which covers Vietnamese). Each begins with the unofficial-work notice.
