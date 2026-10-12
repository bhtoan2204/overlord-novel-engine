"""What is actually imported, as opposed to a link that was only discovered."""

from sqlalchemy.orm import Session

from app.db.models import CatalogEntry, Source

# Public volume titles. Presence here is a checklist, not ingested text.
VOLUME_TITLES = {
    1: "The Undead King",
    2: "The Dark Warrior",
    3: "The Bloody Valkyrie",
    4: "The Lizardman Heroes",
    5: "The Men in the Kingdom I",
    6: "The Men in the Kingdom II",
    7: "The Invaders of the Great Tomb",
    8: "The Two Leaders",
    9: "The Magic Caster of Destroy",
    10: "The Ruler of Conspiracy",
    11: "The Craftsman of Dwarf",
    12: "The Paladin of the Holy Kingdom I",
    13: "The Paladin of the Holy Kingdom II",
    14: "The Witch of the Falling Kingdom",
    15: "The Half-Elf God-kin I",
    16: "The Half-Elf God-kin II",
}


def coverage_report(session: Session) -> dict:
    sources = session.query(Source).all()
    by_volume: dict[int, list[Source]] = {}
    summaries = []
    for source in sources:
        if source.volume_number:
            by_volume.setdefault(source.volume_number, []).append(source)
        if source.source_type in {"user_notes", "summary"} or source.canon_level == "USER_INTERPRETATION":
            summaries.append(source)
    volumes = []
    for number, title in VOLUME_TITLES.items():
        rows = by_volume.get(number, [])
        full_text = [row for row in rows if row.word_count >= 500 and row.canon_level in {"PRIMARY_CANON", "CANON_SUPPLEMENT"}]
        summary_rows = [row for row in rows if row not in full_text]
        if full_text:
            status = "full_text"
        elif summary_rows:
            status = "summary_only"
        else:
            status = "missing"
        volumes.append(
            {
                "volume": number,
                "title": title,
                "status": status,
                "sources": len(rows),
                "words": sum(row.word_count for row in rows),
            }
        )
    links = session.query(CatalogEntry).count()
    return {
        "volumes": volumes,
        "full_text_volumes": sum(1 for item in volumes if item["status"] == "full_text"),
        "summary_notes": len(summaries),
        "discovered_links": links,
        "note": "Discovered URLs are not ingested chapters. Missing means no authorized file has been imported.",
    }
