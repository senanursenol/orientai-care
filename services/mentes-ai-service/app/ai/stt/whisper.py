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
import math
import os
import re
import threading
from dataclasses import dataclass
from io import BytesIO
from typing import Any

import numpy as np

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


def _boolean(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    normalized = raw_value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be true or false")


def _probability(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        value = float(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number") from exc
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between zero and one")
    return value


def _optional_text(name: str, default: str) -> str | None:
    value = os.getenv(name, default).strip()
    return value[:1_000] or None


@dataclass(frozen=True, slots=True)
class WhisperConfig:
    """Runtime settings, configurable through environment variables."""

    model_size: str = os.getenv("WHISPER_MODEL_SIZE", "small")
    # float32 preserved substantially more Turkish words than int8 in the
    # checked-in benchmark. CUDA remains opt-in because a visible GPU driver
    # does not guarantee that CTranslate2's cuBLAS/cuDNN runtime is installed.
    device: str = os.getenv("WHISPER_DEVICE", "cpu")
    compute_type: str = os.getenv("WHISPER_COMPUTE_TYPE", "float32")
    language: str | None = _optional_language()
    beam_size: int = _positive_int("WHISPER_BEAM_SIZE", 5)
    vad_filter: bool = _boolean("WHISPER_VAD_FILTER", False)
    initial_prompt: str | None = _optional_text(
        "WHISPER_INITIAL_PROMPT",
        "T├╝rk├ğe ya┼şl─▒ bak─▒m konu┼şmas─▒. ├ûzel adlar: Eralp, OrientAI. "
        "─░la├ğ, doktor, randevu, aile ve g├╝nl├╝k ya┼şam.",
    )
    hotwords: str | None = _optional_text(
        "WHISPER_HOTWORDS",
        "Eralp, OrientAI, ila├ğ, randevu",
    )
    low_confidence_threshold: float = _probability(
        "WHISPER_LOW_CONFIDENCE_THRESHOLD", 0.55
    )
    local_files_only: bool = _boolean("WHISPER_LOCAL_FILES_ONLY", False)
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
    transcription_confidence: float = 0.0
    low_confidence: bool = True
    model: str = "unknown"


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

            # Conda's NumPy and the CTranslate2 wheel both use Intel OpenMP on
            # Windows. Initializing NumPy's numeric runtime first makes both
            # libraries share the same runtime; the reverse order terminates
            # the process with OMP Error #15 during feature extraction.
            numeric_probe = np.ones((64, 64), dtype=np.float32)
            np.matmul(numeric_probe, numeric_probe)

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
                    local_files_only=self.config.local_files_only,
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
                temperature=0.0,
                vad_filter=self.config.vad_filter,
                vad_parameters={
                    "min_silence_duration_ms": 2_000,
                    "speech_pad_ms": 400,
                },
                condition_on_previous_text=False,
                initial_prompt=self.config.initial_prompt,
                hotwords=self.config.hotwords,
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
            segment_list = list(segments)
            text = "".join(segment.text for segment in segment_list).strip()
            text = re.sub(r"\s+", " ", text)
            token_weights = [
                max(len(segment.text.split()), 1) for segment in segment_list
            ]
            if segment_list:
                average_log_probability = sum(
                    float(segment.avg_logprob) * weight
                    for segment, weight in zip(
                        segment_list, token_weights, strict=True
                    )
                ) / sum(token_weights)
                transcription_confidence = min(
                    1.0, math.exp(min(0.0, average_log_probability))
                )
            else:
                transcription_confidence = 0.0
        except InvalidAudioError:
            raise
        except Exception as exc:
            logger.exception("Whisper failed while decoding or transcribing audio")
            raise WhisperServiceError("Audio transcription failed") from exc

        return TranscriptionResult(
            text=text,
            language=str(info.language),
            language_probability=float(info.language_probability),
            duration_seconds=duration,
            transcription_confidence=round(transcription_confidence, 6),
            low_confidence=(
                transcription_confidence
                < self.config.low_confidence_threshold
            ),
            model=self.config.model_size,
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
            "Audio transcribed: duration=%.1fs language=%s "
            "language_probability=%.3f transcription_confidence=%.3f model=%s",
            result.duration_seconds,
            result.language,
            result.language_probability,
            result.transcription_confidence,
            result.model,
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
