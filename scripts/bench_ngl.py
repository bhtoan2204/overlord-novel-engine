"""Compare llama.cpp with GPU layers off and on. Prints measured numbers only."""

import json
import os
import subprocess
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "third_party" / "llama-b11574" / "llama-server"
MODEL = ROOT / "data" / "models" / "Qwen3-8B-Q4_K_M.gguf"
LOG = ROOT / "data" / "logs" / "bench-ngl.log"


def gpu_row() -> str:
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used,memory.free,utilization.gpu", "--format=csv,noheader"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.stdout.strip()
    except Exception as exc:
        return f"nvidia-smi failed: {exc}"


def run_one(layers: int) -> dict:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment["LD_LIBRARY_PATH"] = str(BIN.parent) + os.pathsep + environment.get("LD_LIBRARY_PATH", "")
    command = [
        str(BIN),
        "-m",
        str(MODEL),
        "-c",
        "2048",
        "-ngl",
        str(layers),
        "-t",
        "8",
        "--host",
        "127.0.0.1",
        "--port",
        "8081",
        "--jinja",
        "--reasoning",
        "off",
        "--no-reasoning-preserve",
    ]
    handle = LOG.open("a", encoding="utf-8")
    handle.write(f"\n\n===== ngl {layers} =====\n")
    handle.flush()
    process = subprocess.Popen(command, env=environment, stdout=handle, stderr=handle, text=True)
    started = time.monotonic()
    try:
        deadline = time.monotonic() + 180
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError(f"server exited {process.returncode}")
            try:
                response = httpx.get("http://127.0.0.1:8081/health", timeout=2)
                if response.status_code == 200:
                    break
            except httpx.HTTPError:
                time.sleep(1)
        else:
            raise RuntimeError("health timeout")
        load_s = time.monotonic() - started
        before = gpu_row()
        body = {
            "messages": [
                {"role": "system", "content": "Viết tiếng Việt, không suy nghĩ."},
                {"role": "user", "content": "Viết đúng bốn câu về một cánh cửa đóng."},
            ],
            "max_tokens": 80,
            "temperature": 0.2,
            "chat_template_kwargs": {"enable_thinking": False},
        }
        t0 = time.monotonic()
        response = httpx.post("http://127.0.0.1:8081/v1/chat/completions", json=body, timeout=600)
        elapsed = time.monotonic() - t0
        response.raise_for_status()
        data = response.json()
        usage = data.get("usage") or {}
        completion = int(usage.get("completion_tokens") or 0)
        during = gpu_row()
        return {
            "gpu_layers": layers,
            "load_s": round(load_s, 2),
            "elapsed_s": round(elapsed, 2),
            "prompt_tokens": int(usage.get("prompt_tokens") or 0),
            "completion_tokens": completion,
            "tokens_per_second": round(completion / elapsed, 2) if elapsed else 0,
            "finish_reason": data["choices"][0].get("finish_reason"),
            "gpu_before": before,
            "gpu_during": during,
            "text_words": len((data["choices"][0]["message"].get("content") or "").split()),
        }
    finally:
        process.terminate()
        try:
            process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            process.kill()
        handle.close()


if __name__ == "__main__":
    rows = [run_one(0), run_one(36)]
    print(json.dumps(rows, ensure_ascii=False, indent=2))
