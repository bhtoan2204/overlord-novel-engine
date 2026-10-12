from app.db.models import Character, OutlineNode


def test_end_to_end_smoke(client, app):
    sample = client.post("/library/sample")
    assert sample.status_code == 200
    assert "Ghi chú" in sample.text
    verified = client.post("/planner/verify")
    assert verified.status_code == 200
    created = client.post("/planner/create")
    assert created.status_code == 200
    assert "Lời mở" in created.text
    blocked = client.post("/generate/step")
    assert blocked.status_code == 200
    assert "Approve the outline" in blocked.text
    approved = client.post("/planner/approve")
    assert "OUTLINE_APPROVED" in approved.text
    generated = client.post("/generate/step")
    assert generated.status_code == 200
    assert "scene-approved" in generated.text
    reader = client.get("/reader")
    assert "Phòng làm việc sau cơn giận" in reader.text
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["ok"] is True
    markdown = client.get("/api/markdown")
    body = markdown.json()["markdown"]
    assert "fanfiction không chính thức" in body
    assert "Ainz" in body
    epub = client.post("/export/epub")
    assert epub.status_code == 200
    assert epub.content[:4] == b"PK\x03\x04"
    pdf = client.post("/export/pdf")
    assert pdf.status_code == 200
    assert pdf.content.startswith(b"%PDF")
    factory = app.state.session_factory
    session = factory()
    try:
        ainz = session.query(Character).filter(Character.name == "Ainz Ooal Gown").one()
        assert ainz.canon_level == "USER_INTERPRETATION"
        assert "nông dân" not in ainz.current_status
        assert session.query(OutlineNode).filter(OutlineNode.status == "approved", OutlineNode.level == "scene").count() == 1
    finally:
        session.close()
    again = client.post("/library/sample")
    assert "sample-already-present" in again.text


def test_dashboard_and_settings(client):
    page = client.get("/")
    assert page.status_code == 200
    assert "Workflow" in page.text
    saved = client.post(
        "/settings",
        data={
            "context_tokens": 4096,
            "vram_budget_mb": 8000,
            "vram_reserve_mb": 3000,
            "cpu_limit_percent": 40,
            "temperature_write": 0.7,
            "scene_target_words": 900,
            "cooldown_seconds": 0,
            "active_model": "qwen3-4b-q4",
            "planner_mode": "deterministic",
            "inference_backend": "mock",
        },
    )
    assert saved.status_code == 200
    assert "4096" in saved.text
