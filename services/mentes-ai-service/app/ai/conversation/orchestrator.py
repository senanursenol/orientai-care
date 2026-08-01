"""Orchestration from patient message to safe assistant response, RAG-backed."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..llm import LLMContext, LLMService, LLMServiceError, llm_service
from ..rag.retriever_service import retrieve_context
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


def _fetch_retrieved_context(message: str, patient_id: str | None) -> str | None:
    """Hasta bağlamını (ORI-31/RAG) çeker; hasta id yoksa veya sonuç bulunamazsa None döner."""
    if not patient_id:
        return None

    try:
        results = retrieve_context(question=message, patient_id=patient_id)
    except Exception:
        return None

    documents = (results.get("documents") or [[]])[0]
    if not documents:
        return None

    return "\n".join(documents)


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
    """Execute required stages, including patient-memory (RAG) retrieval when patient_id is given."""

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
        patient_id: str | None = None,
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

        retrieved_context = _fetch_retrieved_context(cleaned_message, patient_id)

        try:
            raw_response = await self.llm.generate(
                cleaned_message,
                llm_context,
                patient_context=patient_context,
                retrieved_context=retrieved_context,
                role="assistant",
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

    async def simulate_patient(
        self,
        assistant_message: str,
        *,
        emotion_state: str,
        patient_context: str | None = None,
        patient_id: str | None = None,
        history: str = "",
    ) -> ConversationResult:
        """
        Generate a synthetic patient response using the same AI pipeline.
        """

        if (
            not isinstance(assistant_message, str)
            or not assistant_message.strip()
        ):
            raise ConversationServiceError(
                "Assistant message cannot be empty.",
                stage="input",
            )

        cleaned_message = " ".join(
            assistant_message.split()
        )

        try:
            llm_context = self.policy_builder.build_patient_context(
                emotion_state
            )
        except Exception as exc:
            raise ConversationServiceError(
                "Patient response policy could not be created.",
                stage="response_policy",
            ) from exc

        retrieved_context = _fetch_retrieved_context(
            cleaned_message,
            patient_id,
        )

        try:
            raw_response = await self.llm.generate(
                cleaned_message,
                llm_context,
                patient_context=patient_context,
                retrieved_context=retrieved_context,
                history=history,
                role="patient",
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
            sentiment={
                "label": emotion_state,
                "score": 1.0,
                "model": "patient_simulator",
            },
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
