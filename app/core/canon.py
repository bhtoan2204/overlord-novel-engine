"""Canon trust order. Higher rank wins. Alternate-universe facts never enter the main timeline."""

from enum import Enum


class CanonLevel(str, Enum):
    PRIMARY_CANON = "PRIMARY_CANON"
    CANON_SUPPLEMENT = "CANON_SUPPLEMENT"
    WEB_NOVEL_CONTINUITY = "WEB_NOVEL_CONTINUITY"
    SECONDARY_REFERENCE = "SECONDARY_REFERENCE"
    USER_INTERPRETATION = "USER_INTERPRETATION"
    ALTERNATE_UNIVERSE = "ALTERNATE_UNIVERSE"
    AI_GENERATED = "AI_GENERATED"


CANON_RANK: dict[str, int] = {
    CanonLevel.PRIMARY_CANON.value: 100,
    CanonLevel.CANON_SUPPLEMENT.value: 80,
    CanonLevel.WEB_NOVEL_CONTINUITY.value: 50,
    CanonLevel.SECONDARY_REFERENCE.value: 40,
    CanonLevel.USER_INTERPRETATION.value: 30,
    CanonLevel.ALTERNATE_UNIVERSE.value: 10,
    CanonLevel.AI_GENERATED.value: 0,
}

MAIN_TIMELINE = "main"


def canon_rank(level: str) -> int:
    return CANON_RANK.get(level, 0)


def beats(challenger: str, incumbent: str) -> bool:
    """True when challenger should replace incumbent on the main timeline."""
    if challenger == CanonLevel.ALTERNATE_UNIVERSE.value:
        return False
    if challenger == CanonLevel.AI_GENERATED.value:
        return False
    return canon_rank(challenger) > canon_rank(incumbent)
