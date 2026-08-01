"""Patient-aware photo descriptions powered by Gemini 2.5 Flash."""

from __future__ import annotations

import asyncio
import logging
import os
import re
from dataclasses import dataclass, field
from typing import Any


logger = logging.getLogger(__name__)

SUPPORTED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/heic",
    "image/heif",
}

SYSTEM_INSTRUCTION = """
You are OrientAI's photo understanding assistant for a person who may be living
with dementia or Alzheimer's disease.

Describe only what is visibly supported by the image, in calm, simple Turkish.
Connect the visible details to the patient as gentle possible memory cues. If
confirmed patient context is supplied, use only that context. If it is not
supplied, never invent the identity, relationship, location, date, event,
memory, diagnosis, intention, or emotion of a person in the photograph.

Structure the response as:
1. A short, concrete description of the visible scene.
2. A careful patient-oriented connection using uncertainty language such as
   "tanıdık gelebilir" or "bir anıyı çağrıştırabilir".
3. Exactly one warm, open-ended question that may help the patient recall a
   memory without pressuring or correcting them.

Do not diagnose, test the patient's memory, claim certainty about a person, or
give medical advice. If the image is unclear, say so gently. Keep the entire
answer concise and suitable for reading directly to the patient.
""".strip()


class VisionServiceError(RuntimeError):
    """Raised when image understanding cannot produce a safe description."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        provider_status: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.provider_status = provider_status


class InvalidImageError(VisionServiceError, ValueError):
    """Raised when uploaded image bytes or media type are unsupported."""


def _positive_int(name: str, default: int) -> int:
    raw_value = os.getenv(name, str(default))
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if value <= 0:
        raise ValueError(f"{name} must be greater than zero")
    return value


def _safe_error_text(value: object, limit: int = 4_000) -> str:
    """Return useful provider details without exposing credentials."""

    text = str(value).strip() or "Hata mesajı bulunmuyor."
    text = re.sub(
        r"(?i)([?&]key=)[^&\s]+",
        r"\1[REDACTED]",
        text,
    )
    text = re.sub(
        r"(?i)(x-goog-api-key[\"']?\s*[:=]\s*)[^,}\s]+",
        r"\1[REDACTED]",
        text,
    )
    return text[:limit]


@dataclass(frozen=True, slots=True)
class VisionConfig:
    """Runtime settings for Gemini image understanding."""

    model: str = field(
        default_factory=lambda: os.getenv(
            "GEMINI_VISION_MODEL",
            "gemini-3.1-flash-lite",
        )
    )
    max_image_bytes: int = field(
        default_factory=lambda: _positive_int(
            "VISION_MAX_IMAGE_BYTES",
            10 * 1024 * 1024,
        )
    )


class VisionService:
    """Generate a grounded, patient-aware Turkish description of an image."""

    def __init__(
        self,
        config: VisionConfig | None = None,
        client: Any | None = None,
    ) -> None:
        self.config = config or VisionConfig()
        self._client = client

    def _client_or_create(self) -> Any:
        if self._client is not None:
            return self._client

        try:
            from google import genai
        except ImportError as exc:
            raise VisionServiceError(
                "Gemini SDK yüklenemedi: google-genai paketi bulunamadı."
            ) from exc

        # The key remains server-side and uses only the configured name.
        try:
            self._client = genai.Client(
                api_key=os.environ["GEMINI_API_KEY"]
            )
        except KeyError as exc:
            raise VisionServiceError(
                "Gemini istemcisi başlatılamadı: GEMINI_API_KEY ortam değişkeni bulunamadı."
            ) from exc
        except Exception as exc:
            error_message = _safe_error_text(exc)
            raise VisionServiceError(
                "Gemini istemcisi başlatılamadı. "
                f"Hata türü: {type(exc).__name__}. "
                f"Ayrıntı: {error_message}"
            ) from exc
        return self._client

    def _validate(self, image: bytes, mime_type: str) -> None:
        if not image:
            raise InvalidImageError("Fotoğraf verisi boş.")
        if len(image) > self.config.max_image_bytes:
            raise InvalidImageError(
                "Fotoğraf izin verilen dosya boyutunu aşıyor."
            )
        if mime_type not in SUPPORTED_IMAGE_TYPES:
            raise InvalidImageError(
                "JPEG, PNG, WebP, HEIC veya HEIF biçiminde bir fotoğraf yükleyin."
            )

    async def describe(
        self,
        image: bytes,
        mime_type: str,
        patient_context: str | None = None,
    ) -> str:
        """Return a concise Turkish description and one memory prompt."""

        self._validate(image, mime_type)
        context = (patient_context or "").strip()
        context_prompt = (
            f"Doğrulanmış hasta bağlamı:\n{context}"
            if context
            else (
                "Doğrulanmış hasta bağlamı verilmedi. Görseldeki kişilerin "
                "kimliği veya hastayla ilişkisi hakkında varsayım yapma."
            )
        )

        try:
            from google.genai import errors, types
        except ImportError as exc:
            raise VisionServiceError(
                "Gemini SDK yüklenemedi: google-genai paketi bulunamadı."
            ) from exc

        client = self._client_or_create()
        try:
            response = await client.aio.models.generate_content(
                model=self.config.model,
                contents=[
                    types.Part.from_bytes(data=image, mime_type=mime_type),
                    (
                        "Bu fotoğrafı hasta için açıkla ve görünür ayrıntıları "
                        "nazik bir anı çağrışımına dönüştür.\n\n"
                        f"{context_prompt}"
                    ),
                ],
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0.2,
                    max_output_tokens=500,
                ),
            )
        except (InvalidImageError, asyncio.CancelledError):
            raise
        except errors.APIError as exc:
            provider_code = getattr(exc, "code", None)
            provider_status = getattr(exc, "status", None)
            provider_message = _safe_error_text(
                getattr(exc, "message", None) or exc
            )
            logger.exception(
                "Gemini API request failed: model=%s code=%s status=%s",
                self.config.model,
                provider_code,
                provider_status,
            )
            raise VisionServiceError(
                "Gemini API isteği reddedildi veya tamamlanamadı. "
                f"Model: {self.config.model}. "
                f"Google durum kodu: {provider_code or 'bilinmiyor'}. "
                f"Google durum adı: {provider_status or 'bilinmiyor'}. "
                f"Google mesajı: {provider_message}",
                status_code=(
                    provider_code
                    if isinstance(provider_code, int)
                    and 400 <= provider_code <= 599
                    else None
                ),
                provider_status=provider_status,
            ) from exc
        except Exception as exc:
            error_message = _safe_error_text(exc)
            logger.exception(
                "Unexpected Gemini vision error: model=%s error_type=%s",
                self.config.model,
                type(exc).__name__,
            )
            raise VisionServiceError(
                "Fotoğraf açıklanırken beklenmeyen bir hata oluştu. "
                f"Model: {self.config.model}. "
                f"Hata türü: {type(exc).__name__}. "
                f"Ayrıntı: {error_message}"
            ) from exc

        try:
            description = (response.text or "").strip()
        except Exception as exc:
            raise VisionServiceError(
                "Gemini yanıtı metne dönüştürülemedi. "
                f"Hata türü: {type(exc).__name__}. "
                f"Ayrıntı: {_safe_error_text(exc)}"
            ) from exc
        if not description:
            prompt_feedback = _safe_error_text(
                getattr(response, "prompt_feedback", "yok")
            )
            finish_reasons = [
                _safe_error_text(getattr(candidate, "finish_reason", "bilinmiyor"))
                for candidate in (getattr(response, "candidates", None) or [])
            ]
            raise VisionServiceError(
                "Gemini boş bir fotoğraf açıklaması döndürdü. "
                f"Prompt feedback: {prompt_feedback}. "
                f"Finish reasons: {finish_reasons or ['yok']}."
            )
        return description


vision_service = VisionService()


__all__ = [
    "InvalidImageError",
    "SUPPORTED_IMAGE_TYPES",
    "SYSTEM_INSTRUCTION",
    "VisionConfig",
    "VisionService",
    "VisionServiceError",
    "vision_service",
]
