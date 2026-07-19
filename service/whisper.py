"""Asynchronous, local speech-to-text service powered by faster-whisper.

The public ``whisper_service`` object matches the interface used by
``manage.py``::

    transcript = await whisper_service.transcribe(audio_bytes)

The model is loaded lazily and reused for all requests.  Model loading and
transcription run in worker threads so they do not block FastAPI's event loop.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import threading
from dataclasses import dataclass
from io import BytesIO
from typing import Any

logger = logging.getLogger(__name__)


class WhisperServiceError(RuntimeError):
    """Base exception for speech-to-text failures."""


class InvalidAudioError(WhisperServiceError, ValueError):
    """Raised when the supplied audio payload is empty or too large."""


def _positive_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if value <= 0:
        raise ValueError(f"{name} must be greater than zero")
    return value


def _optional_language() -> str | None:
    language = os.getenv("WHISPER_LANGUAGE", "tr").strip().lower()
    return language or None


@dataclass(frozen=True, slots=True)
class WhisperConfig:
    """Runtime settings, configurable through environment variables."""

    model_size: str = os.getenv("WHISPER_MODEL_SIZE", "small")
    device: str = os.getenv("WHISPER_DEVICE", "auto")
    compute_type: str = os.getenv("WHISPER_COMPUTE_TYPE", "default")
    language: str | None = _optional_language()
    beam_size: int = _positive_int("WHISPER_BEAM_SIZE", 5)
    max_concurrent_requests: int = _positive_int(
        "WHISPER_MAX_CONCURRENT_REQUESTS", 1
    )
    max_audio_bytes: int = _positive_int(
        "WHISPER_MAX_AUDIO_BYTES", 25 * 1024 * 1024
    )
    max_audio_seconds: int = _positive_int("WHISPER_MAX_AUDIO_SECONDS", 600)


@dataclass(frozen=True, slots=True)
class TranscriptionResult:
    """Text and useful, non-sensitive metadata returned by Whisper."""

    text: str
    language: str
    language_probability: float
    duration_seconds: float


class WhisperService:
    """Reusable and event-loop-friendly faster-whisper service."""

    def __init__(self, config: WhisperConfig | None = None) -> None:
        self.config = config or WhisperConfig()
        self._model: Any | None = None
        self._model_lock = threading.Lock()
        self._inference_slots = asyncio.Semaphore(
            self.config.max_concurrent_requests
        )

    def _get_model(self) -> Any:
        if self._model is not None:
            return self._model

        with self._model_lock:
            if self._model is not None:
                return self._model

            try:
                from faster_whisper import WhisperModel
            except ImportError as exc:
                raise WhisperServiceError(
                    "faster-whisper is not installed. Run: "
                    "pip install -r requirements.txt"
                ) from exc

            logger.info(
                "Loading Whisper model=%s device=%s compute_type=%s",
                self.config.model_size,
                self.config.device,
                self.config.compute_type,
            )
            try:
                self._model = WhisperModel(
                    self.config.model_size,
                    device=self.config.device,
                    compute_type=self.config.compute_type,
                )
            except Exception as exc:
                raise WhisperServiceError(
                    f"Whisper model '{self.config.model_size}' could not be loaded"
                ) from exc

        return self._model

    def _transcribe_sync(self, audio: bytes) -> TranscriptionResult:
        model = self._get_model()

        try:
            # PyAV, used internally by faster-whisper, accepts a seekable
            # file-like object. Keeping it in memory avoids writing patient
            # audio to disk.
            segments, info = model.transcribe(
                BytesIO(audio),
                language=self.config.language,
                task="transcribe",
                beam_size=self.config.beam_size,
                vad_filter=True,
                vad_parameters={"min_silence_duration_ms": 500},
                condition_on_previous_text=False,
                word_timestamps=False,
            )

            duration = float(info.duration)
            if duration > self.config.max_audio_seconds:
                raise InvalidAudioError(
                    "Audio is too long: "
                    f"{duration:.1f}s (limit: {self.config.max_audio_seconds}s)"
                )

            # ``segments`` is a generator; consuming it here ensures all heavy
            # inference remains inside the worker thread.
            text = "".join(segment.text for segment in segments).strip()
            text = re.sub(r"\s+", " ", text)
        except InvalidAudioError:
            raise
        except Exception as exc:
            raise WhisperServiceError("Audio transcription failed") from exc

        return TranscriptionResult(
            text=text,
            language=str(info.language),
            language_probability=float(info.language_probability),
            duration_seconds=duration,
        )

    @staticmethod
    def _validate_audio(audio: bytes | bytearray | memoryview) -> bytes:
        if not isinstance(audio, (bytes, bytearray, memoryview)):
            raise InvalidAudioError("Audio must be provided as bytes")

        audio_bytes = bytes(audio)
        if not audio_bytes:
            raise InvalidAudioError("Audio payload is empty")
        return audio_bytes

    async def transcribe_with_metadata(
        self, audio: bytes | bytearray | memoryview
    ) -> TranscriptionResult:
        """Transcribe audio bytes without blocking the FastAPI event loop."""

        audio_bytes = self._validate_audio(audio)
        if len(audio_bytes) > self.config.max_audio_bytes:
            raise InvalidAudioError(
                "Audio payload is too large: "
                f"{len(audio_bytes)} bytes "
                f"(limit: {self.config.max_audio_bytes} bytes)"
            )

        async with self._inference_slots:
            result = await asyncio.to_thread(self._transcribe_sync, audio_bytes)

        logger.info(
            "Audio transcribed: duration=%.1fs language=%s probability=%.3f",
            result.duration_seconds,
            result.language,
            result.language_probability,
        )
        return result

    async def transcribe(self, audio: bytes | bytearray | memoryview) -> str:
        """Return only the transcript, as expected by the orchestrator."""

        result = await self.transcribe_with_metadata(audio)
        return result.text


# A single process-wide instance keeps the model warm between API requests.
whisper_service = WhisperService()


async def transcribe(audio: bytes | bytearray | memoryview) -> str:
    """Convenience wrapper for callers that prefer a module-level function."""

    return await whisper_service.transcribe(audio)


__all__ = [
    "InvalidAudioError",
    "TranscriptionResult",
    "WhisperConfig",
    "WhisperService",
    "WhisperServiceError",
    "transcribe",
    "whisper_service",
]
