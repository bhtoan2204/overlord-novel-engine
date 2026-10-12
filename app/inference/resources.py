"""VRAM and CPU policy. A configured budget is a launch plan, not a hard driver ceiling."""

import os
import subprocess
import time
from dataclasses import dataclass

import psutil

from app.core.errors import ResourceError


@dataclass
class GpuStatus:
    name: str
    total_mb: int
    used_mb: int
    free_mb: int
    available: bool
    detail: str = ""


@dataclass
class LaunchPlan:
    model_key: str
    context_tokens: int
    gpu_layers: int
    batch_size: int
    ubatch_size: int
    cpu_threads: int
    cpu_range: str
    mode: str
    reason: str
    estimated_vram_mb: int
    kv_cache_type: str = "f16"


def parse_nvidia_smi(csv_text: str) -> GpuStatus:
    line = ""
    for candidate in csv_text.splitlines():
        if candidate.strip() and "name" not in candidate.lower():
            line = candidate.strip()
            break
    if not line:
        return GpuStatus("unavailable", 0, 0, 0, False, "nvidia-smi returned no device row")
    parts = [part.strip() for part in line.split(",")]
    if len(parts) < 4:
        return GpuStatus("unavailable", 0, 0, 0, False, line)
    try:
        return GpuStatus(parts[0], int(float(parts[1])), int(float(parts[2])), int(float(parts[3])), True)
    except ValueError:
        return GpuStatus("unavailable", 0, 0, 0, False, line)


def probe_gpu() -> GpuStatus:
    try:
        completed = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.used,memory.free", "--format=csv,noheader,nounits"],
            check=False,
            capture_output=True,
            text=True,
            timeout=8,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return GpuStatus("unavailable", 0, 0, 0, False, str(exc))
    if completed.returncode != 0:
        return GpuStatus("unavailable", 0, 0, 0, False, completed.stderr.strip())
    return parse_nvidia_smi(completed.stdout)


def cpu_snapshot() -> dict:
    return {
        "percent": psutil.cpu_percent(interval=0.1),
        "cores": psutil.cpu_count() or 1,
        "ram_available_mb": int(psutil.virtual_memory().available / (1024 * 1024)),
    }


def estimate_vram_mb(weight_mb: float, layers: int, kv_heads: int, head_dim: int, context: int, gpu_layers: int, kv_cache_type: str) -> int:
    if gpu_layers <= 0:
        return 0
    used_layers = layers if gpu_layers < 0 else min(gpu_layers, layers)
    weight = weight_mb * (used_layers / max(layers, 1))
    bytes_per = 1 if kv_cache_type.lower() in {"q8_0", "q8"} else 2
    kv_bytes = 2 * layers * kv_heads * head_dim * context * bytes_per
    kv_mb = kv_bytes / (1024 * 1024)
    overhead = 700
    return int(weight + kv_mb + overhead)


def _threads(percent: int) -> tuple[int, str]:
    cores = psutil.cpu_count() or 1
    used = max(1, int(cores * max(1, min(percent, 100)) / 100))
    end = used - 1
    return used, f"0-{end}"


def plan_launch(
    model: dict,
    gpu: GpuStatus,
    requested_context: int,
    vram_budget_mb: int,
    vram_reserve_mb: int,
    cpu_limit_percent: int,
    kv_cache_type: str = "f16",
    wait_for_vram: bool = False,
    vram_wait_seconds: int = 0,
    sleeper=time.sleep,
    prober=probe_gpu,
) -> LaunchPlan:
    """Apply the required fallback order: context, GPU layers, batch, CPU, then optional wait."""
    threads, cpu_range = _threads(cpu_limit_percent)
    deadline = time.monotonic() + max(0, vram_wait_seconds)
    current_gpu = gpu
    while True:
        usable = 0
        if current_gpu.available:
            usable = min(max(0, current_gpu.free_mb - vram_reserve_mb), vram_budget_mb)
        weight_mb = model["bytes"] / (1024 * 1024)
        layers = int(model["layers"])
        contexts = [requested_context]
        for candidate in (4096, 2048, 1024):
            if candidate < requested_context:
                contexts.append(candidate)
        attempts: list[tuple[int, int, int, int, str]] = []
        kv_types = [kv_cache_type]
        if kv_cache_type == "f16":
            kv_types.append("q8_0")
        for context in contexts:
            for kv_type in kv_types:
                attempts.append((context, layers, 256, 128, kv_type))
        for gpu_layers in (24, 16, 8):
            if gpu_layers >= layers:
                continue
            for context in contexts:
                for kv_type in kv_types:
                    attempts.append((context, gpu_layers, 256, 128, kv_type))
        for context in contexts:
            for kv_type in kv_types:
                attempts.append((context, layers, 128, 64, kv_type))
                for gpu_layers in (24, 16, 8):
                    if gpu_layers < layers:
                        attempts.append((context, gpu_layers, 128, 64, kv_type))
        attempts.append((contexts[-1], 0, 128, 64, "f16"))
        seen: set[tuple[int, int, int, int, str]] = set()
        for context, gpu_layers, batch, ubatch, kv_type in attempts:
            key = (context, gpu_layers, batch, ubatch, kv_type)
            if key in seen:
                continue
            seen.add(key)
            estimate = estimate_vram_mb(
                weight_mb, layers, int(model["kv_heads"]), int(model["head_dim"]), context, gpu_layers, kv_type
            )
            fits = gpu_layers == 0 or (current_gpu.available and estimate <= usable)
            if fits:
                mode = "gpu" if gpu_layers > 0 else "cpu"
                reason = (
                    f"usable VRAM {usable} MB after reserving {vram_reserve_mb} MB; "
                        f"estimate {estimate} MB at context {context}, gpu_layers {gpu_layers}, kv {kv_type}."
                )
                return LaunchPlan(
                    model_key=model.get("key", ""),
                    context_tokens=context,
                    gpu_layers=gpu_layers,
                    batch_size=batch,
                    ubatch_size=ubatch,
                    cpu_threads=threads,
                    cpu_range=cpu_range,
                    mode=mode,
                    reason=reason,
                    estimated_vram_mb=estimate,
                    kv_cache_type=kv_type,
                )
        if wait_for_vram and time.monotonic() < deadline:
            sleeper(min(5, max(0, deadline - time.monotonic())))
            current_gpu = prober()
            continue
        break
    raise ResourceError("Not enough memory for a CPU fallback. Close other processes or choose a smaller model.")


def apply_cpu_affinity(cpu_range: str) -> None:
    start, end = (int(part) for part in cpu_range.split("-"))
    cores = set(range(start, end + 1))
    try:
        os.sched_setaffinity(0, cores)
    except (AttributeError, OSError):
        return
