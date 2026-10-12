"""Ratings adjust later prompts. They never start a fine-tune."""

from sqlalchemy.orm import Session

from app.db.models import Feedback

AXES = (
    "plot_quality",
    "character_accuracy",
    "dialogue",
    "emotional_impact",
    "worldbuilding",
    "suspense",
    "overall",
)

ADVICE = {
    "plot_quality": "Siết quan hệ nhân quả, bớt việc xảy ra cho đủ trang.",
    "character_accuracy": "Bám động cơ và phần hiểu biết của từng người.",
    "dialogue": "Tăng lời thoại có mục đích, mỗi người một cách nói.",
    "emotional_impact": "Để cảm xúc hiện qua lựa chọn, không qua tính từ.",
    "worldbuilding": "Chỉ đưa luật thế giới khi nó đổi quyết định của cảnh.",
    "suspense": "Giữ lại một thông tin quan trọng đến đúng lúc.",
    "overall": "Ưu tiên cảnh có hệ quả chính trị hoặc chiến lược.",
}


def preference_instructions(session: Session, project_id: str) -> str:
    rows = session.query(Feedback).filter(Feedback.project_id == project_id).all()
    if not rows:
        return ""
    totals = {axis: 0.0 for axis in AXES}
    for row in rows:
        for axis in AXES:
            totals[axis] += float((row.ratings or {}).get(axis) or 0)
    notes = []
    for axis, total in totals.items():
        average = total / len(rows)
        if average and average < 3.5:
            notes.append(ADVICE[axis])
    comments = [row.comment.strip() for row in rows if row.comment and row.comment.strip()]
    if comments:
        notes.append("Ghi chú gần nhất của người đọc: " + comments[-1][:400])
    return " ".join(notes)
