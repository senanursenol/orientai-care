"""Conservative speech enhancement before Whisper transcription.

The processor is intentionally gentle: it removes frequencies outside the
speech band, attenuates steady background noise, and normalizes quiet speech
without using a hard noise gate that could discard hesitant or soft voices.
"""

from __future__ import annotations

import logging
import math
import wave
from dataclasses import dataclass
from io import BytesIO

import av
import numpy as np
from scipy.ndimage import uniform_filter1d
from scipy.signal import butter, istft, sosfilt, sosfiltfilt, stft

logger = logging.getLogger(__name__)


class AudioProcessingError(ValueError):
    """Raised when uploaded audio cannot be decoded or safely processed."""


def _dbfs(value: float) -> float:
    return 20.0 * math.log10(max(value, 1e-8))


@dataclass(frozen=True, slots=True)
class AudioProcessingConfig:
    """Settings chosen to preserve quiet and hesitant speech."""

    sample_rate: int = 16_000
    highpass_hz: float = 60.0
    lowpass_hz: float = 7_600.0
    target_rms_dbfs: float = -23.0
    max_gain_db: float = 18.0
    max_attenuation_db: float = 12.0
    peak_limit: float = 0.95
    noise_percentile: float = 20.0
    # Whisper is already noise-robust. Aggressive spectral subtraction can
    # erase quiet consonants and change words, especially in hesitant speech.
    noise_reduction_strength: float = 0.40
    minimum_spectral_gain: float = 0.55
    max_audio_seconds: int = 600


@dataclass(frozen=True, slots=True)
class ProcessedAudio:
    """Whisper-ready PCM WAV plus processing measurements."""

    wav_bytes: bytes
    duration_seconds: float
    sample_rate: int
    input_rms_dbfs: float
    output_rms_dbfs: float
    applied_gain_db: float
    peak: float


