# Inference benchmark

Measured 2026-10-13 on this machine with `scripts/bench_ngl.py`. Model: `Qwen3-8B-Q4_K_M.gguf`. Context 2048. Prompt 39 tokens. `nvidia-smi` reports an RTX 5070 with 12227 MB.

| GPU layers requested | Load | Completion tokens | Wall time | Tokens/second | VRAM used before | VRAM used during |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 29.55 s | 56 | 10.37 s | 5.40 | 2978 MiB | 2971 MiB |
| 36 | 3.71 s | 49 | 9.78 s | 5.01 | 2975 MiB | 2977 MiB |

Both calls finished with `finish_reason=stop`. Server eval time in `data/logs/bench-ngl.log` was 6.14 tokens/second at 0 GPU layers and 5.81 tokens/second at 36 GPU layers.

`-ngl 36` did not increase VRAM and did not raise speed. `ldd` on `libggml-cuda.so` reports `libcudart.so.12 => not found` and `libcublas.so.12 => not found`. `libcuda.so.1` is present under `/usr/lib/wsl/lib`. The llama-server log never records a CUDA device or an offloaded layer. The faster second load is consistent with the file already being in the page cache, not with GPU execution.

GPU acceleration is not working on this process. Do not treat the installed CUDA driver as evidence that generation is offloaded.

No larger model was tried. No fine-tune was run.
