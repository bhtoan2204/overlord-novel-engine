# GPU benchmark

RTX 5070, 12227 MB, WSL2. Model `Qwen3-8B-Q4_K_M.gguf`. Context 2048. Measured by `scripts/bench_ngl.py` on 2026-10-13. Numbers are from `data/logs/bench-ngl.json` and `data/logs/bench-ngl.log`.

| GPU layers requested | Load | Completion tokens | Wall time | Tokens/second | VRAM used during |
| --- | --- | --- | --- | --- | --- |
| 0 | 29.55 s | 56 | 10.37 s | 5.40 | 2971 MiB |
| 36 | 3.71 s | 49 | 9.78 s | 5.01 | 2977 MiB |

Server-side eval speed was 6.14 tokens/second at 0 layers and 5.81 at 36 layers. VRAM did not rise when 36 layers were requested. The second load was faster because the file was already cached.

`ldd third_party/llama-b11574/libggml-cuda.so` reports `libcudart.so.12 => not found` and `libcublas.so.12 => not found`. `libcuda.so.1` is present. The llama-server log does not record a CUDA device. Nothing was reinstalled. The driver being present is not GPU offload.

Those rows were taken before the CUDA runtime libraries were available. `libcudart.so.12` and `libcublas.so.12` were missing, so 36 layers did not leave the CPU.

The libraries were then unpacked from the Ubuntu packages `libcudart12`, `libcublas12`, and `libcublaslt12` into `third_party/cuda12` (no display driver was installed). A second run of the same script, saved as `data/logs/bench-ngl-cuda.json`, measured:

| GPU layers requested | Load | Completion tokens | Wall time | Tokens/second | VRAM used during |
| --- | --- | --- | --- | --- | --- |
| 0 | 5.74 s | 49 | 6.8 s | 7.21 | 1685 MiB |
| 36 | 1.38 s | 43 | 0.63 s | 68.07 | 6309 MiB, 62% utilization |

The volume worker uses that library path and a planned ceiling of 11000 MB with a 1000 MB reserve. Context starts at 8192 and shrinks only if the estimate does not fit.
