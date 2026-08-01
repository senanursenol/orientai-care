"""Asynchronous Turkish text-to-speech service powered by edge-tts.

The module-level ``tts_service`` object matches the orchestrator contract::

    mp3_audio = await tts_service.synthesize(response_text)

Audio is streamed directly into memory and returned as MP3 bytes. No temporary
files are created.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

_RATE_PATTERN = re.compile(r"^[+-]\d+%$")
_PITCH_PATTERN = re.compile(r"^[+-]\d+Hz$")
_VOLUME_PATTERN = re.compile(r"^[+-]\d+%$")


class TTSServiceError(RuntimeError):
    """Base exception for text-to-speech failures."""


class InvalidTextError(TTSServiceError, ValueError):
    """Raised when text is empty, invalid, or longer than the configured limit."""


class AudioOutputLimitError(TTSServiceError):
    """Raised when generated audio exceeds the configured memory limit."""


class TTSDependencyError(TTSServiceError):
    """Raised when the configured TTS client library is unavailable."""


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


def _positive_float(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        value = float(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number") from exc
    if value <= 0:
        raise ValueError(f"{name} must be greater than zero")
    return value


@dataclass(frozen=True, slots=True)
class TTSConfig:
    """Runtime settings, configurable through ``TTS_*`` environment variables."""

    voice: str = field(
        default_factory=lambda: os.getenv("TTS_VOICE", "tr-TR-EmelNeural")
    )
    rate: str = field(default_factory=lambda: os.getenv("TTS_RATE", "-5%"))
    pitch: str = field(default_factory=lambda: os.getenv("TTS_PITCH", "+0Hz"))
    volume: str = field(default_factory=lambda: os.getenv("TTS_VOLUME", "+0%"))
    max_text_chars: int = field(
        default_factory=lambda: _positive_int("TTS_MAX_TEXT_CHARS", 10_000)
    )
    max_audio_bytes: int = field(
        default_factory=lambda: _positive_int(
            "TTS_MAX_AUDIO_BYTES", 10 * 1024 * 1024
        )
    )
    max_concurrent_requests: int = field(
        default_factory=lambda: _positive_int("TTS_MAX_CONCURRENT_REQUESTS", 4)
    )
    request_timeout_seconds: float = field(
        default_factory=lambda: _positive_float("TTS_REQUEST_TIMEOUT_SECONDS", 60.0)
    )
    max_attempts: int = field(
        default_factory=lambda: _positive_int("TTS_MAX_ATTEMPTS", 2)
    )

    def __post_init__(self) -> None:
        if not self.voice.strip():
            raise ValueError("TTS_VOICE cannot be empty")
        if not _RATE_PATTERN.fullmatch(self.rate):
            raise ValueError("TTS_RATE must look like '-5%' or '+10%'")
        if not _PITCH_PATTERN.fullmatch(self.pitch):
            raise ValueError("TTS_PITCH must look like '+0Hz' or '-10Hz'")
        if not _VOLUME_PATTERN.fullmatch(self.volume):
            raise ValueError("TTS_VOLUME must look like '+0%' or '-10%'")


class TTSService:
    """Memory-efficient asynchronous text-to-speech service."""

    def __init__(self, config: TTSConfig | None = None) -> None:
        self.config = config or TTSConfig()
        self._request_slots = asyncio.Semaphore(
            self.config.max_concurrent_requests
        )

    def _validate_text(self, text: str) -> str:
        if not isinstance(text, str):
            raise InvalidTextError("Text must be a string")

        normalized_text = re.sub(r"\s+", " ", text).strip()
        if not normalized_text:
            raise InvalidTextError("Text cannot be empty")
        if len(normalized_text) > self.config.max_text_chars:
            raise InvalidTextError(
                "Text is too long: "
                f"{len(normalized_text)} characters "
                f"(limit: {self.config.max_text_chars})"
            )
        return normalized_text

    async def _synthesize_once(self, text: str) -> bytes:
        try:
            import edge_tts
        except ImportError as exc:
            raise TTSDependencyError(
                "edge-tts is not installed. Run: pip install -r requirements.txt"
            ) from exc

        communicate: Any = edge_tts.Communicate(
            text,
            self.config.voice,
            rate=self.config.rate,
            volume=self.config.volume,
            pitch=self.config.pitch,
        )

        audio = bytearray()
        async for chunk in communicate.stream():
            if chunk["type"] != "audio":
                continue

            audio.extend(chunk["data"])
            if len(audio) > self.config.max_audio_bytes:
                raise AudioOutputLimitError(
                    "Generated audio is too large "
                    f"(limit: {self.config.max_audio_bytes} bytes)"
                )

        if not audio:
            raise TTSServiceError("The TTS provider returned no audio")
        return bytes(audio)

    async def synthesize(self, text: str) -> bytes:
        """Convert text into MP3 bytes without creating temporary files."""

        normalized_text = self._validate_text(text)

        async with self._request_slots:
            for attempt in range(1, self.config.max_attempts + 1):
                try:
                    audio = await asyncio.wait_for(
                        self._synthesize_once(normalized_text),
                        timeout=self.config.request_timeout_seconds,
                    )
                    logger.info(
                        "Speech synthesized: characters=%d audio_bytes=%d voice=%s",
                        len(normalized_text),
                        len(audio),
                        self.config.voice,
                    )
                    return audio
                except (
                    InvalidTextError,
                    AudioOutputLimitError,
                    TTSDependencyError,
                ):
                    raise
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    if attempt >= self.config.max_attempts:
                        raise TTSServiceError(
                            "Speech synthesis failed after "
                            f"{self.config.max_attempts} attempt(s)"
                        ) from exc

                    delay_seconds = 0.5 * (2 ** (attempt - 1))
                    logger.warning(
                        "TTS attempt %d/%d failed; retrying in %.1fs",
                        attempt,
                        self.config.max_attempts,
                        delay_seconds,
                    )
                    await asyncio.sleep(delay_seconds)

        # The retry loop always returns or raises. This keeps static type
        # checkers aware that the method cannot silently return None.
        raise TTSServiceError("Speech synthesis failed")


# One process-wide instance centralizes configuration and concurrency control.
tts_service = TTSService()


async def synthesize(text: str) -> bytes:
    """Convenience wrapper for callers that prefer a module-level function."""

    return await tts_service.synthesize(text)


__all__ = [
    "AudioOutputLimitError",
    "InvalidTextError",
    "TTSConfig",
    "TTSDependencyError",
    "TTSService",
    "TTSServiceError",
    "synthesize",
    "tts_service",
]
