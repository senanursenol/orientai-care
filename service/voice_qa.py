"""End-to-end voice question-answering flow.

Pipeline:

    audio bytes -> Whisper STT -> answer provider -> TTS -> MP3 bytes

The default answer provider contains a small, safe orientation demo. Set
``ANSWER_SERVICE_URL`` to delegate questions to a future LLM/RAG service without
changing the voice pipeline.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol
from zoneinfo import ZoneInfo

import httpx

from .tts import TTSService, tts_service
from .whisper import WhisperService, whisper_service

logger = logging.getLogger(__name__)


class AnswerServiceError(RuntimeError):
    """Raised when an answer provider cannot produce a usable answer."""


class EmptyTranscriptError(ValueError):
    """Raised when STT does not detect speech in the supplied audio."""


class AnswerService(Protocol):
    """Interface implemented by rule-based, LLM, or RAG answer providers."""

    async def answer(self, question: str, patient_id: str) -> str:
        """Return a plain-text answer for a transcribed question."""


@dataclass(frozen=True, slots=True)
class VoiceQAResult:
    """Complete output of one voice interaction."""

    question: str
    answer: str
    audio: bytes
    language: str
    language_probability: float
    input_duration_seconds: float
    audio_content_type: str = "audio/mpeg"


class OrientationAnswerService:
    """Small offline fallback for demonstrating the complete voice flow.

    It deliberately avoids inventing personal information. General and
    personalized answers should be supplied by the project's LLM/RAG service.
    """

    _WEEKDAYS = (
        "Pazartesi",
        "Salı",
        "Çarşamba",
        "Perşembe",
        "Cuma",
        "Cumartesi",
        "Pazar",
    )
    _MONTHS = (
        "Ocak",
        "Şubat",
        "Mart",
        "Nisan",
        "Mayıs",
        "Haziran",
        "Temmuz",
        "Ağustos",
        "Eylül",
        "Ekim",
        "Kasım",
        "Aralık",
    )

    def __init__(self, timezone_name: str = "Europe/Istanbul") -> None:
        self._timezone = ZoneInfo(timezone_name)

    async def answer(self, question: str, patient_id: str) -> str:
        del patient_id  # Reserved for a future personalized RAG provider.

        normalized = re.sub(r"\s+", " ", question.casefold()).strip()
        current_time = datetime.now(self._timezone)

        if any(phrase in normalized for phrase in ("saat kaç", "saat nedir")):
            return f"Şu anda saat {current_time:%H:%M}."

        if any(
            phrase in normalized
            for phrase in (
                "bugün günlerden ne",
                "bugün hangi gün",
                "bugünün tarihi",
                "tarih ne",
                "ayın kaçı",
            )
        ):
            weekday = self._WEEKDAYS[current_time.weekday()]
            month = self._MONTHS[current_time.month - 1]
            return (
                f"Bugün {current_time.day} {month} {current_time.year}, "
                f"{weekday}."
            )

        if any(
            phrase in normalized
            for phrase in ("sen kimsin", "adın ne", "kimsin")
        ):
            return (
                "Ben OrientAI. Günlük yönelim ve hatırlama konusunda yardımcı "
                "olmak için buradayım."
            )

        if any(
            phrase in normalized
            for phrase in ("merhaba", "selam", "günaydın", "iyi akşamlar")
        ):
            return "Merhaba. Buradayım ve sizi dinliyorum. Nasıl yardımcı olabilirim?"

        if any(phrase in normalized for phrase in ("ne yapabilirsin", "yardım et")):
            return (
                "Saat ve tarihi söyleyebilir, sorularınızı dinleyebilir ve bağlı "
                "bilgi servisinden yanıt alabilirim."
            )

        return (
            "Sorunuzu anladım. Bu soruya güvenilir ve kişisel bir yanıt "
            "verebilmem için bilgi ve hafıza servisinin bağlanması gerekiyor."
        )


@dataclass(frozen=True, slots=True)
class HTTPAnswerConfig:
    """Configuration for a generic external LLM/RAG answer endpoint."""

    url: str
    api_key: str | None = None
    timeout_seconds: float = 30.0

    @classmethod
    def from_environment(cls) -> "HTTPAnswerConfig | None":
        url = os.getenv("ANSWER_SERVICE_URL", "").strip()
        if not url:
            return None

        api_key = os.getenv("ANSWER_SERVICE_API_KEY", "").strip() or None
        try:
            timeout = float(os.getenv("ANSWER_SERVICE_TIMEOUT_SECONDS", "30"))
        except ValueError as exc:
            raise ValueError(
                "ANSWER_SERVICE_TIMEOUT_SECONDS must be a number"
            ) from exc
        if timeout <= 0:
            raise ValueError("ANSWER_SERVICE_TIMEOUT_SECONDS must be positive")
        return cls(url=url, api_key=api_key, timeout_seconds=timeout)


class HTTPAnswerService:
    """Adapter for an external answer endpoint.

    Request JSON: ``{"question": str, "patient_id": str}``
    Response JSON may contain ``answer``, ``text_response``, or ``text``.
    """

    def __init__(self, config: HTTPAnswerConfig) -> None:
        self.config = config

    async def answer(self, question: str, patient_id: str) -> str:
        headers = {"Accept": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        try:
            async with httpx.AsyncClient(
                timeout=self.config.timeout_seconds
            ) as client:
                response = await client.post(
                    self.config.url,
                    json={"question": question, "patient_id": patient_id},
                    headers=headers,
                )
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise AnswerServiceError("External answer service failed") from exc

        answer = next(
            (
                payload.get(key)
                for key in ("answer", "text_response", "text")
                if isinstance(payload.get(key), str) and payload[key].strip()
            ),
            None,
        )
        if answer is None:
            raise AnswerServiceError(
                "External answer service returned no supported answer field"
            )
        return re.sub(r"\s+", " ", answer).strip()


def build_answer_service() -> AnswerService:
    """Select the external provider when configured, otherwise use the demo."""

    http_config = HTTPAnswerConfig.from_environment()
    if http_config is not None:
        logger.info("Using external answer service: %s", http_config.url)
        return HTTPAnswerService(http_config)
    logger.info("ANSWER_SERVICE_URL is unset; using orientation demo answers")
    return OrientationAnswerService()


@dataclass(slots=True)
class VoiceQAService:
    """Coordinates STT, answer generation, and TTS in strict sequence."""

    answer_service: AnswerService = field(default_factory=build_answer_service)
    stt: WhisperService = field(default_factory=lambda: whisper_service)
    tts: TTSService = field(default_factory=lambda: tts_service)

    async def ask(
        self,
        audio: bytes | bytearray | memoryview,
        patient_id: str = "demo-patient",
    ) -> VoiceQAResult:
        patient_id = patient_id.strip() or "demo-patient"

        transcription = await self.stt.transcribe_with_metadata(audio)
        question = transcription.text.strip()
        if not question:
            raise EmptyTranscriptError("No speech was detected in the audio")

        answer = (await self.answer_service.answer(question, patient_id)).strip()
        if not answer:
            raise AnswerServiceError("Answer provider returned empty text")

        response_audio = await self.tts.synthesize(answer)
        return VoiceQAResult(
            question=question,
            answer=answer,
            audio=response_audio,
            language=transcription.language,
            language_probability=transcription.language_probability,
            input_duration_seconds=transcription.duration_seconds,
        )


voice_qa_service = VoiceQAService()


__all__ = [
    "AnswerService",
    "AnswerServiceError",
    "EmptyTranscriptError",
    "HTTPAnswerConfig",
    "HTTPAnswerService",
    "OrientationAnswerService",
    "VoiceQAResult",
    "VoiceQAService",
    "build_answer_service",
    "voice_qa_service",
]
