"""Create deterministic noisy/reverberant WAV variants for STT evaluation."""

from __future__ import annotations

import argparse
import wave
from io import BytesIO
from pathlib import Path

import numpy as np

from service.audio_processing import AudioProcessor


def _wav_bytes(signal: np.ndarray, sample_rate: int = 16_000) -> bytes:
    pcm = np.round(np.clip(signal, -1.0, 1.0) * 32767.0).astype("<i2")
    output = BytesIO()
    with wave.open(output, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm.tobytes())
    return output.getvalue()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--snr-db", type=float, default=10.0)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    decoder = AudioProcessor()
    rng = np.random.default_rng(20260719)

    for source in sorted(args.source_dir.iterdir()):
        if not source.is_file():
            continue
        signal = decoder._decode(source.read_bytes())
        speech_rms = float(np.sqrt(np.mean(np.square(signal, dtype=np.float64))))
        noise_rms = speech_rms / (10.0 ** (args.snr_db / 20.0))
        noise = rng.normal(0.0, noise_rms, signal.size).astype(np.float32)

        # A short room reflection approximates a phone/tablet used away from
        # the speaker without attempting to simulate a specific patient.
        delay = int(0.075 * decoder.config.sample_rate)
        reflected = np.zeros_like(signal)
        reflected[delay:] = signal[:-delay] * 0.20
        variant = signal + reflected + noise
        peak = float(np.max(np.abs(variant), initial=0.0))
        if peak > 0.96:
            variant *= 0.96 / peak

        output = args.output_dir / f"{source.stem}.wav"
        output.write_bytes(_wav_bytes(variant))


if __name__ == "__main__":
    main()
