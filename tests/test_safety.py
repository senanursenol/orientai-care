from __future__ import annotations

import unittest

from service.sentiment import (
    SentimentConfig,
    SentimentService,
    TurkishSafetyDetector,
)


class FakeBackend:
    model_name = "fake-turkish-sentiment"

    def __init__(self, negative: float, positive: float) -> None:
        self.scores = {
            "negative": negative,
            "neutral": 0.0,
            "positive": positive,
        }

    def predict(self, text: str) -> dict[str, float]:
        del text
        return self.scores.copy()


class TurkishSafetyDetectorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.detector = TurkishSafetyDetector()

    def test_detects_world_burning_threat(self) -> None:
        result = self.detector.assess("Bütün dünya'yı yakacağım.")

        self.assertEqual(result.label, "violent_threat")
        self.assertEqual(result.severity, "high")
        self.assertTrue(result.needs_attention)
        self.assertGreaterEqual(result.score, 0.98)

    def test_detects_direct_violence_against_a_person(self) -> None:
        result = self.detector.assess("Seni öldüreceğim.")

        self.assertEqual(result.label, "violent_threat")
        self.assertTrue(result.needs_attention)

    def test_detects_self_harm_intent_separately(self) -> None:
        result = self.detector.assess("Kendime zarar vereceğim.")

        self.assertEqual(result.label, "self_harm")
        self.assertEqual(result.severity, "high")
        self.assertTrue(result.needs_attention)

    def test_reported_fictional_threat_is_not_immediate(self) -> None:
        result = self.detector.assess(
            "Filmde karakter bütün dünyayı yakacağım dedi."
        )

        self.assertEqual(result.label, "reported_threat")
        self.assertEqual(result.severity, "low")
        self.assertFalse(result.needs_attention)

    def test_denied_threat_is_safe(self) -> None:
        result = self.detector.assess("Dünyayı yakacağım demiyorum.")

        self.assertEqual(result.label, "safe")
        self.assertFalse(result.needs_attention)

    def test_benign_use_of_fire_verb_is_safe(self) -> None:
        result = self.detector.assess("Akşam sobayı yakacağım.")

        self.assertEqual(result.label, "safe")
        self.assertFalse(result.needs_attention)


class SafetyCalibratedSentimentTests(unittest.TestCase):
    def test_threat_overrides_neutral_fallback(self) -> None:
        service = SentimentService(
            config=SentimentConfig(),
            backend=FakeBackend(negative=0.927865, positive=0.072135),
        )

        result = service.analyze_sync("Bütün dünya'yı yakacağım.")

        self.assertEqual(result["label"], "negative")
        self.assertGreaterEqual(result["score"], 0.98)
        self.assertFalse(result["low_confidence"])
        self.assertTrue(result["needs_attention"])
        self.assertEqual(result["safety"]["label"], "violent_threat")
        self.assertEqual(result["safety"]["severity"], "high")

    def test_strong_binary_disagreement_marks_neutral_as_low_confidence(self) -> None:
        service = SentimentService(
            config=SentimentConfig(),
            backend=FakeBackend(negative=0.94, positive=0.06),
        )

        result = service.analyze_sync("Bir bardak su istiyorum.")

        self.assertEqual(result["label"], "neutral")
        self.assertTrue(result["low_confidence"])
        self.assertEqual(result["safety"]["label"], "safe")


if __name__ == "__main__":
    unittest.main()
