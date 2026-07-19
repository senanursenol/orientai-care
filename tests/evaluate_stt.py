"""Evaluate local Whisper configurations on a labelled Turkish audio set.

The audio files are intentionally not committed. Generate or collect consented
recordings whose filenames match ``tests/fixtures/stt_cases.json`` and place
them in the directory passed with ``--audio-dir``.
"""

from __future__ import annotations

import argparse
import json
import re
import time
import unicodedata
from dataclasses import asdict, dataclass
from io import BytesIO
from pathlib import Path

from faster_whisper import WhisperModel

from service.audio_processing import AudioProcessingConfig, AudioProcessor


def _normalized_words(text: str) -> list[str]:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    # Turkish suffix apostrophes do not represent word boundaries for WER.
    normalized = normalized.replace("'", "").replace("’", "")
    normalized = re.sub(r"[^a-z0-9çğıöşü]+", " ", normalized)
    return normalized.split()


def _edit_distance(reference: list[str], hypothesis: list[str]) -> int:
    previous = list(range(len(hypothesis) + 1))
    for reference_item in reference:
        current = [previous[0] + 1]
        for index, hypothesis_item in enumerate(hypothesis, start=1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[index] + 1,
                    previous[index - 1]
                    + (reference_item != hypothesis_item),
                )
            )
        previous = current
    return previous[-1]


@dataclass(frozen=True, slots=True)
class CaseResult:
    id: str
    reference: str
    hypothesis: str
    word_errors: int
    reference_words: int
    elapsed_seconds: float


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio-dir", type=Path, required=True)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("tests/fixtures/stt_cases.json"),
    )
    parser.add_argument("--model", default="small")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--compute-type", default="int8")
    parser.add_argument("--beam-size", type=int, default=5)
    parser.add_argument("--initial-prompt", default=None)
    parser.add_argument("--hotwords", default=None)
    parser.add_argument("--vad-filter", action="store_true")
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument(
        "--noise-reduction-strength",
        type=float,
        default=0.70,
    )
    parser.add_argument(
        "--minimum-spectral-gain",
        type=float,
        default=0.25,
    )
    return parser


def main() -> None:
    args = _parser().parse_args()
    cases = json.loads(args.manifest.read_text(encoding="utf-8"))
    processor = AudioProcessor(
        AudioProcessingConfig(
            noise_reduction_strength=args.noise_reduction_strength,
            minimum_spectral_gain=args.minimum_spectral_gain,
        )
    )
    model = WhisperModel(
        args.model,
        device=args.device,
        compute_type=args.compute_type,
        local_files_only=args.local_files_only,
    )

    results: list[CaseResult] = []
    for case in cases:
        candidates = list(args.audio_dir.glob(f"{case['id']}.*"))
        if len(candidates) != 1:
            raise SystemExit(
                f"Expected one audio file for {case['id']}, found {len(candidates)}"
            )
        audio = processor.process(candidates[0].read_bytes()).wav_bytes
        started = time.perf_counter()
        segments, _ = model.transcribe(
            BytesIO(audio),
            language="tr",
            task="transcribe",
            beam_size=args.beam_size,
            temperature=0.0,
            vad_filter=args.vad_filter,
            vad_parameters={
                "min_silence_duration_ms": 2_000,
                "speech_pad_ms": 400,
            },
            condition_on_previous_text=False,
            initial_prompt=args.initial_prompt,
            hotwords=args.hotwords,
            word_timestamps=False,
        )
        hypothesis = re.sub(
            r"\s+", " ", "".join(segment.text for segment in segments)
        ).strip()
        elapsed = time.perf_counter() - started
        reference_words = _normalized_words(case["text"])
        hypothesis_words = _normalized_words(hypothesis)
        results.append(
            CaseResult(
                id=case["id"],
                reference=case["text"],
                hypothesis=hypothesis,
                word_errors=_edit_distance(reference_words, hypothesis_words),
                reference_words=len(reference_words),
                elapsed_seconds=round(elapsed, 3),
            )
        )

    errors = sum(result.word_errors for result in results)
    words = sum(result.reference_words for result in results)
    output = {
        "model": args.model,
        "device": args.device,
        "compute_type": args.compute_type,
        "beam_size": args.beam_size,
        "vad_filter": args.vad_filter,
        "noise_reduction_strength": args.noise_reduction_strength,
        "minimum_spectral_gain": args.minimum_spectral_gain,
        "initial_prompt": args.initial_prompt,
        "hotwords": args.hotwords,
        "samples": len(results),
        "word_errors": errors,
        "reference_words": words,
        "wer": round(errors / max(words, 1), 6),
        "elapsed_seconds": round(
            sum(result.elapsed_seconds for result in results), 3
        ),
        "cases": [asdict(result) for result in results],
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
