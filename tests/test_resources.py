from app.inference.resources import GpuStatus, parse_nvidia_smi, plan_launch


MODEL = {
    "key": "qwen3-8b-q4",
    "bytes": 5027783488,
    "layers": 36,
    "kv_heads": 8,
    "head_dim": 128,
}


def test_parse_nvidia_smi():
    status = parse_nvidia_smi("NVIDIA GeForce RTX 5070, 12227, 2853, 9003\n")
    assert status.available
    assert status.free_mb == 9003
    assert status.total_mb == 12227


def test_tight_budget_reduces_context_before_dropping_the_gpu():
    gpu = GpuStatus("RTX 5070", 12227, 2800, 9003, True)
    plan = plan_launch(MODEL, gpu, 8192, 9000, 3000, 50)
    assert plan.context_tokens < 8192
    assert plan.gpu_layers > 0
    assert plan.estimated_vram_mb <= 9003 - 3000


def test_no_memory_falls_back_to_cpu():
    gpu = GpuStatus("RTX 5070", 12227, 12000, 200, True)
    plan = plan_launch(MODEL, gpu, 8192, 9000, 3000, 50)
    assert plan.mode == "cpu"
    assert plan.gpu_layers == 0
