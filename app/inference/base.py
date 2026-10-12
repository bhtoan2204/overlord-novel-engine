"""Inference backends. Tests use the scripted backend. llama.cpp is used for local generation."""

from dataclasses import dataclass, field
from typing import Protocol

@dataclass
class GenerationSettings:
    temperature: float
    seed: int
    max_tokens: int
    task: str
    json_schema: dict | None = None
    json_object: bool = False


@dataclass
class GenerationResult:
    text: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    model: str = ""
    finish_reason: str = "stop"


class ChatBackend(Protocol):
    name: str

    def generate(self, messages: list[dict], settings: GenerationSettings) -> GenerationResult:
        ...

    def health(self) -> dict:
        ...


class ScriptedBackend:
    """Deterministic backend. Responses may be strings or callables of the user message."""

    name = "scripted"

    def __init__(self, responses: list | None = None):
        self.responses = list(responses or [])
        self.calls: list[list[dict]] = []

    def generate(self, messages: list[dict], settings: GenerationSettings) -> GenerationResult:
        self.calls.append(messages)
        if not self.responses:
            from app.inference.mock_content import respond

            text = respond(messages, settings)
        else:
            item = self.responses.pop(0)
            user = messages[-1]["content"] if messages else ""
            text = item(user) if callable(item) else item
        return GenerationResult(text=text, model=self.name)

    def health(self) -> dict:
        return {"ok": True, "backend": self.name}
