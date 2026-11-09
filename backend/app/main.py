"""FastAPI application: a thin HTTP layer over SchemeService.

Run:  uvicorn app.main:app --reload --port 8000
Docs: http://localhost:8000/docs

Privacy: nothing the user says is written to disk or logged. Audio is processed in a
temporary file that is deleted immediately after transcription.
"""

from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .config import Settings
from .ratelimit import RateLimiter
from .service import SchemeService
from .transcribe import Transcriber, is_available

settings = Settings.from_env()
service = SchemeService(settings)
transcriber = Transcriber(settings.whisper_model) if settings.whisper_enabled and is_available() else None
limiter = RateLimiter(settings.rate_limit_per_minute)

app = FastAPI(title="SchemeSaathi API", version="1.0.0", description="Find government welfare schemes you may qualify for.")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    text: str = Field(default="", max_length=5000, description="What the person said or typed.")
    lang: str | None = Field(default=None, description="'en', 'hi' or 'kn'. Auto-detected if omitted.")
    overrides: dict[str, Any] = Field(default_factory=dict, description="Fields the user edited; null clears a field.")


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    lang: str | None = None


def _client_key(request: Request) -> str:
    if settings.trust_proxy:
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _limit(request: Request) -> None:
    if not limiter.allow(_client_key(request)):
        raise HTTPException(status_code=429, detail="Too many requests. Please wait a minute and try again.")


@app.get("/api/health")
def health() -> dict:
    return service.health(transcription_available=transcriber is not None)


@app.get("/api/meta")
def meta() -> dict:
    return service.meta()


@app.post("/api/analyze")
def analyze(body: AnalyzeRequest, request: Request) -> dict:
    _limit(request)
    return service.analyze(text=body.text, overrides=body.overrides, lang=body.lang)


@app.post("/api/ask")
def ask(body: AskRequest, request: Request) -> dict:
    _limit(request)
    return service.ask(question=body.question, lang=body.lang)


@app.post("/api/transcribe")
async def transcribe(request: Request, audio: UploadFile = File(...), lang: str = Form("en")) -> dict:
    _limit(request)
    if transcriber is None:
        raise HTTPException(status_code=501, detail="Server-side transcription is not installed. Use browser speech recognition or `pip install faster-whisper`.")
    limit = settings.max_audio_mb * 1024 * 1024
    data = await audio.read(limit + 1)
    if len(data) > limit:
        raise HTTPException(status_code=413, detail=f"Audio is larger than {settings.max_audio_mb} MB.")
    if not data:
        raise HTTPException(status_code=400, detail="Empty audio.")
    suffix = os.path.splitext(audio.filename or "")[1] or ".webm"
    try:
        return await run_in_threadpool(transcriber.transcribe, data, lang, suffix)
    except Exception as exc:  # decoding errors, model download problems, ...
        raise HTTPException(status_code=500, detail=f"Transcription failed ({exc.__class__.__name__}).") from exc


# Optional: serve the built frontend from this process (SERVE_FRONTEND_DIR=../frontend/dist).
# Mounted last so it never shadows the /api routes.
if settings.serve_frontend_dir and os.path.isdir(settings.serve_frontend_dir):
    app.mount("/", StaticFiles(directory=settings.serve_frontend_dir, html=True), name="frontend")
