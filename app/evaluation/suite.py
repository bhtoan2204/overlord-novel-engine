"""Measurable checks. This module does not invent prose-quality percentages."""

from app.knowledge.schemas import SceneSpec
from app.narrative.validators import run_heuristics


def scene_metrics(session, spec: SceneSpec, prose: str) -> dict:
    reports = run_heuristics(session, spec, prose)
    high = sum(1 for report in reports for issue in report["issues"] if issue["severity"] == "high")
    required = len(spec.required_events)
    covered = sum(1 for event in spec.required_events if event.lower() in prose.lower())
    return {
        "required_events": required,
        "required_events_present": covered,
        "high_severity_issues": high,
        "scores": {report["validator"]: report["scores"] for report in reports},
        "word_count": len(prose.split()),
    }


def compare_outputs(session, spec: SceneSpec, left: str, right: str, left_name: str, right_name: str) -> dict:
    return {
        left_name: scene_metrics(session, spec, left),
        right_name: scene_metrics(session, spec, right),
        "note": "Comparison uses the heuristic validators only. It is not a human quality rating.",
    }
