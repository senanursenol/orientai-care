from __future__ import annotations

import asyncio
import math
import unittest
import wave
from io import BytesIO
from types import SimpleNamespace

import numpy as np

from service.audio_processing import AudioProcessingError, AudioProcessor
from service.voice_input import VoiceInputService
from service.whisper import TranscriptionResult


def wav_bytes(
    samples: np.ndarray,
    sample_rate: int = 16_000,
    channels: int = 1,
) -> bytes:
    clipped = np.clip(samples, -1.0, 1.0)
    pcm = np.round(clipped * 32767.0).astype("<i2")
    output = BytesIO()
    with wave.open(output, "wb") as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm.tobytes())
    return output.getvalue()


def read_wav(audio: bytes) -> tuple[np.ndarray, int, int]:
    with wave.open(BytesIO(audio), "rb") as wav:
        sample_rate = wav.getframerate()
        channels = wav.getnchannels()
        pcm = np.frombuffer(wav.readframes(wav.getnframes()), dtype="<i2")
    return pcm.astype(np.float32) / 32767.0, sample_rate, channels


def rms(signal: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(signal, dtype=np.float64))))


class AudioProcessorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.processor = AudioProcessor()

    def test_resamples_stereo_audio_to_mono_16khz(self) -> None:
        sample_rate = 48_000
        time = np.arange(sample_rate, dtype=np.float32) / sample_rate
        left = 0.15 * np.sin(2 * np.pi * 220 * time)
        right = 0.10 * np.sin(2 * np.pi * 330 * time)
        stereo = np.column_stack((left, right)).reshape(-1)

        result = self.processor.process(
            wav_bytes(stereo, sample_rate=sample_rate, channels=2)
        )
        output, output_rate, output_channels = read_wav(result.wav_bytes)

        self.assertEqual(output_rate, 16_000)
        self.assertEqual(output_channels, 1)
        self.assertAlmostEqual(result.duration_seconds, 1.0, places=2)
        self.assertGreater(output.size, 15_900)

    def test_quiet_speech_is_amplified_without_clipping(self) -> None:
        time = np.arange(32_000, dtype=np.float32) / 16_000
        quiet = 0.004 * np.sin(2 * np.pi * 180 * time)

        result = self.processor.process(wav_bytes(quiet))
        output, _, _ = read_wav(result.wav_bytes)

        self.assertGreater(result.applied_gain_db, 10.0)
        self.assertGreater(rms(output), rms(quiet) * 3.0)
        self.assertLessEqual(float(np.max(np.abs(output))), 0.951)

    def test_steady_noise_reduction_improves_snr(self) -> None:
        rng = np.random.default_rng(42)
        sample_rate = 16_000
        time = np.arange(sample_rate * 3, dtype=np.float32) / sample_rate
        envelope = np.zeros_like(time)
        envelope[(time >= 0.4) & (time < 1.2)] = 1.0
        envelope[(time >= 1.6) & (time < 2.6)] = 0.8
        clean = envelope * (
            0.08 * np.sin(2 * np.pi * 190 * time)
            + 0.035 * np.sin(2 * np.pi * 380 * time)
        )
        noise = rng.normal(0.0, 0.025, clean.size).astype(np.float32)
        noisy = clean + noise
        before_snr = 10.0 * math.log10(
            np.mean(clean**2) / np.mean(noise**2)
        )

        clean_output, _, _ = read_wav(
            self.processor.process(wav_bytes(clean)).wav_bytes
        )
        noisy_output, _, _ = read_wav(
            self.processor.process(wav_bytes(noisy)).wav_bytes
        )
        scale = float(
            np.dot(noisy_output, clean_output)
            / max(np.dot(clean_output, clean_output), 1e-12)
        )
        reconstructed = clean_output * scale
        residual = noisy_output - reconstructed
        after_snr = 10.0 * math.log10(
            np.mean(reconstructed**2) / max(np.mean(residual**2), 1e-12)
        )

        self.assertGreater(after_snr, before_snr + 1.0)

    def test_rejects_undecodable_audio(self) -> None:
        with self.assertRaises(AudioProcessingError):
            self.processor.process(b"not an audio recording")


class FakeWhisperService:
    def __init__(self) -> None:
        self.config = SimpleNamespace(max_audio_bytes=1024 * 1024)
        self.received_audio = b""

    async def transcribe_with_metadata(self, audio: bytes) -> TranscriptionResult:
        self.received_audio = audio
        return TranscriptionResult(
            text="Merhaba, benim adım Eralp.",
            language="tr",
            language_probability=1.0,
            duration_seconds=1.0,
        )


class FakeSentimentService:
    def __init__(self, *, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.received_text = ""

    async def analyze(self, text: str) -> dict[str, object]:
        self.received_text = text
        if self.should_fail:
            raise RuntimeError("sentiment unavailable")
        return {
            "label": "positive",
            "score": 0.91,
            "scores": {
                "anxious": 0.01,
                "negative": 0.02,
                "neutral": 0.06,
                "positive": 0.91,
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


class VoiceInputIntegrationTests(unittest.TestCase):
    def test_processed_wav_is_forwarded_to_whisper(self) -> None:
        time = np.arange(16_000, dtype=np.float32) / 16_000
        source = 0.01 * np.sin(2 * np.pi * 220 * time)
        fake_stt = FakeWhisperService()
        fake_sentiment = FakeSentimentService()
        service = VoiceInputService(
            stt=fake_stt,
            processor=AudioProcessor(),
            sentiment=fake_sentiment,
        )

        result = asyncio.run(service.prepare(wav_bytes(source)))
        _, sample_rate, channels = read_wav(fake_stt.received_audio)

        self.assertEqual(result.ai_input, "Merhaba, benim adım Eralp.")
        self.assertEqual(fake_sentiment.received_text, result.ai_input)
        self.assertEqual(result.sentiment["label"], "positive")
        self.assertEqual(sample_rate, 16_000)
        self.assertEqual(channels, 1)

    def test_sentiment_failure_preserves_transcript(self) -> None:
        time = np.arange(16_000, dtype=np.float32) / 16_000
        source = 0.01 * np.sin(2 * np.pi * 220 * time)
        service = VoiceInputService(
            stt=FakeWhisperService(),
            processor=AudioProcessor(),
            sentiment=FakeSentimentService(should_fail=True),
        )

        result = asyncio.run(service.prepare(wav_bytes(source)))

        self.assertEqual(result.ai_input, "Merhaba, benim adım Eralp.")
        self.assertEqual(result.sentiment["label"], "unknown")
        self.assertTrue(result.sentiment["low_confidence"])


if __name__ == "__main__":
    unittest.main()
