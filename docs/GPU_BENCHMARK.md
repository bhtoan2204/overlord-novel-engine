# GPU benchmark

RTX 5070, 12227 MB, WSL2. Model `Qwen3-8B-Q4_K_M.gguf`. Context 2048. Measured by `scripts/bench_ngl.py` on 2026-10-13. Numbers are from `data/logs/bench-ngl.json` and `data/logs/bench-ngl.log`.

| GPU layers requested | Load | Completion tokens | Wall time | Tokens/second | VRAM used during |
| --- | --- | --- | --- | --- | --- |
| 0 | 29.55 s | 56 | 10.37 s | 5.40 | 2971 MiB |
| 36 | 3.71 s | 49 | 9.78 s | 5.01 | 2977 MiB |

Server-side eval speed was 6.14 tokens/second at 0 layers and 5.81 at 36 layers. VRAM did not rise when 36 layers were requested. The second load was faster because the file was already cached.

`ldd third_party/llama-b11574/libggml-cuda.so` reports `libcudart.so.12 => not found` and `libcublas.so.12 => not found`. `libcuda.so.1` is present. The llama-server log does not record a CUDA device. Nothing was reinstalled. The driver being present is not GPU offload.

The resource plan still prefers at most 9 GB, keeps a 3 GB reserve, and runs one request. That plan’s `mode: gpu` label is an estimate. These measurements say the process is on CPU.
