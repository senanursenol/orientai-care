"""Turkish sentiment and anxiety analysis for the OrientAI orchestrator.

The transformer supplies positive/neutral/negative probabilities. A separate,
transparent anxiety layer handles care-domain phrases that a generic sentiment
model cannot represent, while respecting common Turkish negations.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import threading
import unicodedata
from dataclasses import dataclass, field
from typing import Protocol

import numpy as np

# Initialize the shared numeric/OpenMP runtime before PyTorch and CTranslate2.
# This ordering prevents duplicate Intel OpenMP initialization in the Conda
# environment when speech and sentiment models run in the same process.
_numeric_probe = np.ones((64, 64), dtype=np.float32)
np.matmul(_numeric_probe, _numeric_probe)

logger = logging.getLogger(__name__)

SENTIMENT_LABELS = ("anxious", "negative", "neutral", "positive")


class SentimentServiceError(RuntimeError):
    """Raised when sentiment inference cannot produce a result."""


def _configure_transformers_for_text_only() -> None:
    """Keep optional image backends out of Turkish BERT model loading."""
    import transformers.utils as transformers_utils
    from transformers.utils import import_utils as transformers_import_utils

    def torchvision_is_unavailable() -> bool:
        return False

    # Transformers 5 imports image helpers while resolving text-only BERT
    # classes. This service does not need torchvision, and hiding it here
    # prevents a mismatched optional build from breaking sentiment inference.
    transformers_utils.is_torchvision_available = torchvision_is_unavailable
    transformers_import_utils.is_torchvision_available = (
        torchvision_is_unavailable
    )


def _positive_int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default))
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if value <= 0:
        raise ValueError(f"{name} must be greater than zero")
    return value


def _probability(name: str, default: float) -> float:
    raw = os.getenv(name, str(default))
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number") from exc
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between zero and one")
    return value


@dataclass(frozen=True, slots=True)
class SentimentConfig:
    model_name: str = os.getenv(
        "SENTIMENT_MODEL_NAME",
        "savasy/bert-base-turkish-sentiment-cased",
    )
    max_length: int = _positive_int("SENTIMENT_MAX_LENGTH", 128)
    max_concurrent_requests: int = _positive_int(
        "SENTIMENT_MAX_CONCURRENT_REQUESTS", 1
    )
    anxiety_threshold: float = _probability("SENTIMENT_ANXIETY_THRESHOLD", 0.52)
    low_confidence_threshold: float = _probability(
        "SENTIMENT_LOW_CONFIDENCE_THRESHOLD", 0.58
    )
    local_files_only: bool = os.getenv(
        "SENTIMENT_LOCAL_FILES_ONLY", "false"
    ).strip().lower() in {"1", "true", "yes"}


class SentimentBackend(Protocol):
    model_name: str

    def predict(self, text: str) -> dict[str, float]:
        """Return negative, neutral, and positive probabilities."""


class TransformerSentimentBackend:
    """Lazy, process-wide Turkish BERT sentiment backend."""

    def __init__(self, config: SentimentConfig) -> None:
        self.config = config
        self.model_name = config.model_name
        self._tokenizer = None
        self._model = None
        self._torch = None
        self._load_lock = threading.Lock()
        self._inference_lock = threading.Lock()

    def _load(self):
        if self._model is not None and self._tokenizer is not None:
            return self._tokenizer, self._model

        with self._load_lock:
            if self._model is not None and self._tokenizer is not None:
                return self._tokenizer, self._model
            try:
                import torch

                _configure_transformers_for_text_only()
                from transformers import (
                    AutoModelForSequenceClassification,
                    AutoTokenizer,
                )

                try:
                    # Prefer the local cache so inference never depends on a
                    # network round trip after the model has been provisioned.
                    tokenizer = AutoTokenizer.from_pretrained(
                        self.model_name,
                        local_files_only=True,
                    )
                    model = AutoModelForSequenceClassification.from_pretrained(
                        self.model_name,
                        local_files_only=True,
                        use_safetensors=True,
                    )
                except OSError:
                    if self.config.local_files_only:
                        raise
                    tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                    model = AutoModelForSequenceClassification.from_pretrained(
                        self.model_name,
                        use_safetensors=True,
                    )
                model.eval()
            except Exception as exc:
                raise SentimentServiceError(
                    f"Sentiment model '{self.model_name}' could not be loaded"
                ) from exc

            self._tokenizer = tokenizer
            self._model = model
            self._torch = torch
            logger.info("Loaded Turkish sentiment model: %s", self.model_name)
        return self._tokenizer, self._model

    @staticmethod
    def _canonical_label(label: str) -> str:
        normalized = label.strip().casefold()
        aliases = {
            "label_0": "negative",
            "label_1": "neutral",
            "label_2": "positive",
            "negative": "negative",
            "neutral": "neutral",
            "positive": "positive",
        }
        if normalized not in aliases:
            raise SentimentServiceError(f"Unsupported sentiment label: {label}")
        return aliases[normalized]

    def predict(self, text: str) -> dict[str, float]:
        tokenizer, model = self._load()
        try:
            encoded = tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=self.config.max_length,
            )
            with self._inference_lock, self._torch.inference_mode():
                logits = model(**encoded).logits[0]
                probabilities = self._torch.softmax(logits, dim=-1).cpu().tolist()
        except Exception as exc:
            raise SentimentServiceError("Sentiment inference failed") from exc

        scores = {"negative": 0.0, "neutral": 0.0, "positive": 0.0}
        for index, score in enumerate(probabilities):
            raw_label = model.config.id2label.get(index, f"LABEL_{index}")
            scores[self._canonical_label(raw_label)] = float(score)
        return scores


@dataclass(frozen=True, slots=True)
class AnxietyAssessment:
    score: float
    signals: tuple[str, ...]


def _normalize_turkish(text: str) -> str:
    replacements = str.maketrans(
        {
            "ı": "i",
            "İ": "i",
            "ş": "s",
            "Ş": "s",
            "ğ": "g",
            "Ğ": "g",
            "ü": "u",
            "Ü": "u",
            "ö": "o",
            "Ö": "o",
            "ç": "c",
            "Ç": "c",
        }
    )
    normalized = unicodedata.normalize("NFKC", text).translate(replacements)
    normalized = normalized.casefold()
    return re.sub(r"[^a-z0-9]+", " ", normalized).strip()


@dataclass(frozen=True, slots=True)
class SafetyAssessment:
    """Rule-based safety intent result kept separate from sentiment."""

    label: str
    score: float
    severity: str
    needs_attention: bool
    signals: tuple[str, ...]


class TurkishSafetyDetector:
    """Detect explicit violent and self-harm intent in Turkish text.

    This is a transparent prototype safety layer, not a clinical or law-
    enforcement risk assessment. Reported/quoted threats are retained as a
    low-severity signal without being treated as an immediate threat.
    """

    _REPORTED_CONTEXT = (
        "dedi",
        "diyor",
        "demisti",
        "soyledi",
        "cumlesi",
        "ifadesi",
        "filmde",
        "kitapta",
        "hikayede",
        "haberde",
        "ruyamda",
    )
    _DENIAL_CONTEXT = (
        "demiyorum",
        "soylemiyorum",
        "oyle bir niyetim yok",
        "zarar verme niyetim yok",
    )
    _SELF_HARM_PATTERNS = (
        (r"\bkendimi\s+oldurecegim\b", "kendimi oldurecegim", 0.99),
        (r"\bcanima\s+kiyacagim\b", "canima kiyma niyeti", 0.99),
        (r"\bintihar\s+(?:edecegim|etmek istiyorum)\b", "intihar niyeti", 0.99),
        (r"\bkendime\s+zarar\s+verecegim\b", "kendine zarar verme niyeti", 0.98),
        (r"\byasamak\s+istemiyorum\b", "yasamak istemiyorum", 0.94),
    )
    _VIOLENT_PATTERNS = (
        (
            r"\b(?:butun\s+)?dunya(?:\s+yi|yi)?\s+yakacagim\b",
            "dunyayi yakma tehdidi",
            0.98,
        ),
        (
            r"\b(?:seni|onu|onlari|herkesi|insanlari|ailemi|komsuyu)\s+"
            r"(?:oldurecegim|oldururum|vuracagim|bicaklayacagim|yakacagim)\b",
            "kisiye yonelik siddet tehdidi",
            0.99,
        ),
        (
            r"\b(?:evi|evini|burayi|okulu|hastaneyi|binayi)\s+yakacagim\b",
            "mekana yonelik yakma tehdidi",
            0.97,
        ),
        (
            r"\b(?:oldurecegim|gebertirim|vuracagim|bicaklayacagim|saldiracagim)\b",
            "acik siddet niyeti",
            0.96,
        ),
        (r"\bzarar\s+verecegim\b", "zarar verme niyeti", 0.94),
        (r"\bcanini\s+yakacagim\b", "zarar verme tehdidi", 0.94),
    )

    @staticmethod
    def _matches(
        normalized: str,
        patterns: tuple[tuple[str, str, float], ...],
    ) -> list[tuple[str, float]]:
        return [
            (signal, score)
            for pattern, signal, score in patterns
            if re.search(pattern, normalized)
        ]

    def assess(self, text: str) -> SafetyAssessment:
        normalized = _normalize_turkish(text)
        self_harm = self._matches(normalized, self._SELF_HARM_PATTERNS)
        violent = self._matches(normalized, self._VIOLENT_PATTERNS)

        if not self_harm and not violent:
            return SafetyAssessment("safe", 0.0, "none", False, ())

        if any(marker in normalized for marker in self._DENIAL_CONTEXT):
            return SafetyAssessment("safe", 0.0, "none", False, ())

        matches = self_harm or violent
        signals = tuple(signal for signal, _ in matches)
        score = max(score for _, score in matches)
        if any(marker in normalized for marker in self._REPORTED_CONTEXT):
            return SafetyAssessment(
                "reported_threat",
                round(min(0.55, score * 0.5), 6),
                "low",
                False,
                signals,
            )

        return SafetyAssessment(
            "self_harm" if self_harm else "violent_threat",
            score,
            "high",
            True,
            signals,
        )


class TurkishAnxietyDetector:
    """Transparent care-domain anxiety detector with negation handling."""

    _NEGATED = (
        "artik korkmuyorum",
        "korkmuyorum",
        "korkmus degilim",
        "endiseli degilim",
        "endiselenmiyorum",
        "panik degilim",
        "tedirgin degilim",
        "huzursuz degilim",
        "guvende hissetmiyor degilim",
        "kaybolmadim",
    )
    _WEIGHTED_PATTERNS = (
        ("yardim edin", 0.90),
        ("guvende hissetmiyorum", 0.88),
        ("kayboldum", 0.88),
        ("panik oldum", 0.86),
        ("cok korkuyorum", 0.86),
        ("korkuyorum", 0.78),
        ("cok endiseliyim", 0.82),
        ("endiseliyim", 0.72),
        ("endiselendiriyor", 0.70),
        ("ne yapacagimi bilmiyorum", 0.75),
        ("eve nasil doneceg", 0.82),
        ("kimseyi tanimiyorum", 0.72),
        ("beni yalniz birakma", 0.78),
        ("yalniz kalmak istemiyorum", 0.74),
        ("bir sey mi oldu", 0.62),
        ("bir sey oldu mu", 0.62),
        ("basima bir sey", 0.74),
        ("odami bulamiyorum", 0.76),
        ("evimi bulamiyorum", 0.78),
        ("nerede oldugumu anlayamiyorum", 0.74),
        ("yanimda kal", 0.62),
        ("icime kotu seyler", 0.68),
        ("korku var", 0.76),
        ("korku hiss", 0.76),
        ("ne olacak", 0.58),
        ("telas", 0.72),
        ("kaygi", 0.76),
        ("endise duy", 0.72),
        ("donemeyeceg", 0.70),
        ("yabanci geliyor", 0.60),
        ("kafam karis", 0.66),
        ("kafam cok karis", 0.68),
        ("kotu bir sey gelecek", 0.76),
        ("basina bir sey", 0.72),
        ("sakinlesemiyorum", 0.68),
        ("tanidik gelmiyor", 0.65),
        ("urktum", 0.72),
        ("meraktan", 0.58),
        ("bulamiyorum", 0.48),
        ("hatirlamiyorum", 0.42),
        ("tedirginim", 0.72),
        ("huzursuzum", 0.68),
    )

    @staticmethod
    def _normalize(text: str) -> str:
        return _normalize_turkish(text)

    def assess(self, text: str, negative_score: float) -> AnxietyAssessment:
        normalized = self._normalize(text)
        for phrase in self._NEGATED:
            normalized = normalized.replace(phrase, " ")
        normalized = re.sub(r"\s+", " ", normalized).strip()

        hits: list[tuple[str, float]] = []
        for phrase, weight in self._WEIGHTED_PATTERNS:
            if phrase in normalized:
                # Keep only the strongest overlapping expression.
                if any(phrase in existing for existing, _ in hits):
                    continue
                hits = [item for item in hits if item[0] not in phrase]
                hits.append((phrase, weight))

        if not hits:
            return AnxietyAssessment(score=0.0, signals=())

        combined = 1.0
        for _, weight in hits:
            combined *= 1.0 - weight
        cue_score = 1.0 - combined
        score = min(0.99, cue_score * 0.88 + negative_score * 0.12)
        return AnxietyAssessment(
            score=score,
            signals=tuple(phrase for phrase, _ in hits),
        )


@dataclass(frozen=True, slots=True)
class PolarityAssessment:
    label: str | None
    signals: tuple[str, ...]


class TurkishPolarityDetector:
    """Detect explicit affect; no affect is treated as neutral information."""

    _NEGATED_NEGATIVE = (
        "uzgun degilim",
        "mutsuz degilim",
        "kotu hissetmiyorum",
        "canim sikkin degil",
        "rahatsiz degilim",
        "yalniz degilim",
        "moralim bozuk degil",
    )
    _POSITIVE = (
        "iyi hissed",
        "mutlu old",
        "mutluy",
        "cok mutlu",
        "mutlu hissed",
        "cok guzel",
        "guzel olmus",
        "guzeldi",
        "rahatlat",
        "harika",
        "sevind",
        "tesekkur",
        "guvende ve huzurlu",
        "huzurlu hissed",
        "keyfim yerinde",
        "her sey yolunda",
        "simdi iyiyim",
        "memnunum",
        "neseliyim",
        "umutluyum",
        "hosuma gitti",
        "yuzum guldu",
        "nese",
        "iyi geldi",
        "memnuniyet",
        "keyifli",
        "icim rahat",
        "sevinc",
        "moralim cok yuksek",
        "ferahla",
        "emniyette hissed",
    )
    _NEGATIVE = (
        "kotu hissed",
        "hicbir sey yapmak istemiyorum",
        "nefret",
        "uzgun",
        "canim sikkin",
        "moralim bozuk",
        "memnun degilim",
        "yorgunum",
        "keyfim yok",
        "kotu kok",
        "berbat",
        "yalniz ve mutsuz",
        "mutsuz",
        "iyi degilim",
        "mutlu degilim",
        "rahatsizim",
        "biktim",
        "sinirliyim",
        "kizginim",
        "canim aciyor",
        "agrim var",
        "iyi degil",
        "hevesim yok",
        "degersiz",
        "keder",
        "rahatsiz etti",
        "aglamak",
        "hoslanmiyorum",
        "hoslanmadi",
        "huzun",
        "isteksiz",
        "bitkin",
        "usan",
        "umutsuz",
        "icimden hicbir sey gelmiyor",
    )

    def assess(self, text: str, base_scores: dict[str, float]) -> PolarityAssessment:
        normalized = _normalize_turkish(text)
        for phrase in self._NEGATED_NEGATIVE:
            normalized = normalized.replace(phrase, " ")
        normalized = re.sub(r"\s+", " ", normalized).strip()

        positive = tuple(phrase for phrase in self._POSITIVE if phrase in normalized)
        negative = tuple(phrase for phrase in self._NEGATIVE if phrase in normalized)
        if positive and not negative:
            return PolarityAssessment("positive", positive)
        if negative and not positive:
            return PolarityAssessment("negative", negative)
        if positive and negative:
            label = max(
                ("negative", "positive"),
                key=lambda candidate: base_scores[candidate],
            )
            signals = negative if label == "negative" else positive
            return PolarityAssessment(label, signals)
        return PolarityAssessment(None, ())


@dataclass(slots=True)
class SentimentService:
    config: SentimentConfig = field(default_factory=SentimentConfig)
    backend: SentimentBackend | None = None
    anxiety_detector: TurkishAnxietyDetector = field(
        default_factory=TurkishAnxietyDetector
    )
    polarity_detector: TurkishPolarityDetector = field(
        default_factory=TurkishPolarityDetector
    )
    safety_detector: TurkishSafetyDetector = field(
        default_factory=TurkishSafetyDetector
    )
    _inference_slots: asyncio.Semaphore = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if self.backend is None:
            self.backend = TransformerSentimentBackend(self.config)
        self._inference_slots = asyncio.Semaphore(
            self.config.max_concurrent_requests
        )

    def analyze_sync(
        self,
        text: str,
        *,
        include_care_calibration: bool = True,
    ) -> dict:
        if not isinstance(text, str):
            raise SentimentServiceError("Sentiment input must be text")
        cleaned = re.sub(r"\s+", " ", text).strip()
        if not cleaned:
            raise SentimentServiceError("Sentiment input cannot be empty")

        assert self.backend is not None
        base_scores = self.backend.predict(cleaned)
        safety = self.safety_detector.assess(cleaned)
        anxiety = (
            self.anxiety_detector.assess(cleaned, base_scores["negative"])
            if include_care_calibration
            else AnxietyAssessment(score=0.0, signals=())
        )
        polarity = (
            self.polarity_detector.assess(cleaned, base_scores)
            if include_care_calibration
            else PolarityAssessment(label=None, signals=())
        )

        if safety.needs_attention:
            safety_negative = max(safety.score, base_scores["negative"])
            remaining = 1.0 - safety_negative
            nonnegative_total = base_scores["neutral"] + base_scores["positive"]
            scores = {
                "anxious": 0.0,
                "negative": safety_negative,
                "neutral": remaining
                * base_scores["neutral"]
                / max(nonnegative_total, 1e-12),
                "positive": remaining
                * base_scores["positive"]
                / max(nonnegative_total, 1e-12),
            }
            label = "negative"
            signals = safety.signals
        elif anxiety.score >= self.config.anxiety_threshold:
            remaining = 1.0 - anxiety.score
            scores = {
                "anxious": anxiety.score,
                **{
                    label: base_scores[label] * remaining
                    for label in ("negative", "neutral", "positive")
                },
            }
            label = "anxious"
            signals = anxiety.signals
        elif include_care_calibration and polarity.label is None:
            # The selected BERT model is deliberately strong at Turkish
            # polarity but has no neutral class. In care dialogue, factual
            # requests and orientation statements must remain neutral unless
            # an explicit affective signal is present.
            # The base model is binary and can be highly confident even for
            # factual requests. Keep neutral as the routing label, but lower
            # its confidence when the binary model strongly disagrees instead
            # of presenting a fixed, artificial 0.75 as model certainty.
            polarity_total = base_scores["negative"] + base_scores["positive"]
            disagreement = abs(
                base_scores["negative"] - base_scores["positive"]
            ) / max(polarity_total, 1e-12)
            calibrated_neutral = max(0.51, 0.75 - 0.25 * disagreement)
            neutral_score = min(
                0.95,
                max(base_scores["neutral"], calibrated_neutral),
            )
            remaining = 1.0 - neutral_score
            scores = {
                "anxious": 0.0,
                "negative": remaining
                * base_scores["negative"]
                / max(polarity_total, 1e-12),
                "neutral": neutral_score,
                "positive": remaining
                * base_scores["positive"]
                / max(polarity_total, 1e-12),
            }
            label = "neutral"
            signals = ()
        else:
            scores = {"anxious": anxiety.score, **base_scores}
            total = sum(scores.values())
            scores = {key: value / total for key, value in scores.items()}
            label = polarity.label or max(base_scores, key=base_scores.get)
            signals = polarity.signals

        score = float(scores[label])
        ordered_scores = {
            name: round(float(scores.get(name, 0.0)), 6)
            for name in SENTIMENT_LABELS
        }
        return {
            "label": label,
            "score": round(score, 6),
            "scores": ordered_scores,
            "low_confidence": score < self.config.low_confidence_threshold,
            "needs_attention": (
                label in {"anxious", "negative"} or safety.needs_attention
            ),
            "signals": list(signals),
            "safety": {
                "label": safety.label,
                "score": round(float(safety.score), 6),
                "severity": safety.severity,
                "needs_attention": safety.needs_attention,
                "signals": list(safety.signals),
            },
            "model": self.backend.model_name,
            "method": "transformer+care+safety-calibration-v2",
        }

    async def analyze(self, text: str) -> dict:
        async with self._inference_slots:
            return await asyncio.to_thread(self.analyze_sync, text)


sentiment_service = SentimentService()


__all__ = [
    "AnxietyAssessment",
    "SENTIMENT_LABELS",
    "SafetyAssessment",
    "SentimentConfig",
    "SentimentService",
    "SentimentServiceError",
    "TransformerSentimentBackend",
    "TurkishAnxietyDetector",
    "TurkishPolarityDetector",
    "TurkishSafetyDetector",
    "sentiment_service",
]
