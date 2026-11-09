"""Settings, read from environment variables (see .env.example)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _csv(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


@dataclass
class Settings:
    llm_provider: str = "none"  # "none" | "anthropic"
    anthropic_model: str = "claude-haiku-5-5"
    embedding_backend: str = "tfidf"  # "tfidf" | "sentence-transformers"
    embedding_model: str = "intfloat/multilingual-e5-small"
    min_relevant_score: float | None = None  # None = use the embedder's default
    whisper_enabled: bool = True  # only used if faster-whisper is installed
    whisper_model: str = "small"
    cors_origins: list[str] = field(default_factory=lambda: ["http://localhost:5173", "http://localhost:3000", "http://localhost:8080"])
    max_text_chars: int = 2000
    max_audio_mb: int = 10
    rate_limit_per_minute: int = 30
    serve_frontend_dir: str = ""  # e.g. ../frontend/dist to serve the UI from the same process
    trust_proxy: bool = False  # True only behind your own reverse proxy that sets X-Forwarded-For

    @classmethod
    def from_env(cls) -> "Settings":
        e = os.environ.get
        return cls(
            llm_provider=e("LLM_PROVIDER", "none").lower(),
            anthropic_model=e("ANTHROPIC_MODEL", cls.anthropic_model),
            embedding_backend=e("EMBEDDING_BACKEND", "tfidf").lower(),
            embedding_model=e("EMBEDDING_MODEL", cls.embedding_model),
            min_relevant_score=float(e("MIN_RELEVANT_SCORE")) if e("MIN_RELEVANT_SCORE") else None,
            whisper_enabled=e("WHISPER_ENABLED", "true").lower() in ("1", "true", "yes"),
            whisper_model=e("WHISPER_MODEL", "small"),
            cors_origins=_csv(e("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://localhost:8080")),
            max_text_chars=int(e("MAX_TEXT_CHARS", "2000")),
            max_audio_mb=int(e("MAX_AUDIO_MB", "10")),
            rate_limit_per_minute=int(e("RATE_LIMIT_PER_MINUTE", "30")),
            serve_frontend_dir=e("SERVE_FRONTEND_DIR", ""),
            trust_proxy=e("TRUST_PROXY", "false").lower() in ("1", "true", "yes"),
        )
