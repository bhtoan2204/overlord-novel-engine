"""llama.cpp server lifecycle and OpenAI-compatible chat client."""

import json
import os
import subprocess
import time
from pathlib import Path

import httpx
import yaml

from app.core.config import Settings
from app.core.errors import InferenceError, ResourceError
from app.core.logging import get_logger, strip_think
from app.inference.base import GenerationResult, GenerationSettings
from app.inference.budget import completion_budget
from app.inference.gate import GATE
from app.inference.resources import LaunchPlan, apply_cpu_affinity, plan_launch, probe_gpu

log = get_logger(__name__)


def load_registry(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    models = data.get("models", {})
    for key, model in models.items():
        model["key"] = key
    return data


class LlamaCppBackend:
    name = "llama.cpp"

    def __init__(self, settings: Settings):
        self.settings = settings
        self.process: subprocess.Popen | None = None
        self.plan: LaunchPlan | None = None
        self.model_key = settings.active_model
        self._library_dir = settings.llama_server_bin.parent

    def resolve_model(self) -> tuple[str, dict, Path]:
        registry = load_registry(self.settings.model_registry_path)
        models = registry["models"]
        order = [self.settings.active_model, "qwen3-4b-q4"]
        seen = []
        for key in order:
            model = models.get(key)
            if not model:
                continue
            path = self.settings.data_dir / "models" / model["file"]
            seen.append(str(path))
            if path.exists() and path.stat().st_size > 1_000_000:
                return key, model, path
        raise InferenceError(
            "No GGUF checkpoint is installed. Run scripts/download_models.sh. Looked for: " + ", ".join(seen)
        )

    def ensure_started(self) -> LaunchPlan:
        if self.process and self.process.poll() is None and self.plan:
            return self.plan
        GATE.acquire("inference")
        try:
            key, model, path = self.resolve_model()
            gpu = probe_gpu()
            plan = plan_launch(
                model,
                gpu,
                self.settings.context_tokens,
                self.settings.vram_budget_mb,
                self.settings.vram_reserve_mb,
                self.settings.cpu_limit_percent,
                self.settings.kv_cache_type,
                self.settings.wait_for_vram,
                self.settings.vram_wait_seconds,
            )
            apply_cpu_affinity(plan.cpu_range)
            command = [
                str(self.settings.llama_server_bin),
                "-m",
                str(path),
                "-c",
                str(plan.context_tokens),
                "-ngl",
                str(plan.gpu_layers),
                "-t",
                str(plan.cpu_threads),
                "-tb",
                str(plan.cpu_threads),
                "--cpu-range",
                plan.cpu_range,
                "-b",
                str(plan.batch_size),
                "-ub",
                str(plan.ubatch_size),
                "--host",
                self.settings.llama_server_host,
                "--port",
                str(self.settings.llama_server_port),
                "--jinja",
                "--reasoning",
                "off",
                "--no-reasoning-preserve",
                "--alias",
                key,
                "--sleep-idle-seconds",
                str(self.settings.idle_unload_seconds),
            ]
            if plan.kv_cache_type and plan.kv_cache_type != "f16":
                command.extend(["-ctk", plan.kv_cache_type, "-ctv", plan.kv_cache_type])
            environment = os.environ.copy()
            cuda_lib = self.settings.root / "third_party" / "cuda12" / "usr" / "lib" / "x86_64-linux-gnu"
            library_paths = [str(self._library_dir)]
            if cuda_lib.exists():
                library_paths.insert(0, str(cuda_lib))
            environment["LD_LIBRARY_PATH"] = os.pathsep.join(library_paths + [environment.get("LD_LIBRARY_PATH", "")])
            log.info(
                "starting llama-server model=%s context=%s gpu_layers=%s mode=%s",
                key,
                plan.context_tokens,
                plan.gpu_layers,
                plan.mode,
            )
            log_path = self.settings.data_dir / "logs" / "llama-server.log"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            self._log_handle = log_path.open("a", encoding="utf-8")
            self.process = subprocess.Popen(
                command,
                env=environment,
                stdout=self._log_handle,
                stderr=self._log_handle,
                text=True,
            )
            self._wait_until_healthy()
            self.plan = plan
            self.model_key = key
            return plan
        except Exception:
            self.stop()
            raise

    def _wait_until_healthy(self) -> None:
        url = f"http://{self.settings.llama_server_host}:{self.settings.llama_server_port}/health"
        deadline = time.monotonic() + 180
        last = ""
        while time.monotonic() < deadline:
            if self.process and self.process.poll() is not None:
                raise InferenceError("llama-server exited early. See data/logs/llama-server.log.")
            try:
                response = httpx.get(url, timeout=2.0)
                if response.status_code == 200:
                    return
                last = response.text[:200]
            except httpx.HTTPError as exc:
                last = str(exc)
            time.sleep(1)
        raise InferenceError(f"llama-server did not become healthy: {last}")

    def count_tokens(self, messages: list[dict]) -> int:
        """Ask llama-server to count the prompt. Fall back to a word estimate."""
        self.ensure_started()
        url = f"http://{self.settings.llama_server_host}:{self.settings.llama_server_port}/tokenize"
        content = "\n".join(message.get("content") or "" for message in messages)
        try:
            response = httpx.post(url, json={"content": content}, timeout=30.0)
            if response.status_code == 200:
                data = response.json()
                tokens = data.get("tokens")
                if isinstance(tokens, list):
                    return len(tokens)
                if isinstance(data.get("tokens"), int):
                    return int(data["tokens"])
        except httpx.HTTPError:
            pass
        from app.core.text import estimate_tokens

        return estimate_tokens(content) + 32

    def generate(self, messages: list[dict], settings: GenerationSettings) -> GenerationResult:
        self.ensure_started()
        context_limit = self.plan.context_tokens if self.plan else self.settings.context_tokens
        prompt_tokens = self.count_tokens(messages)
        max_tokens = completion_budget(context_limit, prompt_tokens, settings.max_tokens)
        body = {
            "messages": messages,
            "temperature": settings.temperature,
            "seed": settings.seed,
            "max_tokens": max_tokens,
            "chat_template_kwargs": {"enable_thinking": False},
        }
        if settings.json_object:
            body["response_format"] = {"type": "json_object"}
        url = f"http://{self.settings.llama_server_host}:{self.settings.llama_server_port}/v1/chat/completions"
        try:
            response = httpx.post(url, json=body, timeout=600.0)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            detail = ""
            response_obj = getattr(exc, "response", None)
            if response_obj is not None:
                detail = response_obj.text[:500]
            if "exceed_context_size_error" in detail:
                raise InferenceError(f"Context overflow: {detail}") from exc
            raise InferenceError(f"llama-server request failed: {exc} {detail}") from exc
        data = response.json()
        choice = data["choices"][0]
        message = choice["message"]
        text = strip_think(message.get("content") or "")
        usage = data.get("usage") or {}
        finish = choice.get("finish_reason") or "stop"
        if finish == "length":
            finish = "truncation"
        log.info(
            "generation task=%s prompt_tokens=%s completion_tokens=%s finish=%s",
            settings.task,
            usage.get("prompt_tokens", prompt_tokens),
            usage.get("completion_tokens", 0),
            finish,
        )
        return GenerationResult(
            text=text,
            prompt_tokens=int(usage.get("prompt_tokens") or prompt_tokens),
            completion_tokens=int(usage.get("completion_tokens") or 0),
            model=self.model_key,
            finish_reason=finish,
        )

    def health(self) -> dict:
        running = bool(self.process and self.process.poll() is None)
        installed = self.settings.llama_server_bin.exists()
        return {
            "ok": installed,
            "backend": self.name,
            "running": running,
            "model": self.model_key,
            "plan": None if not self.plan else self.plan.__dict__,
            "binary": str(self.settings.llama_server_bin),
        }

    def stop(self) -> None:
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                self.process.kill()
        self.process = None
        self.plan = None
        handle = getattr(self, "_log_handle", None)
        if handle is not None:
            handle.close()
            self._log_handle = None
        GATE.release("inference")


def select_backend(settings: Settings):
    if settings.inference_backend == "mock":
        from app.inference.base import ScriptedBackend

        return ScriptedBackend()
    if settings.inference_backend == "llama":
        return LlamaCppBackend(settings)
    raise ResourceError(f"Unknown inference backend: {settings.inference_backend}")
