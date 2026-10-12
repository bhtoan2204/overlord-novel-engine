from app.core.canon import CanonLevel, beats


def test_primary_canon_beats_lower_sources():
    assert beats(CanonLevel.PRIMARY_CANON.value, CanonLevel.USER_INTERPRETATION.value)
    assert beats(CanonLevel.CANON_SUPPLEMENT.value, CanonLevel.SECONDARY_REFERENCE.value)


def test_alternate_and_generated_never_override_main_canon():
    assert not beats(CanonLevel.ALTERNATE_UNIVERSE.value, CanonLevel.USER_INTERPRETATION.value)
    assert not beats(CanonLevel.AI_GENERATED.value, CanonLevel.PRIMARY_CANON.value)
    assert not beats(CanonLevel.USER_INTERPRETATION.value, CanonLevel.PRIMARY_CANON.value)
