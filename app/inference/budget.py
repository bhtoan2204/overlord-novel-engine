"""Completion room is whatever the context has left after the real prompt."""

from app.core.errors import InferenceError


def completion_budget(context_tokens: int, prompt_tokens: int, requested: int, slack: int = 32) -> int:
    """Return how many new tokens fit. Raises when the prompt itself does not fit."""
    if context_tokens <= 0:
        raise InferenceError("Context size is not set.")
    if prompt_tokens < 0:
        prompt_tokens = 0
    room = context_tokens - prompt_tokens - slack
    if room < 32:
        raise InferenceError(
            f"Prompt uses {prompt_tokens} tokens and does not fit in a context of {context_tokens}."
        )
    return max(32, min(int(requested), room))
