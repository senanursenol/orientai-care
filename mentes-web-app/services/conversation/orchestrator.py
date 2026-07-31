"""RAG-free orchestration from patient message to safe assistant response."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..llm import LLMContext, LLMService, LLMServiceError, llm_service
from ..sentiment.sentiment import (
    SentimentService,
    SentimentServiceError,
    sentiment_service,
)
from .output_safety import (
    OutputSafetyError,
    OutputSafetyService,
    output_safety_service,
)
from .response_policy import ResponsePolicyBuilder, response_policy_builder


class ConversationServiceError(RuntimeError):
    """Raised when a required stage of the conversation pipeline fails."""

    def __init__(
        self,
        message: str,
        *,
        stage: str,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.stage = stage
        self.status_code = status_code


@dataclass(frozen=True, slots=True)
class ConversationResult:
    """Result shared by text and voice API adapters."""

    input: str
    sentiment: dict[str, Any]
    llm_context: LLMContext
    assistant_response: str
    output_safety: dict[str, object]
    model: str


@dataclass(slots=True)
class ConversationService:
    """Execute required stages while deliberately omitting unavailable RAG."""

    sentiment: SentimentService = field(default_factory=lambda: sentiment_service)
    policy_builder: ResponsePolicyBuilder = field(
        default_factory=lambda: response_policy_builder
    )
    llm: LLMService = field(default_factory=lambda: llm_service)
    output_safety: OutputSafetyService = field(
        default_factory=lambda: output_safety_service
    )

    async def respond(
        self,
        message: str,
        *,
        sentiment_result: dict[str, Any] | None = None,
        patient_context: str | None = None,
    ) -> ConversationResult:
        """Generate a safe response from text or an already-transcribed voice."""

        if not isinstance(message, str) or not message.strip():
            raise ConversationServiceError(
                "Kullanıcı mesajı boş olamaz.",
                stage="input",
            )
        cleaned_message = " ".join(message.split())

        if sentiment_result is None:
            try:
                sentiment_result = await self.sentiment.analyze(cleaned_message)
            except SentimentServiceError as exc:
                raise ConversationServiceError(
                    "Sentiment ve safety analizi tamamlanamadı.",
                    stage="sentiment",
                ) from exc
        elif sentiment_result.get("model") == "unavailable":
            raise ConversationServiceError(
                "Ses mesajının sentiment ve safety analizi tamamlanamadı.",
                stage="sentiment",
            )

        try:
            llm_context = self.policy_builder.build(sentiment_result)
        except (TypeError, ValueError, KeyError) as exc:
            raise ConversationServiceError(
                "Yanıt politikası oluşturulamadı.",
                stage="response_policy",
            ) from exc

        try:
            raw_response = await self.llm.generate(
                cleaned_message,
                llm_context,
                patient_context=patient_context,
                # RAG is intentionally omitted until its data source is ready.
                retrieved_context=None,
            )
        except LLMServiceError as exc:
            raise ConversationServiceError(
                str(exc),
                stage="llm",
                status_code=exc.status_code,
            ) from exc

        try:
            safe_response = self.output_safety.check(
                raw_response,
                llm_context,
            )
        except OutputSafetyError as exc:
            raise ConversationServiceError(
                str(exc),
                stage="output_safety",
            ) from exc

        return ConversationResult(
            input=cleaned_message,
            sentiment=sentiment_result,
            llm_context=llm_context,
            assistant_response=safe_response.text,
            output_safety=safe_response.metadata(),
            model=self.llm.config.model,
        )


conversation_service = ConversationService()


__all__ = [
    "ConversationResult",
    "ConversationService",
    "ConversationServiceError",
    "conversation_service",
]
