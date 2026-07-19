from __future__ import annotations

import asyncio
import unittest

from service.sentiment import (
    SentimentConfig,
    SentimentService,
    SentimentServiceError,
    TurkishAnxietyDetector,
    TurkishPolarityDetector,
)


class FakeBackend:
    model_name = "fake-turkish-sentiment"

    def __init__(self, scores: dict[str, float]) -> None:
        self.scores = scores

    def predict(self, text: str) -> dict[str, float]:
        del text
        return self.scores.copy()


class TurkishAnxietyDetectorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.detector = TurkishAnxietyDetector()

    def test_detects_explicit_anxiety(self) -> None:
        result = self.detector.assess(
            "Kayboldum, eve nasıl döneceğimi bilmiyorum ve korkuyorum.",
            negative_score=0.8,
        )
        self.assertGreater(result.score, 0.8)
        self.assertIn("kayboldum", result.signals)

    def test_respects_negated_anxiety(self) -> None:
        result = self.detector.assess(
            "Artık korkmuyorum, şimdi kendimi iyi hissediyorum.",
            negative_score=0.05,
        )
        self.assertEqual(result.score, 0.0)
        self.assertEqual(result.signals, ())

    def test_plain_location_question_is_not_anxiety(self) -> None:
        result = self.detector.assess("İlacım nerede?", negative_score=0.2)
        self.assertEqual(result.score, 0.0)


class TurkishPolarityDetectorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.detector = TurkishPolarityDetector()
        self.base = {"negative": 0.2, "neutral": 0.0, "positive": 0.8}

    def test_factual_request_has_no_polarity(self) -> None:
        result = self.detector.assess("Bir bardak su istiyorum.", self.base)
        self.assertIsNone(result.label)

    def test_detects_negative_mood(self) -> None:
        result = self.detector.assess("Canım sıkkın ve moralim bozuk.", self.base)
        self.assertEqual(result.label, "negative")

    def test_negated_negative_with_happiness_is_positive(self) -> None:
        result = self.detector.assess(
            "Üzgün değilim, ailem yanımda ve mutluyum.", self.base
        )
        self.assertEqual(result.label, "positive")


class SentimentServiceTests(unittest.TestCase):
    def test_anxiety_overrides_generic_negative_sentiment(self) -> None:
        service = SentimentService(
            config=SentimentConfig(),
            backend=FakeBackend(
                {"negative": 0.80, "neutral": 0.15, "positive": 0.05}
            ),
        )
        result = service.analyze_sync("Kayboldum ve çok korkuyorum.")
        self.assertEqual(result["label"], "anxious")
        self.assertTrue(result["needs_attention"])

    def test_negative_without_anxiety_remains_negative(self) -> None:
        service = SentimentService(
            config=SentimentConfig(),
            backend=FakeBackend(
                {"negative": 0.75, "neutral": 0.20, "positive": 0.05}
            ),
        )
        result = service.analyze_sync("Bugün çok üzgünüm.")
        self.assertEqual(result["label"], "negative")
        self.assertIn("uzgun", result["signals"])

    def test_async_manage_contract_returns_dictionary(self) -> None:
        service = SentimentService(
            config=SentimentConfig(),
            backend=FakeBackend(
                {"negative": 0.05, "neutral": 0.10, "positive": 0.85}
            ),
        )
        result = asyncio.run(service.analyze("Bugün çok mutluyum."))
        self.assertEqual(result["label"], "positive")
        self.assertIn("score", result)
        self.assertIn("scores", result)

    def test_rejects_empty_text(self) -> None:
        service = SentimentService(
            config=SentimentConfig(),
            backend=FakeBackend(
                {"negative": 0.1, "neutral": 0.8, "positive": 0.1}
            ),
        )
        with self.assertRaises(SentimentServiceError):
            service.analyze_sync("   ")


if __name__ == "__main__":
    unittest.main()
