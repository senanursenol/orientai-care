"""FastAPI application for voice and text sentiment input."""

from __future__ import annotations

import os


from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.services.stt.audio_processing import AudioProcessingError
from app.services.sentiment.sentiment import (
    SentimentServiceError,
    sentiment_service,
)
from app.services.stt.voice_input import (
    EmptyTranscriptError,
    voice_input_service,
)
from app.services.stt.whisper import (
    InvalidAudioError,
    WhisperServiceError,
    whisper_service,
)
from app.services.tts.tts import tts_service
from app.services.rag.retriever_service import retrieve_context
from app.services.rag.prompt_builder import build_rag_prompt
from app.services.rag.vision_memory_service import retrieve_memories_for_image


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


class RagChatRequest(BaseModel):
    """Node backend'in (services/mentes-service) /api/chat için gönderdiği istek."""

    patient_id: str = Field(min_length=1)
    message: str = Field(min_length=1, max_length=2_000)


class RagContextDocument(BaseModel):
    """Retriever'dan dönen tek bir anı/rutin kaydı."""

    content: str
    metadata: dict


class RagChatResponse(BaseModel):
    """Node backend'e dönen RAG yanıtı."""

    answer: str
    context: list[RagContextDocument]


class ImageMemoryRequest(BaseModel):
    """Vision servisinden (ORI-28/29) gelen fotoğraf açıklamasını RAG hafızasıyla ilişkilendirme isteği."""

    patient_id: str = Field(min_length=1)
    image_description: str = Field(min_length=1)
    detected_labels: list[str] | None = None


class ImageMemoryResponse(BaseModel):
    """Görsel + RAG bağlamının birleştirildiği, LLM'e verilmeye hazır sonuç."""

    context: str
    documents: list[RagContextDocument]
    has_context: bool
    prompt: str


def _allowed_origins() -> list[str]:
    configured = os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    )
    return [origin.strip() for origin in configured.split(",") if origin.strip()]


app = FastAPI(
    title="OrientAI Input Analysis Service",
    version="1.0.0",
    description="Browser voice/text input -> sentiment analysis",
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


@app.post("/api/voice/transcribe", response_model=VoiceInputResponse)
async def transcribe_voice(
    audio: UploadFile = File(..., description="Recorded browser audio"),
) -> VoiceInputResponse:
    if audio.content_type and not (
        audio.content_type.startswith("audio/")
        or audio.content_type == "application/octet-stream"
    ):
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
        result = await voice_input_service.prepare(audio_bytes)
    except (AudioProcessingError, InvalidAudioError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except EmptyTranscriptError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except WhisperServiceError as exc:
        raise HTTPException(
            status_code=502, detail="Speech-to-text service is unavailable"
        ) from exc

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


@app.post("/api/rag/chat", response_model=RagChatResponse)
async def rag_chat(payload: RagChatRequest) -> RagChatResponse:
    """Node backend'in (mentes-service) /api/chat -> /api/rag/chat köprüsü (ORI-21 kontratı)."""
    try:
        results = retrieve_context(question=payload.message, patient_id=payload.patient_id)
    except Exception as exc:  # ChromaDB/collection hataları
        raise HTTPException(
            status_code=502, detail="Memory retrieval service is unavailable"
        ) from exc

    documents = (results.get("documents") or [[]])[0]
    metadatas = (results.get("metadatas") or [[]])[0]
    context_docs = [
        RagContextDocument(content=doc, metadata=meta)
        for doc, meta in zip(documents, metadatas)
    ]

    if documents:
        context_text = "\n".join(documents)
        prompt = build_rag_prompt(context=context_text, question=payload.message)
    else:
        prompt = build_rag_prompt(
            context="Bu hastaya ait ilgili bir bilgi bulunamadı.",
            question=payload.message,
        )

    # Not: gerçek LLM çağrısı henüz bağlanmadı (ayrı bir görev); şimdilik hazırlanan
    # context'in kendisi cevap olarak döner ki Node ucu (ORI-21) uçtan uca test edilebilsin.
    answer = prompt if not documents else "\n".join(documents)

    return RagChatResponse(answer=answer, context=context_docs)


@app.post("/api/rag/image-memory", response_model=ImageMemoryResponse)
async def rag_image_memory(payload: ImageMemoryRequest) -> ImageMemoryResponse:
    """
    ORI-31: Vision servisinden (ORI-28/29) gelen fotoğraf açıklamasını hastanın
    kişisel anı/rutin hafızasıyla (RAG, patient_id filtreli) ilişkilendirir ve
    LLM'e verilmeye hazır bir prompt üretir.
    """
    try:
        result = retrieve_memories_for_image(
            image_description=payload.image_description,
            patient_id=payload.patient_id,
            detected_labels=payload.detected_labels,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502, detail="Memory retrieval service is unavailable"
        ) from exc

    return ImageMemoryResponse(
        context=result["context"],
        documents=[RagContextDocument(**doc) for doc in result["documents"]],
        has_context=result["has_context"],
        prompt=result["prompt"],
    )
