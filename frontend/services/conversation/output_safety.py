"""Deterministic final check for text returned by the conversational LLM."""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..llm import LLMContext


class OutputSafetyError(RuntimeError):
    """Raised when no patient-safe assistant text can be produced."""


@dataclass(frozen=True, slots=True)
class OutputSafetyResult:
    """Final text and an auditable summary of the checks applied to it."""

    text: str
    blocked: bool
    modified: bool
    reasons: tuple[str, ...]
    method: str = "deterministic-output-safety-v1"

    def metadata(self) -> dict[str, object]:
        return {
            "blocked": self.blocked,
            "modified": self.modified,
            "reasons": list(self.reasons),
            "method": self.method,
        }


class OutputSafetyService:
    """Reject unsafe model behavior and enforce response-policy constraints."""

    _UNSAFE_PATTERNS = (
        (
            re.compile(
                r"\b(?:sen|siz)\s+(?:kesinlikle\s+)?"
                r"(?:alzheimer|demans)\s+hastas[ıi]s[ıi]n",
                re.IGNORECASE,
            ),
            "unsupported_diagnosis",
        ),
        (
            re.compile(
                r"\b(?:ilac[ıi]n[ıi]|ilaçlarını?|tedaviyi)\s+"
                r"(?:b[ıi]rak|kes|kullanma)",
                re.IGNORECASE,
            ),
            "unsafe_medical_instruction",
        ),
        (
            re.compile(
                r"\b(?:doktora|hekime|acil deste[ğg]e)\s+"
                r"(?:gitme|başvurma|gerek yok)",
                re.IGNORECASE,
            ),
            "discourages_professional_help",
        ),
        (
            re.compile(
                r"\b(?:saçmal[ıi]yorsun|uyduruyorsun|yan[ıi]l[ıi]yorsun|"
                r"sus|bunu anlamal[ıi]s[ıi]n)\b",
                re.IGNORECASE,
            ),
            "confrontational_language",
        ),
        (
            re.compile(
                r"\b(?:kendine zarar ver|kendini öldür|başkasını öldür)\b",
                re.IGNORECASE,
            ),
            "harmful_instruction",
        ),
    )
    _MAX_LENGTHS = {
        "short": 600,
        "medium": 1_200,
        "long": 2_000,
    }

    @staticmethod
    def _fallback(context: LLMContext) -> str:
        if context.safety.needs_attention:
            return (
                "Şu anda yalnız kalmamanız önemli. Lütfen hemen yakınınızdaki "
                "güvendiğiniz bir kişiden veya profesyonel destekten yardım "
                "isteyin. Yanınızda güvenebileceğiniz biri var mı?"
            )
        if context.emotional_state == "anxious":
            return (
                "Bunun sizi kaygılandırdığını anlıyorum. Yanınızdayım; birlikte "
                "sakin ve küçük bir adımla ilerleyebiliriz. Size şimdi en çok "
                "ne yardımcı olur?"
            )
        if context.emotional_state == "negative":
            return (
                "Bunun sizin için zor olduğunu anlıyorum. Sizi dinliyorum ve "
                "yanınızdayım. Şu anda size nasıl destek olabilirim?"
            )
        return (
            "Sizi dinliyorum ve yanınızdayım. Bunu birlikte sakin bir şekilde "
            "ele alabiliriz."
        )

    @staticmethod
    def _keep_at_most_one_question(text: str) -> tuple[str, bool]:
        if text.count("?") <= 1:
            return text, False

        question_seen = False
        kept: list[str] = []
        parts = re.split(r"(?<=[.!?])\s+", text)
        for part in parts:
            if "?" not in part:
                kept.append(part)
                continue
            if question_seen:
                continue
            question_seen = True
            first_question = part.find("?")
            kept.append(
                part[: first_question + 1]
                + part[first_question + 1 :].replace("?", ".")
            )
        return " ".join(kept).strip(), True

    @staticmethod
    def _limit_length(text: str, limit: int) -> tuple[str, bool]:
        if len(text) <= limit:
            return text, False

        shortened = text[:limit].rsplit(" ", 1)[0].rstrip(" ,;:")
        sentence_end = max(
            shortened.rfind("."),
            shortened.rfind("!"),
            shortened.rfind("?"),
        )
        if sentence_end >= max(0, limit // 2):
            shortened = shortened[: sentence_end + 1]
        elif shortened and shortened[-1] not in ".!?":
            shortened += "."
        return shortened, True

    def check(self, text: str, context: LLMContext) -> OutputSafetyResult:
        """Return safe patient-facing text plus non-sensitive audit metadata."""

        if not isinstance(text, str) or not text.strip():
            raise OutputSafetyError("LLM çıktısı boş olamaz.")

        normalized = re.sub(r"\s+", " ", text).strip()
        reasons = [
            reason
            for pattern, reason in self._UNSAFE_PATTERNS
            if pattern.search(normalized)
        ]
        if reasons:
            return OutputSafetyResult(
                text=self._fallback(context),
                blocked=True,
                modified=True,
                reasons=tuple(dict.fromkeys(reasons)),
            )

        modified = normalized != text
        if context.response_policy.ask_at_most_one_question:
            normalized, questions_modified = self._keep_at_most_one_question(
                normalized
            )
            if questions_modified:
                reasons.append("question_limit_enforced")
                modified = True

        max_length = self._MAX_LENGTHS.get(
            context.response_policy.length,
            self._MAX_LENGTHS["short"],
        )
        normalized, length_modified = self._limit_length(
            normalized,
            max_length,
        )
        if length_modified:
            reasons.append("length_limit_enforced")
            modified = True

        if not normalized:
            raise OutputSafetyError(
                "Güvenlik kontrolünden sonra kullanılabilir yanıt kalmadı."
            )
        return OutputSafetyResult(
            text=normalized,
            blocked=False,
            modified=modified,
            reasons=tuple(reasons),
        )


output_safety_service = OutputSafetyService()


__all__ = [
    "OutputSafetyError",
    "OutputSafetyResult",
    "OutputSafetyService",
    "output_safety_service",
]
