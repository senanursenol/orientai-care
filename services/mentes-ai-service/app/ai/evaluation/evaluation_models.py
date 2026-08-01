"""Data models for Assistant Evaluation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(slots=True)
class EvaluationResult:
    """
    Result returned by the Evaluation Agent.
    """

    rag_grounded: int
    empathy: int
    guidance: int
    safety: int
    hallucination: int

    overall_score: float

    strengths: List[str] = field(default_factory=list)
    improvements: List[str] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict:
        return {
            "rag_grounded": self.rag_grounded,
            "empathy": self.empathy,
            "guidance": self.guidance,
            "safety": self.safety,
            "hallucination": self.hallucination,
            "overall_score": self.overall_score,
            "strengths": self.strengths,
            "improvements": self.improvements,
            "summary": self.summary,
        }