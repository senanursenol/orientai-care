"""Prepare browser-recorded speech as text input for the conversation service.

Current pipeline:

    audio bytes -> speech enhancement -> Whisper STT -> sentiment -> AI-ready text

The conversation orchestrator consumes this result, calls the LLM and checks
its output. The browser can then pass the final response to TTS when enabled.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field

from .audio_processing import AudioProcessor, audio_processor
from ..sentiment.sentiment import SentimentService, sentiment_service
from .whisper import WhisperService, whisper_service


logger = logging.getLogger(__name__)


class EmptyTranscriptError(ValueError):
    """Raised when Whisper does not detect speech in the supplied audio."""


@dataclass(frozen=True, slots=True)
class VoiceInputResult:
    """Text and metadata prepared for the conversation orchestrator."""

    ai_input: str
    language: str
    language_probability: float
    input_duration_seconds: float
    transcription_confidence: float
    transcription_low_confidence: bool
    transcription_model: str
    sentiment: dict[str, object]


@dataclass(slots=True)
class VoiceInputService:
    """Converts recorded audio into clean model input text."""

    stt: WhisperService = field(default_factory=lambda: whisper_service)
    processor: AudioProcessor = field(default_factory=lambda: audio_processor)
    sentiment: SentimentService = field(default_factory=lambda: sentiment_service)

    async def prepare(
        self,
        audio: bytes | bytearray | memoryview,
    ) -> VoiceInputResult:
        processed = await asyncio.to_thread(self.processor.process, audio)
        transcription = await self.stt.transcribe_with_metadata(processed.wav_bytes)
        ai_input = transcription.text.strip()
        if not ai_input:
            raise EmptyTranscriptError("No speech was detected in the audio")

        try:
            sentiment = await self.sentiment.analyze(ai_input)
        except Exception:
            # Do not discard an understood message when only the optional
            # sentiment step is temporarily unavailable.
            logger.exception("Sentiment analysis failed for a voice transcript")
            sentiment = {
                "label": "unknown",
                "score": 0.0,
                "scores": {
                    "anxious": 0.0,
                    "negative": 0.0,
                    "neutral": 0.0,
                    "positive": 0.0,
                },
                "low_confidence": True,
                "needs_attention": False,
                "signals": [],
                "safety": {
                    "label": "unknown",
                    "score": 0.0,
                    "severity": "unknown",
                    "needs_attention": False,
                    "signals": [],
                },
                "model": "unavailable",
                "method": "unavailable",
            }

        return VoiceInputResult(
            ai_input=ai_input,
            language=transcription.language,
            language_probability=transcription.language_probability,
            input_duration_seconds=transcription.duration_seconds,
            transcription_confidence=transcription.transcription_confidence,
            transcription_low_confidence=transcription.low_confidence,
            transcription_model=transcription.model,
            sentiment=sentiment,
        )


voice_input_service = VoiceInputService()


__all__ = [
    "EmptyTranscriptError",
    "VoiceInputResult",
    "VoiceInputService",
    "voice_input_service",
]
