"""Golden-label benchmark harness for the deterministic engine."""

import json
import time
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from packages.engine.reconciliation import reconcile
from packages.engine.synthetic import generate_synthetic_dataset

@dataclass(frozen=True, slots=True)
class GoldenLabel:
    line_a_id: UUID
    line_b_id: UUID
    expected_match: bool
    notes: str | None


@dataclass(frozen=True, slots=True)
class BenchmarkMetrics:
    precision: float
    recall: float
    f1: float
    tp: int
    fp: int
    fn: int
    tn: int


@dataclass(frozen=True, slots=True)
class BenchmarkReport:
    metrics: BenchmarkMetrics
    matched_by_tier: dict[int, int]
    exceptions_by_reason: dict[str, int]


@dataclass(frozen=True, slots=True)
class ScalabilityReport:
    requested_records: int
    records_processed: int
    expected_matches: int
    actual_matches: int
    expected_exceptions: int
    actual_exceptions: int
    metrics: BenchmarkMetrics
    processing_seconds: float

    @property
    def records_per_second(self) -> float:
        if self.processing_seconds == 0:
            return float("inf")
        return self.records_processed / self.processing_seconds

    @property
    def stable_result(self) -> tuple[int, int, int, int, int, int, int, int]:
        return (
            self.requested_records, self.records_processed, self.expected_matches,
            self.actual_matches, self.expected_exceptions, self.actual_exceptions,
            self.metrics.tp, self.metrics.fp,
        )


def load_labels(path: Path) -> list[GoldenLabel]:
    labels: list[GoldenLabel] = []
    if not path.exists():
        return labels
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        labels.append(GoldenLabel(UUID(item["line_a_id"]), UUID(item["line_b_id"]), bool(item["expected_match"]), item.get("notes")))
    return labels


def calculate_metrics(expected: list[bool], predicted: list[bool]) -> BenchmarkMetrics:
    if len(expected) != len(predicted):
        raise ValueError("expected and predicted collections must have equal length")
    if not expected:
        raise ValueError("cannot calculate metrics without labels")
    tp = sum(actual and guess for actual, guess in zip(expected, predicted))
    fp = sum(not actual and guess for actual, guess in zip(expected, predicted))
    fn = sum(actual and not guess for actual, guess in zip(expected, predicted))
    tn = sum(not actual and not guess for actual, guess in zip(expected, predicted))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return BenchmarkMetrics(
        precision=precision, recall=recall, f1=f1,
        tp=int(tp), fp=int(fp), fn=int(fn), tn=int(tn),
    )


def run_benchmark(labels_path: Path) -> BenchmarkReport:
    labels = load_labels(labels_path)
    if not labels:
        raise ValueError("cannot benchmark without golden labels")
    dataset = generate_synthetic_dataset()
    result = reconcile(dataset.left_records, dataset.right_records)
    matches = {(match.left_id, match.right_id): match for match in result.matches}
    expected = [label.expected_match for label in labels]
    predicted = [(label.line_a_id, label.line_b_id) in matches for label in labels]
    return BenchmarkReport(
        metrics=calculate_metrics(expected, predicted),
        matched_by_tier=_count_tiers(result, labels),
        exceptions_by_reason=_count_reasons(result),
    )


def run_scalability_benchmark(record_count: int, seed: int = 20260904) -> ScalabilityReport:
    dataset = generate_synthetic_dataset(record_count=record_count, seed=seed)
    expected_pairs = dataset.expected_pairs
    expected = [expected_match for _, _, expected_match in expected_pairs]
    started = time.perf_counter()
    result = reconcile(dataset.left_records, dataset.right_records)
    elapsed = time.perf_counter() - started
    actual_pairs = {(match.left_id, match.right_id) for match in result.matches}
    predicted = [(left_id, right_id) in actual_pairs for left_id, right_id, _ in expected_pairs]
    return ScalabilityReport(
        requested_records=record_count,
        records_processed=len(dataset.left_payloads) + len(dataset.right_payloads),
        expected_matches=sum(expected),
        actual_matches=len(result.matches),
        expected_exceptions=len(expected) - sum(expected),
        actual_exceptions=len(result.exceptions),
        metrics=calculate_metrics(expected, predicted),
        processing_seconds=elapsed,
    )


def _count_tiers(result, labels: list[GoldenLabel]) -> dict[int, int]:
    label_pairs = {(label.line_a_id, label.line_b_id) for label in labels if label.expected_match}
    counts: dict[int, int] = {}
    for match in result.matches:
        if (match.left_id, match.right_id) in label_pairs:
            counts[match.tier] = counts.get(match.tier, 0) + 1
    return dict(sorted(counts.items()))


def _count_reasons(result) -> dict[str, int]:
    counts: dict[str, int] = {}
    for exception in result.exceptions:
        key = str(exception.reason_code)
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def main() -> None:
    import sys

    if "--scale" in sys.argv:
        for size in (50, 100, 500, 1000):
            report = run_scalability_benchmark(size)
            metrics = report.metrics
            print(
                f"records={report.requested_records} processed={report.records_processed} "
                f"expected_matches={report.expected_matches} actual_matches={report.actual_matches} "
                f"expected_exceptions={report.expected_exceptions} actual_exceptions={report.actual_exceptions} "
                f"precision={metrics.precision:.3f} recall={metrics.recall:.3f} f1={metrics.f1:.3f} "
                f"seconds={report.processing_seconds:.6f} records_per_second={report.records_per_second:.1f}"
            )
        return
    report = run_benchmark(Path("data/golden/labels.jsonl"))
    metrics = report.metrics
    print(f"precision={metrics.precision:.3f} recall={metrics.recall:.3f} f1={metrics.f1:.3f}")
    print(f"confusion_matrix=TP:{metrics.tp} FP:{metrics.fp} FN:{metrics.fn} TN:{metrics.tn}")
    print(f"matched_by_tier={report.matched_by_tier}")
    print(f"exceptions_by_reason={report.exceptions_by_reason}")


if __name__ == "__main__":
    main()
