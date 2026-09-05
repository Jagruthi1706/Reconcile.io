from pathlib import Path

from packages.engine.bench import load_labels, run_benchmark, run_scalability_benchmark
from packages.engine.reconciliation import reconcile
from packages.engine.synthetic import generate_synthetic_dataset, validate_canonical_records


def test_dataset_generation_is_deterministic_and_isolated() -> None:
    first = generate_synthetic_dataset()
    second = generate_synthetic_dataset()
    assert first == second
    assert generate_synthetic_dataset(7) != first


def test_all_source_payloads_normalize_to_valid_canonical_records() -> None:
    dataset = generate_synthetic_dataset()
    records = dataset.left_records + dataset.right_records
    validate_canonical_records(records)
    assert {record.source for record in records} == {"invoice", "razorpay_settlement", "gl", "bank"}
    assert all(record.raw_payload for record in records)


def test_synthetic_dataset_exercises_one_to_one_and_exceptions() -> None:
    dataset = generate_synthetic_dataset()
    result = reconcile(dataset.left_records, dataset.right_records)
    assert len({match.right_id for match in result.matches}) == len(result.matches)
    assert any(exception.reason_code.value == "DUPLICATE_CANDIDATE" for exception in result.exceptions)
    assert any(exception.reason_code.value == "IN_TRANSIT_NOT_CLEARED" for exception in result.exceptions)


def test_golden_labels_load_and_benchmark_repeats_identically() -> None:
    labels = load_labels(Path("data/golden/labels.jsonl"))
    assert len(labels) == 30
    assert run_benchmark(Path("data/golden/labels.jsonl")) == run_benchmark(Path("data/golden/labels.jsonl"))


def test_configurable_sizes_are_unique_and_deterministic() -> None:
    for size in (50, 100, 500, 1000):
        first = generate_synthetic_dataset(record_count=size, seed=77)
        second = generate_synthetic_dataset(record_count=size, seed=77)
        assert first == second
        assert len(first.left_payloads) >= size
        assert len({payload["id"] for payload in first.left_payloads + first.right_payloads}) == len(first.left_payloads) + len(first.right_payloads)


def test_scalability_expectations_are_independent_of_matcher_output() -> None:
    report = run_scalability_benchmark(50, seed=77)
    assert report.expected_matches == 25
    assert report.expected_exceptions == 30
    assert report.actual_matches == report.expected_matches
    assert report.metrics.f1 == 1.0

    perturbed = generate_synthetic_dataset(record_count=50, seed=77)
    payload = dict(perturbed.right_payloads[0])
    payload["amount"] = "999999.99"
    changed_right = (payload,) + perturbed.right_payloads[1:]
    changed = perturbed.__class__(perturbed.left_payloads, changed_right, perturbed.source_payloads, perturbed.seed, perturbed.expected_pairs)
    assert changed.expected_pairs == perturbed.expected_pairs
    assert changed.right_payloads[0]["amount"] != perturbed.right_payloads[0]["amount"]


def test_scalability_benchmark_repeats_with_identical_results() -> None:
    first = run_scalability_benchmark(500, seed=91)
    second = run_scalability_benchmark(500, seed=91)
    assert first.stable_result == second.stable_result