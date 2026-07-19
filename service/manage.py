"""
A demo orchestrator service that coordinates multiple AI services, open to developments in the process.

Flow:
1. Get transcript (from audio via Whisper, or plain text)
2. Run sentiment analysis + memory retrieval in parallel
3. Optionally enrich memories with vision context
4. Generate LLM response + synthesize audio
5. Return response to user immediately
6. Persist summary + interaction log as background tasks (non-blocking)
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

<<<<<<< HEAD
<<<<<<< HEAD
# Replace these with actual service imports
# from services import whisper_service, sentiment_service, rag_service
# from services import vision_service, llm_service, tts_service
=======
=======
from .sentiment import sentiment_service
>>>>>>> 77953ac (Sprint 2)
from .tts import tts_service
from .whisper import whisper_service

# Replace these with actual service imports
# from services import rag_service
# from services import vision_service, llm_service
>>>>>>> 91d16b3 (First Commit)
# from db import db

logger = logging.getLogger("orchestrator")
router = APIRouter()

# Schemas

class PatientInputSchema(BaseModel):
    patient_id: str
    text: Optional[str] = None
    audio_file: Optional[bytes] = None
    image_file: Optional[bytes] = None


class ProcessResponse(BaseModel):
    text_response: str
    audio_response: Optional[bytes] = None
    sentiment: Optional[dict] = None
    warnings: list[str] = Field(default_factory=list)

# Helpers

def now() -> datetime:
    return datetime.now(timezone.utc)


async def _safe_call(name: str, coro):

    try:
        return await coro, None
    except Exception as exc:
        logger.exception("Service '%s' failed", name)
        return None, f"{name} failed: {exc}"


async def _persist_interaction(
    patient_id: str,
    transcript: str,
    response_text: str,
    sentiment: dict,
    summary: str,
):

    try:
        await rag_service.add_memory(
            patient_id=patient_id,
            content=summary,
            memory_type="conversation_log",
            timestamp=now(),
        )
    except Exception:
        logger.exception(
            "Failed to store memory for patient_id=%s — needs retry/DLQ", patient_id
        )

    try:
        await db.log_interaction(patient_id, transcript, response_text, sentiment)
    except Exception:
        logger.exception(
            "Failed to log interaction for patient_id=%s — needs retry/DLQ", patient_id
        )


@router.post("/orchestrator/process", response_model=ProcessResponse)
async def process_input(payload: PatientInputSchema, background_tasks: BackgroundTasks):
    warnings: list[str] = []

    if payload.audio_file:
        try:
            transcript = await whisper_service.transcribe(payload.audio_file)
        except Exception as exc:
            logger.exception("Whisper transcription failed")
            raise HTTPException(502, "Speech-to-text service unavailable") from exc
    elif payload.text:
        transcript = payload.text
    else:
        raise HTTPException(400, "No audio or text provided")

    if not transcript or not transcript.strip():
        raise HTTPException(422, "Transcription produced empty text")

    sentiment_result, memories_result = await asyncio.gather(
        _safe_call("sentiment_service", sentiment_service.analyze(transcript)),
        _safe_call(
            "rag_service.retrieve",
            rag_service.retrieve(transcript, patient_id=payload.patient_id),
        ),
    )
    sentiment, sentiment_err = sentiment_result
    memories, memories_err = memories_result

    if sentiment_err:
        warnings.append(sentiment_err)
        sentiment = {"label": "unknown", "score": 0.0}

    # Memory retrieval is more important for response quality but should not

    if memories_err:
        warnings.append(memories_err)
        memories = []

    if payload.image_file:
        vision_context, vision_err = await _safe_call(
            "vision_service", vision_service.analyze(payload.image_file)
        )
        if vision_err:
            warnings.append(vision_err)
        else:
            extra_memories, extra_err = await _safe_call(
                "rag_service.retrieve(vision)",
                rag_service.retrieve(vision_context, patient_id=payload.patient_id),
            )
            if extra_err:
                warnings.append(extra_err)
            elif extra_memories:
                memories += extra_memories

    try:
        response_text = await llm_service.generate(transcript, memories, sentiment)
    except Exception as exc:
        logger.exception("LLM generation failed")
        raise HTTPException(502, "Response generation service unavailable") from exc

    audio_response, tts_err = await _safe_call(
        "tts_service", tts_service.synthesize(response_text)
    )
    if tts_err:
        warnings.append(tts_err)
        audio_response = None

    summary, summary_err = await _safe_call(
        "llm_service.summarize_interaction",
        llm_service.summarize_interaction(transcript, response_text),
    )
    if summary_err:
        warnings.append(summary_err)
        summary = transcript[:500]  # crude fallback

    background_tasks.add_task(
        _persist_interaction,
        payload.patient_id,
        transcript,
        response_text,
        sentiment,
        summary,
    )

    return ProcessResponse(
        text_response=response_text,
        audio_response=audio_response,
        sentiment=sentiment,
        warnings=warnings,
<<<<<<< HEAD
    )
=======
    )
>>>>>>> 91d16b3 (First Commit)
