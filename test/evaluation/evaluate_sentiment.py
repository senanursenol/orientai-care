from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from service.sentiment import SENTIMENT_LABELS, SentimentService


FIXTURE = Path(__file__).parent / "fixtures" / "sentiment_cases.json"


def metrics(expected: list[str], predicted: list[str]) -> dict:
    confusion = {
        label: {candidate: 0 for candidate in SENTIMENT_LABELS}
        for label in SENTIMENT_LABELS
    }
    for truth, guess in zip(expected, predicted, strict=True):
        confusion[truth][guess] += 1

    per_class = {}
    for label in SENTIMENT_LABELS:
        true_positive = confusion[label][label]
        false_negative = sum(confusion[label].values()) - true_positive
        false_positive = (
            sum(confusion[other][label] for other in SENTIMENT_LABELS)
            - true_positive
        )
        precision = true_positive / max(true_positive + false_positive, 1)
        recall = true_positive / max(true_positive + false_negative, 1)
        f1 = 2 * precision * recall / max(precision + recall, 1e-12)
        per_class[label] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "support": sum(confusion[label].values()),
        }

    accuracy = sum(a == b for a, b in zip(expected, predicted, strict=True)) / len(
        expected
    )
    macro_f1 = sum(item["f1"] for item in per_class.values()) / len(per_class)
    return {
        "samples": len(expected),
        "accuracy": round(accuracy, 4),
        "macro_f1": round(macro_f1, 4),
        "per_class": per_class,
        "confusion": confusion,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-only", action="store_true")
    parser.add_argument("--fixture", type=Path, default=FIXTURE)
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--minimum-accuracy", type=float, default=0.82)
    parser.add_argument("--minimum-macro-f1", type=float, default=0.80)
    parser.add_argument("--minimum-anxious-recall", type=float, default=0.90)
    args = parser.parse_args()

    cases = json.loads(args.fixture.read_text(encoding="utf-8"))
    service = SentimentService()
    expected: list[str] = []
    predicted: list[str] = []
    failures = []
    low_confidence = Counter()

    for case in cases:
        result = service.analyze_sync(
            case["text"], include_care_calibration=not args.base_only
        )
        expected.append(case["label"])
        predicted.append(result["label"])
        low_confidence[result["label"]] += int(result["low_confidence"])
        if result["label"] != case["label"]:
            failures.append(
                {
                    "text": case["text"],
                    "expected": case["label"],
                    "predicted": result["label"],
                    "score": result["score"],
                    "signals": result["signals"],
                }
            )

    report = metrics(expected, predicted)
    report["mode"] = "base-only" if args.base_only else "hybrid"
    report["fixture"] = str(args.fixture)
    report["low_confidence_predictions"] = dict(low_confidence)
    report["failures"] = failures
    passed = (
        report["accuracy"] >= args.minimum_accuracy
        and report["macro_f1"] >= args.minimum_macro_f1
        and report["per_class"]["anxious"]["recall"]
        >= args.minimum_anxious_recall
    )
    report["passed"] = passed
    if args.summary:
        summary = {
            "fixture": report["fixture"],
            "samples": report["samples"],
            "accuracy": report["accuracy"],
            "macro_f1": report["macro_f1"],
            "anxious_recall": report["per_class"]["anxious"]["recall"],
            "failures": len(report["failures"]),
            "passed": passed,
        }
        print(json.dumps(summary, ensure_ascii=False))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