class AudioProcessor:
    """Decode, clean, and normalize browser audio for speech recognition."""

    def __init__(self, config: AudioProcessingConfig | None = None) -> None:
        self.config = config or AudioProcessingConfig()

    def _decode(self, audio: bytes) -> np.ndarray:
        chunks: list[np.ndarray] = []
        max_samples = self.config.sample_rate * self.config.max_audio_seconds
        decoded_samples = 0

        try:
            with av.open(BytesIO(audio), mode="r") as container:
                if not container.streams.audio:
                    raise AudioProcessingError("The uploaded file contains no audio")

                resampler = av.AudioResampler(
                    format="fltp",
                    layout="mono",
                    rate=self.config.sample_rate,
                )
                for frame in container.decode(audio=0):
                    for resampled in resampler.resample(frame):
                        chunk = resampled.to_ndarray().reshape(-1)
                        chunks.append(chunk.astype(np.float32, copy=False))
                        decoded_samples += chunk.size
                        if decoded_samples > max_samples:
                            raise AudioProcessingError(
                                "Audio is longer than the processing limit"
                            )

                for resampled in resampler.resample(None):
                    chunk = resampled.to_ndarray().reshape(-1)
                    chunks.append(chunk.astype(np.float32, copy=False))
                    decoded_samples += chunk.size
        except AudioProcessingError:
            raise
        except Exception as exc:
            raise AudioProcessingError("Audio could not be decoded") from exc

        if not chunks:
            raise AudioProcessingError("Audio payload contains no samples")

        signal = np.concatenate(chunks)
        if signal.size > max_samples:
            raise AudioProcessingError("Audio is longer than the processing limit")
        if not np.all(np.isfinite(signal)):
            raise AudioProcessingError("Audio contains invalid samples")
        return np.clip(signal, -1.0, 1.0)

    def _speech_band_filter(self, signal: np.ndarray) -> np.ndarray:
        sos = butter(
            4,
            [self.config.highpass_hz, self.config.lowpass_hz],
            btype="bandpass",
            fs=self.config.sample_rate,
            output="sos",
        )
        if signal.size > 128:
            return sosfiltfilt(sos, signal).astype(np.float32)
        return sosfilt(sos, signal).astype(np.float32)

    def _reduce_steady_noise(self, signal: np.ndarray) -> np.ndarray:
        frame_samples = int(self.config.sample_rate * 0.025)
        hop_samples = int(self.config.sample_rate * 0.010)
        if signal.size < frame_samples * 2:
            return signal

        _, _, spectrum = stft(
            signal,
            fs=self.config.sample_rate,
            window="hann",
            nperseg=frame_samples,
            noverlap=frame_samples - hop_samples,
            boundary="zeros",
            padded=True,
        )
        power = np.abs(spectrum) ** 2
        frame_energy = np.mean(power, axis=0)
        low_energy = float(
            np.percentile(frame_energy, self.config.noise_percentile)
        )
        high_energy = float(np.percentile(frame_energy, 80.0))

        # Without a meaningful energy contrast there is no trustworthy
        # noise-only region. Skipping denoising is safer than suppressing a
        # continuous, quiet voice as if it were background noise.
        if high_energy < max(low_energy * 2.0, 1e-12):
            return signal

        noise_frames = power[:, frame_energy <= low_energy]
        if noise_frames.shape[1] < 2:
            return signal
        noise_power = np.median(noise_frames, axis=1, keepdims=True)
        gain = 1.0 - (
            self.config.noise_reduction_strength
            * noise_power
            / np.maximum(power, 1e-12)
        )
        gain = np.clip(gain, self.config.minimum_spectral_gain, 1.0)
        gain = uniform_filter1d(gain, size=3, axis=1, mode="nearest")

        _, cleaned = istft(
            spectrum * gain,
            fs=self.config.sample_rate,
            window="hann",
            nperseg=frame_samples,
            noverlap=frame_samples - hop_samples,
            input_onesided=True,
            boundary=True,
        )
        if cleaned.size < signal.size:
            cleaned = np.pad(cleaned, (0, signal.size - cleaned.size))
        return cleaned[: signal.size].astype(np.float32)

    def _normalize(self, signal: np.ndarray) -> tuple[np.ndarray, float]:
        absolute = np.abs(signal)
        peak = float(np.max(absolute, initial=0.0))
        if peak < 1e-7:
            return signal, 0.0

        # Measure active samples instead of the whole recording so natural
        # pauses do not cause excessive amplification.
        active_floor = max(peak * 0.05, 1e-5)
        active = signal[absolute >= active_floor]
        active_rms = float(np.sqrt(np.mean(np.square(active, dtype=np.float64))))
        target_rms = 10.0 ** (self.config.target_rms_dbfs / 20.0)
        desired_gain = target_rms / max(active_rms, 1e-8)
        max_gain = 10.0 ** (self.config.max_gain_db / 20.0)
        min_gain = 10.0 ** (-self.config.max_attenuation_db / 20.0)
        peak_safe_gain = self.config.peak_limit / peak
        gain = min(max(desired_gain, min_gain), max_gain, peak_safe_gain)
        normalized = np.clip(signal * gain, -self.config.peak_limit, self.config.peak_limit)
        return normalized.astype(np.float32), 20.0 * math.log10(max(gain, 1e-8))

    def _to_wav(self, signal: np.ndarray) -> bytes:
        pcm = np.round(np.clip(signal, -1.0, 1.0) * 32767.0).astype("<i2")
        output = BytesIO()
        with wave.open(output, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(self.config.sample_rate)
            wav.writeframes(pcm.tobytes())
        return output.getvalue()

    def process(self, audio: bytes | bytearray | memoryview) -> ProcessedAudio:
        """Return a conservative, Whisper-ready version of uploaded audio."""

        if not isinstance(audio, (bytes, bytearray, memoryview)):
            raise AudioProcessingError("Audio must be provided as bytes")
        audio_bytes = bytes(audio)
        if not audio_bytes:
            raise AudioProcessingError("Audio payload is empty")

        decoded = self._decode(audio_bytes)
        input_rms = float(np.sqrt(np.mean(np.square(decoded, dtype=np.float64))))

        centered = decoded - float(np.mean(decoded))
        filtered = self._speech_band_filter(centered)
        denoised = self._reduce_steady_noise(filtered)
        normalized, gain_db = self._normalize(denoised)

        output_rms = float(
            np.sqrt(np.mean(np.square(normalized, dtype=np.float64)))
        )
        peak = float(np.max(np.abs(normalized), initial=0.0))
        duration = normalized.size / self.config.sample_rate

        logger.info(
            "Audio processed: duration=%.1fs input_rms=%.1fdBFS "
            "output_rms=%.1fdBFS gain=%.1fdB peak=%.3f",
            duration,
            _dbfs(input_rms),
            _dbfs(output_rms),
            gain_db,
            peak,
        )
        return ProcessedAudio(
            wav_bytes=self._to_wav(normalized),
            duration_seconds=duration,
            sample_rate=self.config.sample_rate,
            input_rms_dbfs=_dbfs(input_rms),
            output_rms_dbfs=_dbfs(output_rms),
            applied_gain_db=gain_db,
            peak=peak,
        )


audio_processor = AudioProcessor()


__all__ = [
    "AudioProcessingConfig",
    "AudioProcessingError",
    "AudioProcessor",
    "ProcessedAudio",
    "audio_processor",
]
