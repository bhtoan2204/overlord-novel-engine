from app.core.workflow import WorkflowState, can_transition


def test_linear_progress_and_interrupts():
    assert can_transition(WorkflowState.OUTLINE_CREATED, WorkflowState.OUTLINE_APPROVED)
    assert not can_transition(WorkflowState.NOT_STARTED, WorkflowState.VOLUME_COMPLETED)
    assert can_transition(WorkflowState.SCENE_GENERATING, WorkflowState.PAUSED)
    assert can_transition(WorkflowState.PAUSED, WorkflowState.SCENE_GENERATING)
    assert can_transition(WorkflowState.FAILED, WorkflowState.SCENE_GENERATING)
