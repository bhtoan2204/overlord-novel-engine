"""Generation workflow. Active states can pause, fail, or cancel. There is no infinite retry."""

from enum import Enum


class WorkflowState(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    SOURCES_PREPARED = "SOURCES_PREPARED"
    KNOWLEDGE_EXTRACTED = "KNOWLEDGE_EXTRACTED"
    CANON_VERIFIED = "CANON_VERIFIED"
    OUTLINE_CREATED = "OUTLINE_CREATED"
    OUTLINE_APPROVED = "OUTLINE_APPROVED"
    CHAPTER_PLANNED = "CHAPTER_PLANNED"
    SCENE_GENERATING = "SCENE_GENERATING"
    SCENE_VALIDATING = "SCENE_VALIDATING"
    SCENE_REVISING = "SCENE_REVISING"
    SCENE_APPROVED = "SCENE_APPROVED"
    STATE_COMMITTED = "STATE_COMMITTED"
    CHAPTER_COMPLETED = "CHAPTER_COMPLETED"
    VOLUME_COMPLETED = "VOLUME_COMPLETED"
    FAILED = "FAILED"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"


LINEAR: tuple[WorkflowState, ...] = (
    WorkflowState.NOT_STARTED,
    WorkflowState.SOURCES_PREPARED,
    WorkflowState.KNOWLEDGE_EXTRACTED,
    WorkflowState.CANON_VERIFIED,
    WorkflowState.OUTLINE_CREATED,
    WorkflowState.OUTLINE_APPROVED,
    WorkflowState.CHAPTER_PLANNED,
    WorkflowState.SCENE_GENERATING,
    WorkflowState.SCENE_VALIDATING,
    WorkflowState.SCENE_REVISING,
    WorkflowState.SCENE_APPROVED,
    WorkflowState.STATE_COMMITTED,
    WorkflowState.CHAPTER_COMPLETED,
    WorkflowState.VOLUME_COMPLETED,
)

TERMINAL = {WorkflowState.VOLUME_COMPLETED, WorkflowState.CANCELLED}
INTERRUPTING = {WorkflowState.FAILED, WorkflowState.PAUSED, WorkflowState.CANCELLED}
INTERRUPTED_SCENE_STATES = {
    WorkflowState.SCENE_GENERATING,
    WorkflowState.SCENE_VALIDATING,
    WorkflowState.SCENE_REVISING,
}

# States from which a scene may still be generated or resumed.
GENERATION_READY = {
    WorkflowState.OUTLINE_APPROVED,
    WorkflowState.CHAPTER_PLANNED,
    WorkflowState.SCENE_APPROVED,
    WorkflowState.STATE_COMMITTED,
    WorkflowState.CHAPTER_COMPLETED,
    WorkflowState.PAUSED,
    WorkflowState.FAILED,
}


def can_transition(current: WorkflowState, target: WorkflowState) -> bool:
    if current == target:
        return True
    if target in INTERRUPTING and current not in TERMINAL:
        return True
    if current == WorkflowState.PAUSED and target in GENERATION_READY | {
        WorkflowState.SCENE_GENERATING,
        WorkflowState.CHAPTER_PLANNED,
    }:
        return True
    if current == WorkflowState.FAILED and target in GENERATION_READY | {WorkflowState.SCENE_GENERATING}:
        return True
    try:
        left = LINEAR.index(current)
        right = LINEAR.index(target)
    except ValueError:
        return False
    return right == left + 1 or (current == WorkflowState.STATE_COMMITTED and target == WorkflowState.CHAPTER_PLANNED) or (
        current == WorkflowState.CHAPTER_COMPLETED and target == WorkflowState.CHAPTER_PLANNED
    ) or (current == WorkflowState.SCENE_APPROVED and target == WorkflowState.SCENE_GENERATING)
