"""Assistant Evaluation Service."""

from __future__ import annotations
from .evaluation_prompt import build_evaluation_prompt

import json
from dataclasses import dataclass, field

from ..llm import (
    LLMService,
    LLMServiceError,
    llm_service,
)

from app.ai.llm import (
    LLMContext,
    ResponsePolicy,
    SafetyContext,
)

from .evaluation_models import EvaluationResult

class EvaluationServiceError(RuntimeError):
    """Raised when evaluation fails."""


@dataclass(slots=True)
class EvaluationService:

    llm: LLMService = field(
        default_factory=lambda: llm_service
    )

    async def evaluate(
        self,
        *,
        conversation: str,
        patient_context: str | None = None,
        retrieved_context: str | None = None,
    ) -> EvaluationResult:

        prompt = build_evaluation_prompt(
            conversation=conversation,
            patient_context=patient_context,
            retrieved_context=retrieved_context,
        )

        evaluation_context = LLMContext(
            emotional_state="evaluation",
            confidence="high",
            response_policy=ResponsePolicy(
                tone="calm_and_clear",
                length="short",
                acknowledge_feeling=False,
                ask_at_most_one_question=False,
                avoid_confrontation=True,
            ),
            safety=SafetyContext(
                needs_attention=False,
            ),
        )

        try:

            raw_response = await self.llm.generate(

                prompt,

                context=evaluation_context,

                patient_context=patient_context,

                retrieved_context=retrieved_context,

                history=conversation,

                role="evaluator",

            )

        except LLMServiceError as exc:

            raise EvaluationServiceError(
                str(exc)
            ) from exc

        try:

            data = json.loads(raw_response)

        except json.JSONDecodeError as exc:

            raise EvaluationServiceError(
                "Evaluation Agent invalid JSON returned."
            ) from exc

        overall_score = (

            data["rag_grounded"]

            + data["hallucination"]

            + data["empathy"]

            + data["guidance"]

            + data["safety"]

        )

        @property
        def passed(self):

            return self.overall_score >= 8

        return EvaluationResult(

            rag_grounded=data["rag_grounded"],

            hallucination=data["hallucination"],

            empathy=data["empathy"],

            guidance=data["guidance"],

            safety=data["safety"],

            overall_score=overall_score,

            strengths=data.get("strengths", []),

            improvements=data.get("improvements", []),

            summary=data.get("summary", ""),

        )


evaluation_service = EvaluationService()