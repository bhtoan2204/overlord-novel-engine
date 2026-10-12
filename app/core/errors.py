class EngineError(Exception):
    """Expected application failure with a message safe to show in the UI."""


class ResourceError(EngineError):
    pass


class InferenceError(EngineError):
    pass


class WorkflowError(EngineError):
    pass


class ValidationFailed(EngineError):
    pass
