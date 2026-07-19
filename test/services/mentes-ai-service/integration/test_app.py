from __future__ import annotations

import asyncio
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from service.app import TextInputRequest, analyze_text
from service.sentiment import SentimentServiceError


class FakeSentimentService:
    def __init__(self, *, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.received_text = ""

    async def analyze(self, text: str) -> dict[str, object]:
        self.received_text = text
        if self.should_fail:
            raise SentimentServiceError("unavailable")
        return {
            "label": "positive",
            "score": 0.87,
            "scores": {
                "anxious": 0.01,
                "negative": 0.02,
                "neutral": 0.10,
                "positive": 0.87,
            },
            "low_confidence": False,
            "needs_attention": False,
            "signals": [],
            "safety": {
                "label": "safe",
                "score": 0.0,
                "severity": "none",
                "needs_attention": False,
                "signals": [],
            },
            "model": "fake",
            "method": "test",
        }


class TextAnalysisEndpointTests(unittest.TestCase):
    def test_text_is_trimmed_and_forwarded_to_sentiment(self) -> None:
        fake = FakeSentimentService()
        with patch("service.app.sentiment_service", fake):
            response = asyncio.run(
                analyze_text(TextInputRequest(text="  Bugün çok mutluyum.  "))
            )

        self.assertEqual(response.input, "Bugün çok mutluyum.")
        self.assertEqual(fake.received_text, response.input)
        self.assertEqual(response.sentiment.label, "positive")
        self.assertFalse(response.sentiment.low_confidence)

    def test_whitespace_only_text_is_rejected(self) -> None:
        with self.assertRaises(HTTPException) as context:
            asyncio.run(analyze_text(TextInputRequest(text="   ")))

        self.assertEqual(context.exception.status_code, 422)

    def test_sentiment_outage_returns_gateway_error(self) -> None:
        fake = FakeSentimentService(should_fail=True)
        with patch("service.app.sentiment_service", fake):
            with self.assertRaises(HTTPException) as context:
                asyncio.run(analyze_text(TextInputRequest(text="Merhaba")))

        self.assertEqual(context.exception.status_code, 502)


if __name__ == "__main__":
    unittest.main()
