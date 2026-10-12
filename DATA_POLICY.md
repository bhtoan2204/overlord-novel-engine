# Data policy

The index at https://meobietbay.com/overlord/ is a catalog reference. It is not permission to copy the novels into this database or into a training set.

## What the discovery module does

`app/ingestion/discovery.py` fetches `robots.txt`, and only if the user-agent is allowed does it fetch the index URL. It keeps anchor titles and links, capped at 200 characters. It does not store article bodies. On 12 October 2026, `https://meobietbay.com/robots.txt` disallowed `/wp-admin/` and did not disallow `/overlord/`.

The module sleeps for the configured rate limit (default 2 seconds) between the robots check and the page fetch. It does not ignore `robots.txt` and it does not send a spoofed browser identity beyond the declared `OverlordNovelEngine` user agent.

## What may be imported

TXT, Markdown, EPUB, JSON, and PDF that you supply, with a filled license or permission field. Import is idempotent on a SHA-256 of the NFC-normalized text.

Every source row stores: id, title, url, type, volume, chapter, segment order, timeline, canon level, license, language, ingestion time, and checksum.

Canon levels:

- `PRIMARY_CANON`
- `CANON_SUPPLEMENT`
- `ALTERNATE_UNIVERSE`
- `WEB_NOVEL_CONTINUITY`
- `SECONDARY_REFERENCE`
- `USER_INTERPRETATION`
- `AI_GENERATED`

Primary canon wins over lower ranks. An alternate-universe event is never copied onto the main timeline. Generated prose does not become source canon.

The bundled `data/seed/volume_16_study_notes.json` is an original study summary. Its canon level is `USER_INTERPRETATION` and its license is `original-structured-notes`. It is not a substitute for the books, and `training_allowed` is false.

## Training

Fine-tuning stays off unless `OVERLORD_TRAINING_ENABLED=true` and the CLI flag `--enable-training` are both set. Even then, `scripts/train_qlora.py` refuses to start a job by itself. A record is eligible only when `training_allowed` is true and the license is one of `apache-2.0`, `mit`, `cc-by-4.0`, or `original-notes-with-training-rights`. The study notes are not on that list.

## Generated text

Exports include a notice that the work is unofficial fan fiction. The writer is instructed to use an original Vietnamese narrative voice and the glossary in `app/core/disclaimer.py`, and not to imitate the original author's prose.
