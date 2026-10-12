from pathlib import Path

from sqlalchemy import text

from app.db.models import Segment
from app.retrieval.context import build_context_pack
from app.retrieval.hybrid import hybrid_search
from app.services.library import import_file


def test_hybrid_search_returns_the_shalltear_note_with_evidence(app, session):
    notes = Path(__file__).resolve().parents[1] / "data" / "seed" / "volume_16_study_notes.json"
    source, _ = import_file(
        session,
        app.state.settings,
        app.state.embedder,
        app.state.index,
        notes,
        title="notes",
        source_type="user_notes",
        canon_level="USER_INTERPRETATION",
        license_status="original-structured-notes",
    )
    alternate = Segment(
        id="alt-1",
        source_id=source.id,
        ordinal=99,
        text="Trong một vũ trụ khác, Shalltear Bloodfallen không liên quan tới Bảo vật thế giới.",
        canon_level="ALTERNATE_UNIVERSE",
        timeline="alternate",
    )
    session.add(alternate)
    session.execute(
        text("INSERT INTO segment_fts(text, segment_id) VALUES (:text, :id)"),
        {"text": alternate.text, "id": alternate.id},
    )
    app.state.index.add([alternate.id], app.state.embedder.embed([alternate.text]))
    session.commit()
    hits = hybrid_search(session, app.state.embedder, app.state.index, "Shalltear Bloodfallen Bảo vật thế giới")
    assert hits
    assert "Shalltear" in hits[0].text
    assert hits[0].source_id == source.id
    assert all(hit.timeline != "alternate" for hit in hits)
    pack = build_context_pack(session, viewpoint="Ainz Ooal Gown", hits=hits, token_budget=800)
    kinds = {section["kind"] for section in pack["sections"]}
    assert "viewpoint_profile" in kinds
    assert "Albedo đang giữ một đơn vị bí mật tìm các Đấng Tối Cao khác" in pack["prohibited_knowledge"]
    secret = "Albedo đang giữ một đơn vị bí mật tìm các Đấng Tối Cao khác"
    assert all(secret not in section["text"] for section in pack["sections"])
    assert all("Đơn vị bí mật của Albedo" not in section["text"] for section in pack["sections"])
