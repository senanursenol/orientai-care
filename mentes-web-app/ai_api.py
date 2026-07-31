"""FastAPI application for multimodal patient conversation and assistance."""

from __future__ import annotations

import os
import logging
from typing import NoReturn


from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field

from services.conversation import (
    ConversationResult,
    ConversationServiceError,
    conversation_service,
)
from services.stt.audio_processing import AudioProcessingError
from services.sentiment.sentiment import (
    SentimentServiceError,
    sentiment_service,
)
from services.stt.voice_input import (
    EmptyTranscriptError,
    VoiceInputResult,
    voice_input_service,
)
from services.stt.whisper import (
    InvalidAudioError,
    WhisperServiceError,
    whisper_service,
)
from services.tts.tts import (
    InvalidTextError,
    TTSServiceError,
    tts_service,
)
from services.vision.vision_service import (
    InvalidImageError,
    VisionServiceError,
    vision_service,
)


logger = logging.getLogger(__name__)


class SafetyResponse(BaseModel):
    """Safety intent result kept separate from emotional sentiment."""

    label: str
    score: float
    severity: str
    needs_attention: bool
    signals: list[str]


class SentimentResponse(BaseModel):
    """Content-based emotion estimate for the transcribed speech."""

    label: str
    score: float
    scores: dict[str, float]
    low_confidence: bool
    needs_attention: bool
    signals: list[str]
    safety: SafetyResponse
    model: str
    method: str


class VoiceInputResponse(BaseModel):
    """Transcribed text and its content-based emotion estimate."""

    ai_input: str
    detected_language: str
    language_probability: float
    input_duration_seconds: float
    transcription_confidence: float
    transcription_low_confidence: bool
    transcription_model: str
    sentiment: SentimentResponse


class TextInputRequest(BaseModel):
    """Text supplied directly by the browser composer."""

    text: str = Field(min_length=1, max_length=2_000)


class TextInputResponse(BaseModel):
    """Normalized text and its content-based emotion estimate."""

    input: str
    sentiment: SentimentResponse


class ResponsePolicyResponse(BaseModel):
    """Explicit response controls sent to Gemini."""

    tone: str
    length: str
    acknowledge_feeling: bool
    ask_at_most_one_question: bool
    avoid_confrontation: bool


class LLMContextResponse(BaseModel):
    """Structured sentiment, policy and safety metadata consumed by Gemini."""

    emotional_state: str
    confidence: str
    response_policy: ResponsePolicyResponse
    safety: dict[str, bool]


class OutputSafetyResponse(BaseModel):
    """Audit metadata from the deterministic final-response check."""

    blocked: bool
    modified: bool
    reasons: list[str]
    method: str


class TextConversationResponse(BaseModel):
    """Complete RAG-free conversation result for a typed message."""

    input: str
    sentiment: SentimentResponse
    llm_context: LLMContextResponse
    assistant_response: str
    output_safety: OutputSafetyResponse
    model: str


class VoiceConversationResponse(TextConversationResponse):
    """Complete conversation result plus speech-to-text metadata."""

    detected_language: str
    language_probability: float
    input_duration_seconds: float
    transcription_confidence: float
    transcription_low_confidence: bool
    transcription_model: str


class VisionDescriptionResponse(BaseModel):
    """Patient-facing, memory-aware description of an uploaded photo."""

    description: str
    model: str


class SpeechSynthesisRequest(BaseModel):
    """Assistant response that should be read aloud in Turkish."""

    text: str = Field(min_length=1, max_length=10_000)


def _allowed_origins() -> list[str]:
    configured = os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    )
    return [origin.strip() for origin in configured.split(",") if origin.strip()]


def _conversation_payload(result: ConversationResult) -> dict[str, object]:
    return {
        "input": result.input,
        "sentiment": result.sentiment,
        "llm_context": result.llm_context.to_dict(),
        "assistant_response": result.assistant_response,
        "output_safety": result.output_safety,
        "model": result.model,
    }


def _raise_conversation_http_error(exc: ConversationServiceError) -> NoReturn:
    logger.exception("Conversation pipeline failed at stage=%s", exc.stage)
    if exc.stage == "input":
        status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    else:
        status_code = exc.status_code or status.HTTP_502_BAD_GATEWAY
    raise HTTPException(
        status_code=status_code,
        detail=f"Konuşma akışı '{exc.stage}' adımında tamamlanamadı: {exc}",
    ) from exc


