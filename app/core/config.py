"""Application settings. Environment variables use the OVERLORD_ prefix."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="OVERLORD_",
        env_file=".env",
        extra="ignore",
    )

    host: str = "127.0.0.1"
    port: int = 8765
    database_url: str = "sqlite:///data/novel_engine.db"
    data_dir: Path = ROOT / "data"
    model_registry_path: Path = ROOT / "config" / "models.yaml"
    llama_server_bin: Path = ROOT / "third_party" / "llama-b11574" / "llama-server"
    llama_server_host: str = "127.0.0.1"
    llama_server_port: int = 8081
    inference_backend: str = "llama"
    embedding_backend: str = "hash"
    embedding_model: str = "intfloat/multilingual-e5-small"
    active_model: str = "qwen3-8b-q4"
    context_tokens: int = 8192
    vram_budget_mb: int = 9000
    vram_reserve_mb: int = 3000
    cpu_limit_percent: int = 50
    cooldown_seconds: float = 2.0
    max_revision_iterations: int = 3
    temperature_plan: float = 0.3
    temperature_write: float = 0.8
    temperature_validate: float = 0.1
    seed: int = 17
    planner_mode: str = "deterministic"
    scene_target_words: int = 1600
    volume_target_words: int = 60000
    volume_target_words_min: int = 45000
    volume_target_words_max: int = 65000
    max_json_attempts: int = 3
    training_enabled: bool = False
    wait_for_vram: bool = False
    vram_wait_seconds: int = 30
    idle_unload_seconds: int = 120
    discovery_user_agent: str = "OverlordNovelEngine/0.1 (local metadata index; +https://localhost)"
    discovery_rate_limit_seconds: float = 2.0
    retrieval_token_budget: int = 1800
    log_level: str = "INFO"
    font_path: Path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    use_llm_validators: bool = False
    kv_cache_type: str = "f16"

    root: Path = Field(default=ROOT)

    def sqlite_path(self) -> Path | None:
        prefix = "sqlite:///"
        if self.database_url.startswith(prefix):
            raw = self.database_url[len(prefix) :]
            path = Path(raw)
            if not path.is_absolute():
                path = self.root / path
            return path
        return None


@lru_cache
def get_settings() -> Settings:
    return Settings()
