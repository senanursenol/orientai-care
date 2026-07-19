"""FastAPI application exposing the OrientAI voice question-answering flow."""

from __future__ import annotations

import base64
import os

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .tts import AudioOutputLimitError, InvalidTextError, TTSServiceError
from .voice_qa import (
    AnswerServiceError,
    EmptyTranscriptError,
    voice_qa_service,
)
from .whisper import InvalidAudioError, WhisperServiceError


class VoiceQAResponse(BaseModel):
    """Browser-friendly response containing text plus base64 MP3 audio."""

    question: str
    answer: str
    audio_base64: str
    audio_content_type: str
    detected_language: str
    language_probability: float
    input_duration_seconds: float


def _allowed_origins() -> list[str]:
    configured = os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    )
    return [origin.strip() for origin in configured.split(",") if origin.strip()]


app = FastAPI(
    title="OrientAI Voice Service",
    version="1.0.0",
    description="Whisper STT -> answer provider -> Turkish TTS",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "voice-qa"}


@app.post("/api/voice/ask", response_model=VoiceQAResponse)
async def ask_voice(
    audio: UploadFile = File(..., description="Recorded browser audio"),
    patient_id: str = Form("demo-patient"),
) -> VoiceQAResponse:
    if audio.content_type and not (
        audio.content_type.startswith("audio/")
        or audio.content_type == "application/octet-stream"
    ):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="The uploaded file must contain audio",
        )

    max_bytes = voice_qa_service.stt.config.max_audio_bytes
    audio_bytes = await audio.read(max_bytes + 1)
    await audio.close()
    if len(audio_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Audio exceeds the {max_bytes}-byte limit",
        )

    try:
        result = await voice_qa_service.ask(audio_bytes, patient_id=patient_id)
    except InvalidAudioError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except EmptyTranscriptError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except AnswerServiceError as exc:
        raise HTTPException(
            status_code=502, detail="Answer service is unavailable"
        ) from exc
    except (WhisperServiceError, InvalidTextError, AudioOutputLimitError, TTSServiceError) as exc:
        raise HTTPException(
            status_code=502, detail="Voice processing service is unavailable"
        ) from exc

    return VoiceQAResponse(
        question=result.question,
        answer=result.answer,
        audio_base64=base64.b64encode(result.audio).decode("ascii"),
        audio_content_type=result.audio_content_type,
        detected_language=result.language,
        language_probability=result.language_probability,
        input_duration_seconds=result.input_duration_seconds,
    )