async def _prepare_uploaded_voice(audio: UploadFile) -> VoiceInputResult:
    if audio.content_type and not (
        audio.content_type.startswith("audio/")
        or audio.content_type == "application/octet-stream"
    ):
        await audio.close()
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="The uploaded file must contain audio",
        )

    max_bytes = voice_input_service.stt.config.max_audio_bytes
    audio_bytes = await audio.read(max_bytes + 1)
    await audio.close()
    if len(audio_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Audio exceeds the {max_bytes}-byte limit",
        )

    try:
        return await voice_input_service.prepare(audio_bytes)
    except (AudioProcessingError, InvalidAudioError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except EmptyTranscriptError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except WhisperServiceError as exc:
        raise HTTPException(
            status_code=502,
            detail="Speech-to-text service is unavailable",
        ) from exc


app = FastAPI(
    title="OrientAI Multimodal Input Service",
    version="1.0.0",
    description="Browser text, voice and photo input for patient support",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "input-analysis"}


@app.post("/api/text/analyze", response_model=TextInputResponse)
async def analyze_text(payload: TextInputRequest) -> TextInputResponse:
    text = payload.text.strip()
    if not text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Text input cannot be empty",
        )

    try:
        sentiment = await sentiment_service.analyze(text)
    except SentimentServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Sentiment analysis service is unavailable",
        ) from exc

    return TextInputResponse(input=text, sentiment=sentiment)


@app.post("/api/chat/text", response_model=TextConversationResponse)
async def chat_with_text(payload: TextInputRequest) -> TextConversationResponse:
    """Run sentiment, policy, Gemini and output safety for typed input."""

    try:
        result = await conversation_service.respond(payload.text)
    except ConversationServiceError as exc:
        _raise_conversation_http_error(exc)

    return TextConversationResponse(**_conversation_payload(result))


@app.post("/api/voice/transcribe", response_model=VoiceInputResponse)
async def transcribe_voice(
    audio: UploadFile = File(..., description="Recorded browser audio"),
) -> VoiceInputResponse:
    result = await _prepare_uploaded_voice(audio)

    return VoiceInputResponse(
        ai_input=result.ai_input,
        detected_language=result.language,
        language_probability=result.language_probability,
        input_duration_seconds=result.input_duration_seconds,
        transcription_confidence=result.transcription_confidence,
        transcription_low_confidence=result.transcription_low_confidence,
        transcription_model=result.transcription_model,
        sentiment=result.sentiment,
    )


@app.post("/api/chat/voice", response_model=VoiceConversationResponse)
async def chat_with_voice(
    audio: UploadFile = File(..., description="Recorded browser audio"),
    patient_context: str | None = Form(
        default=None,
        description="Optional, verified patient context",
    ),
) -> VoiceConversationResponse:
    """Run STT and the complete RAG-free conversation pipeline."""

    voice_result = await _prepare_uploaded_voice(audio)
    try:
        result = await conversation_service.respond(
            voice_result.ai_input,
            sentiment_result=voice_result.sentiment,
            patient_context=patient_context,
        )
    except ConversationServiceError as exc:
        _raise_conversation_http_error(exc)

    return VoiceConversationResponse(
        **_conversation_payload(result),
        detected_language=voice_result.language,
        language_probability=voice_result.language_probability,
        input_duration_seconds=voice_result.input_duration_seconds,
        transcription_confidence=voice_result.transcription_confidence,
        transcription_low_confidence=voice_result.transcription_low_confidence,
        transcription_model=voice_result.transcription_model,
    )


@app.post(
    "/api/tts/synthesize",
    response_class=Response,
    responses={
        200: {
            "content": {"audio/mpeg": {}},
            "description": "Synthesized Turkish MP3 audio",
        }
    },
)
async def synthesize_speech(payload: SpeechSynthesisRequest) -> Response:
    """Return a clear Turkish reading of an assistant response."""

    try:
        audio = await tts_service.synthesize(payload.text)
    except InvalidTextError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    except TTSServiceError as exc:
        logger.exception(
            "TTS synthesis failed: voice=%s characters=%d",
            tts_service.config.voice,
            len(payload.text),
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Sesli destek oluşturulamadı: {exc}",
        ) from exc

    return Response(
        content=audio,
        media_type="audio/mpeg",
        headers={
            "Cache-Control": "no-store",
            "Content-Disposition": 'inline; filename="orientai-response.mp3"',
        },
    )


@app.post(
    "/api/vision/describe",
    response_model=VisionDescriptionResponse,
)
async def describe_photo(
    image: UploadFile = File(..., description="Patient-provided photo"),
    patient_context: str | None = Form(
        default=None,
        description="Optional, verified patient context",
    ),
) -> VisionDescriptionResponse:
    mime_type = (image.content_type or "").lower()
    max_bytes = vision_service.config.max_image_bytes
    image_bytes = await image.read(max_bytes + 1)
    await image.close()

    if len(image_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Fotoğraf izin verilen dosya boyutunu aşıyor.",
        )

    try:
        description = await vision_service.describe(
            image_bytes,
            mime_type,
            patient_context,
        )
    except InvalidImageError as exc:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=str(exc),
        ) from exc
    except VisionServiceError as exc:
        logger.exception(
            "Vision endpoint failed: model=%s mime_type=%s bytes=%d provider_status=%s",
            vision_service.config.model,
            mime_type,
            len(image_bytes),
            exc.provider_status,
        )
        raise HTTPException(
            status_code=exc.status_code or status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return VisionDescriptionResponse(
        description=description,
        model=vision_service.config.model,
    )
