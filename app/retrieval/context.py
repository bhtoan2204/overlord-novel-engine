"""Bounded context packages. A viewpoint character does not receive the whole archive."""

from sqlalchemy.orm import Session

from app.core.canon import MAIN_TIMELINE, canon_rank
from app.core.text import estimate_tokens, tokens
from app.db.models import Assertion, Character, Plotline, WorldRule
from app.retrieval.hybrid import Hit


def build_context_pack(
    session: Session,
    *,
    viewpoint: str | None,
    hits: list[Hit],
    token_budget: int,
    as_of_order: int | None = None,
) -> dict:
    sections: list[dict] = []
    spent = 0

    def add(kind: str, text: str, evidence: str, confidence: float) -> None:
        nonlocal spent
        cost = estimate_tokens(text)
        if spent + cost > token_budget:
            return
        spent += cost
        sections.append(
            {"kind": kind, "text": text, "evidence": evidence, "confidence": round(confidence, 3)}
        )

    character = None
    if viewpoint:
        character = session.query(Character).filter(Character.name == viewpoint).one_or_none()
        if character:
            add(
                "viewpoint_profile",
                f"{character.name}, chủng loài {character.race}, phe {character.faction}. "
                f"Tính cách: {character.personality}. Trạng thái hồ sơ: {character.current_status}.",
                character.evidence_source_id or "",
                character.confidence,
            )
            knowledge = character.knowledge_state or {}
            add(
                "viewpoint_knowledge",
                "Được biết: " + "; ".join(knowledge.get("knows") or []) + ". Có điều nhân vật này không biết; những điều đó chỉ nằm trong danh sách cấm, không được viết thành suy nghĩ của nhân vật.",
                character.evidence_source_id or "",
                character.confidence,
            )

    assertions = session.query(Assertion).filter(Assertion.timeline == MAIN_TIMELINE).all()
    hidden_values: list[str] = []
    grouped: dict[tuple[str, str], Assertion] = {}
    for assertion in assertions:
        if as_of_order is not None and assertion.as_of_order > as_of_order:
            continue
        if assertion.kind == "fact" and assertion.audience == "restricted":
            knowers = set(assertion.knowers or [])
            if viewpoint not in knowers:
                hidden_values.append(assertion.value)
                continue
        if assertion.kind == "belief" and assertion.believer != viewpoint:
            continue
        key = (assertion.subject_name, assertion.predicate)
        current = grouped.get(key)
        if current is None or canon_rank(assertion.canon_level) > canon_rank(current.canon_level):
            grouped[key] = assertion
    for assertion in grouped.values():
        if assertion.canon_level == "AI_GENERATED":
            continue
        add(
            "fact" if assertion.kind == "fact" else assertion.kind,
            f"{assertion.subject_name} / {assertion.predicate}: {assertion.value}",
            assertion.evidence_source_id or "",
            assertion.confidence,
        )

    for rule in session.query(WorldRule).all():
        add("rule", f"[{rule.category}] {rule.statement}", rule.evidence_source_id or "", rule.confidence)

    for plotline in session.query(Plotline).filter(Plotline.timeline == MAIN_TIMELINE, Plotline.current_status != "resolved").all():
        questions = "; ".join(plotline.unresolved_questions or [])
        summary = f"{plotline.title}. Câu hỏi mở: {questions}"
        if _leaks_secret(summary, hidden_values):
            continue
        add("plotline", summary, ",".join(plotline.supporting_evidence or []), 0.6)

    for hit in hits:
        add("source", hit.text, hit.source_id, hit.score)

    prohibited = []
    if character:
        prohibited.extend(character.knowledge_state.get("does_not_know") or [])
    prohibited.extend(value for value in hidden_values if value not in prohibited)
    return {"sections": sections, "token_estimate": spent, "prohibited_knowledge": prohibited}


def _leaks_secret(text: str, secrets: list[str]) -> bool:
    text_tokens = set(tokens(text))
    for secret in secrets:
        overlap = {token for token in tokens(secret) if len(token) > 2 and token in text_tokens}
        if len(overlap) >= 3:
            return True
    return False
