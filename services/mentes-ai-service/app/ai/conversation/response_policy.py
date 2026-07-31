"""Convert sentiment and safety results into explicit LLM response controls."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..llm import LLMContext, ResponsePolicy, SafetyContext


@dataclass(frozen=True, slots=True)
class ResponsePolicyBuilder:
    """Build deterministic policy metadata without asking the LLM to infer it."""

    high_confidence_threshold: float = 0.80
    medium_confidence_threshold: float = 0.58

    def _confidence(self, score: float, low_confidence: bool) -> str:
        if low_confidence or score < self.medium_confidence_threshold:
            return "low"
        if score >= self.high_confidence_threshold:
            return "high"
        return "medium"

    @staticmethod
    def _policy_for(
        emotional_state: str,
        needs_attention: bool,
    ) -> ResponsePolicy:
        if needs_attention:
            return ResponsePolicy(
                tone="calm_and_direct",
                length="short",
                acknowledge_feeling=True,
                ask_at_most_one_question=True,
                avoid_confrontation=True,
            )
        if emotional_state == "anxious":
            return ResponsePolicy(
                tone="calm_and_reassuring",
                length="short",
                acknowledge_feeling=True,
                ask_at_most_one_question=True,
                avoid_confrontation=True,
            )
        if emotional_state == "negative":
            return ResponsePolicy(
                tone="empathetic_and_supportive",
                length="short",
                acknowledge_feeling=True,
                ask_at_most_one_question=True,
                avoid_confrontation=True,
            )
        if emotional_state == "positive":
            return ResponsePolicy(
                tone="warm_and_encouraging",
                length="short",
                acknowledge_feeling=False,
                ask_at_most_one_question=True,
                avoid_confrontation=True,
            )
        return ResponsePolicy(
            tone="calm_and_clear",
            length="short",
            acknowledge_feeling=False,
            ask_at_most_one_question=True,
            avoid_confrontation=True,
        )

    def build(self, sentiment: dict[str, Any]) -> LLMContext:
        """Return the exact structured context consumed by ``LLMService``."""

        emotional_state = str(sentiment.get("label") or "unknown").strip()
        try:
            score = float(sentiment.get("score") or 0.0)
        except (TypeError, ValueError):
            score = 0.0
        low_confidence = bool(sentiment.get("low_confidence", True))

        safety_data = sentiment.get("safety")
        if not isinstance(safety_data, dict):
            safety_data = {}
        needs_attention = bool(
            safety_data.get(
                "needs_attention",
                sentiment.get("needs_attention", False),
            )
        )

        return LLMContext(
            emotional_state=emotional_state,
            confidence=self._confidence(score, low_confidence),
            response_policy=self._policy_for(
                emotional_state,
                needs_attention,
            ),
            safety=SafetyContext(needs_attention=needs_attention),
        )


response_policy_builder = ResponsePolicyBuilder()


__all__ = ["ResponsePolicyBuilder", "response_policy_builder"]
