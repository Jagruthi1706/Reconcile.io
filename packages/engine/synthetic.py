"""Deterministic synthetic source payloads and canonical normalization."""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from random import Random
from typing import Mapping, Sequence
from uuid import UUID, uuid5

from packages.engine.canonical import CanonicalLedgerRecord, SourceAdapter

SYNTHETIC_SEED = 20260904


@dataclass(frozen=True, slots=True)
class SyntheticDataset:
    left_payloads: tuple[Mapping[str, object], ...]
    right_payloads: tuple[Mapping[str, object], ...]
    source_payloads: tuple[Mapping[str, object], ...]
    seed: int
    expected_pairs: tuple[tuple[UUID, UUID, bool], ...] = ()

    @property
    def left_records(self) -> tuple[CanonicalLedgerRecord, ...]:
        return normalize_payloads(self.left_payloads)

    @property
    def right_records(self) -> tuple[CanonicalLedgerRecord, ...]:
        return normalize_payloads(self.right_payloads)


class SyntheticAdapter(SourceAdapter):
    """Normalize synthetic source payloads through the same adapter boundary."""

    def normalize(self, payload: object) -> Sequence[CanonicalLedgerRecord]:
        if not isinstance(payload, Mapping):
            raise TypeError("synthetic payload must be a mapping")
        return normalize_payloads((payload,))


def _payload(record_id: int, source: str, amount: str, day: int, reference: str | None, description: str, rng: Random, currency: str = "USD") -> Mapping[str, object]:
    key = {"invoice": "invoice_number", "razorpay_settlement": "payout_id", "gl": "document_reference", "bank": "bank_reference"}[source]
    result: dict[str, object] = {
        "id": str(UUID(int=record_id)), "source": source, "amount": amount,
        "currency": currency, "date": f"2026-01-{day:02d}",
        "description": description, "synthetic_nonce": rng.randrange(1, 1_000_000),
    }
    result[key] = reference
    return result


def _legacy_synthetic_dataset(seed: int = SYNTHETIC_SEED) -> SyntheticDataset:
    """Generate source-shaped records with an explicit, isolated RNG."""
    rng = Random(seed)
    left: list[Mapping[str, object]] = []
    right: list[Mapping[str, object]] = []

    def pair(number: int, source: str, other_source: str, amount: str, other_amount: str, day: int, other_day: int, reference: str | None, other_reference: str | None, description: str, other_description: str, other_currency: str = "USD") -> None:
        left.append(_payload(1000 + number, source, amount, day, reference, description, rng))
        right.append(_payload(2000 + number, other_source, other_amount, other_day, other_reference, other_description, rng, other_currency))

    pair(1, "invoice", "bank", "100.00", "100.00", 1, 1, "INV-001", "INV-001", "Invoice INV-001", "Bank receipt INV-001")
    pair(2, "razorpay_settlement", "bank", "250.00", "250.00", 2, 2, "PAY-002", "PAY-002", "Payout PAY-002", "Settlement PAY-002")
    pair(3, "gl", "bank", "375.50", "375.50", 3, 3, "GL-003", "GL-003", "Cash GL-003", "Bank GL-003")
    pair(4, "gl", "bank", "80.00", "80.00", 4, 4, "OPEX-004", "OPEX-004", "Office rent OPEX-004", "Bank OPEX-004")
    pair(5, "bank", "gl", "120.00", "120.00", 5, 5, None, "GL-005", "Acme invoice settlement", "Acme invoice settlement")
    pair(6, "razorpay_settlement", "bank", "500.00", "492.50", 6, 10, "PAY-006", "PAY-006", "Payout PAY-006", "Payout PAY-006 less fee")
    pair(7, "invoice", "bank", "1000.00", "1010.00", 7, 8, "INV-007", "INV-007", "Invoice INV-007", "Invoice INV-007")
    pair(8, "bank", "gl", "42.00", "42.00", 8, 9, None, "OPEX-008", "Cloud subscription Acme", "Cloud subscription Acme")
    pair(9, "invoice", "bank", "90.00", "90.00", 9, 9, "INV-009", "INV-009", "Invoice INV-009", "Invoice INV-009", "EUR")
    pair(10, "invoice", "bank", "110.00", "110.00", 10, 10, "INV-MISSING", "INV-010", "Invoice INV-MISSING", "Invoice INV-010")
    pair(11, "invoice", "bank", "130.00", "130.01", 11, 20, "INV-011", "INV-011", "Invoice INV-011", "Invoice INV-011")
    pair(12, "invoice", "bank", "140.00", "150.00", 12, 12, "INV-012", "INV-012", "Invoice INV-012", "Invoice INV-012")
    pair(13, "gl", "bank", "160.00", "160.00", 13, 13, "GL-013", "BANK-013", "Payment in transit GL-013", "Bank clearing item BANK-013")
    pair(14, "bank", "gl", "12.00", "500.00", 14, 14, "FEE-014", "OPEX-014", "Processor fee FEE-014", "Office cost OPEX-014")
    pair(15, "bank", "gl", "8.00", "500.00", 15, 15, "INT-015", "OPEX-015", "Bank interest INT-015", "Office cost OPEX-015")
    pair(16, "bank", "gl", "33.00", "500.00", 16, 16, "CB-016", "OPEX-016", "Chargeback CB-016", "Office cost OPEX-016")
    pair(17, "invoice", "bank", "170.00", "170.00", 17, 17, "DUP-017", "DUP-017", "Invoice DUP-017", "Invoice DUP-017")
    right.append(_payload(2099, "bank", "170.00", 17, "DUP-017", "Invoice DUP-017", rng))
    pair(18, "invoice", "bank", "180.00", "180.00", 18, 18, "ONE-018", "ONE-018", "Invoice ONE-018", "Invoice ONE-018")
    left.append(_payload(1098, "invoice", "180.00", 18, "ONE-018", "Invoice ONE-018", rng))
    pair(19, "invoice", "bank", "190.00", "190.00", 19, 19, "EXACT-019", "EXACT-019", "Invoice EXACT-019", "Invoice EXACT-019")
    pair(20, "razorpay_settlement", "bank", "205.00", "205.00", 20, 21, "PAY-020", "PAY-020", "Payout PAY-020", "Payout PAY-020")
    pair(21, "gl", "bank", "215.00", "215.00", 21, 21, "GL-021", "GL-021", "GL cash GL-021", "Bank GL-021")
    pair(22, "gl", "bank", "225.00", "225.00", 22, 22, "OPEX-022", "OPEX-022", "Travel OPEX-022", "Bank OPEX-022")
    pair(23, "invoice", "bank", "235.00", "235.00", 23, 23, "INV-023", "INV-023", "Invoice INV-023", "Invoice INV-023")
    pair(24, "bank", "gl", "245.00", "245.00", 24, 24, None, "GL-024", "Marketing services Acme", "Marketing services Acme")
    pair(25, "invoice", "bank", "255.00", "255.00", 25, 25, "INV-025", "INV-025", "Invoice INV-025", "Invoice INV-025")
    pair(26, "razorpay_settlement", "bank", "265.00", "261.50", 26, 27, "PAY-026", "PAY-026", "Payout PAY-026", "Payout PAY-026")
    pair(27, "invoice", "bank", "275.00", "275.00", 27, 27, "INV-027", "INV-027", "Invoice INV-027", "Invoice INV-027")
    pair(28, "gl", "bank", "285.00", "285.00", 28, 28, "GL-028", "GL-028", "GL cash GL-028", "Bank GL-028")
    pair(29, "bank", "gl", "295.00", "295.00", 29, 29, None, "GL-029", "Software tools Acme", "Software tools Acme")
    pair(30, "invoice", "bank", "305.00", "305.00", 30, 30, "INV-030", "INV-030", "Invoice INV-030", "Invoice INV-030")
    return SyntheticDataset(tuple(left), tuple(right), tuple(left + right), seed)


_SCALABLE_NAMESPACE = UUID("c4a9cb7f-3c6d-4a9d-b2a7-50a09ecab9c0")


def generate_synthetic_dataset(
    record_count: int | None = None,
    seed: int = SYNTHETIC_SEED,
) -> SyntheticDataset:
    """Generate the legacy fixture or a larger varied reconciliation workload.

    ``None`` retains the authored 30-case benchmark fixture. For a configured
    count, the generated expectations are authored from the scenario type, not
    inferred from the matcher output.
    """
    if record_count is None:
        return _legacy_synthetic_dataset(seed)
    if record_count < 1:
        raise ValueError("record_count must be positive")

    rng = Random(seed)
    left: list[Mapping[str, object]] = []
    right: list[Mapping[str, object]] = []
    expected_pairs: list[tuple[UUID, UUID, bool]] = []
    scenario_names = ("exact", "tolerant", "description", "unmatched", "amount", "date", "currency", "duplicate", "one_to_one", "review")

    for index in range(record_count):
        scenario = index % len(scenario_names)
        day = 1 + (index % 27)
        reference = f"BATCH-{seed}-{index:05d}"
        left_id = uuid5(_SCALABLE_NAMESPACE, f"{seed}:left:{index}")
        right_id = uuid5(_SCALABLE_NAMESPACE, f"{seed}:right:{index}")
        amount = Decimal("75.00") + Decimal(index) + Decimal(index % 100) / Decimal("100")
        description = f"Merchant settlement batch {index:05d}"
        left_source = ("invoice", "razorpay_settlement", "gl", "invoice", "invoice", "gl", "invoice", "invoice", "invoice", "bank")[scenario]
        right_source = "bank" if scenario != 9 else "gl"
        left_ref: str | None = reference
        right_ref: str | None = reference
        right_amount = amount
        right_day = day
        right_currency = "USD"
        right_description = description
        expected = scenario in {0, 1, 2, 9}

        if scenario == 2:
            left_ref = None
            right_ref = f"OTHER-{index:05d}"
        elif scenario == 3:
            right_ref = f"STALE-{index:05d}"
            right_amount = amount + Decimal("17.00")
        elif scenario == 4:
            right_amount = amount * Decimal("1.05")
        elif scenario == 5:
            right_day = day + 10
            right_amount = amount * Decimal("1.005")
        elif scenario == 6:
            right_currency = "EUR"
        elif scenario == 7:
            right_ref = reference
            right_amount = amount
        elif scenario == 8:
            left_ref = reference
            right_ref = reference
            expected = True
        elif scenario == 9:
            left_ref = None
            right_ref = f"REVIEW-{index:05d}"

        left_payload = _generated_payload(left_id, left_source, amount, day, left_ref, description, rng)
        right_payload = _generated_payload(right_id, right_source, right_amount, right_day, right_ref, right_description, rng, right_currency)
        left.append(left_payload)
        right.append(right_payload)
        expected_pairs.append((left_id, right_id, expected))

        if scenario == 7:
            duplicate_id = uuid5(_SCALABLE_NAMESPACE, f"{seed}:duplicate:{index}")
            right.append(_generated_payload(duplicate_id, right_source, amount, day, reference, description, rng))
            expected_pairs[-1] = (left_id, right_id, False)

        if scenario == 8:
            second_left_id = uuid5(_SCALABLE_NAMESPACE, f"{seed}:one-to-one-left:{index}")
            left.append(_generated_payload(second_left_id, left_source, amount, day, reference, description, rng))
            expected_pairs.append((second_left_id, right_id, False))

    provider_only_id = uuid5(_SCALABLE_NAMESPACE, f"{seed}:provider-only")
    right.append(_generated_payload(provider_only_id, "razorpay_settlement", Decimal("9999.99"), 1, f"PROVIDER-ONLY-{seed}", "Provider-only settlement", rng))

    return SyntheticDataset(tuple(left), tuple(right), tuple(left + right), seed, tuple(expected_pairs))


def _generated_payload(
    record_id: UUID,
    source: str,
    amount: Decimal,
    day: int,
    reference: str | None,
    description: str,
    rng: Random,
    currency: str = "USD",
) -> Mapping[str, object]:
    key = {"invoice": "invoice_number", "razorpay_settlement": "payout_id", "gl": "document_reference", "bank": "bank_reference"}[source]
    return {
        "id": str(record_id), "source": source, "amount": str(amount.quantize(Decimal("0.01"))),
        "currency": currency, "date": (date(2026, 1, 1) + timedelta(days=day - 1)).isoformat(),
        "description": description, key: reference, "synthetic_nonce": rng.randrange(1, 1_000_000),
    }


def normalize_payloads(payloads: Sequence[Mapping[str, object]]) -> tuple[CanonicalLedgerRecord, ...]:
    return tuple(_normalize_payload(payload) for payload in payloads)


def _normalize_payload(payload: Mapping[str, object]) -> CanonicalLedgerRecord:
    source = str(payload["source"])
    key = {"invoice": "invoice_number", "razorpay_settlement": "payout_id", "gl": "document_reference", "bank": "bank_reference"}[source]
    reference = payload.get(key)
    return CanonicalLedgerRecord(
        id=UUID(str(payload["id"])), source=source, amount=Decimal(str(payload["amount"])),
        currency=str(payload["currency"]), txn_date=date.fromisoformat(str(payload["date"])),
        external_ref=str(reference) if reference is not None else None,
        description=str(payload["description"]), raw_payload=dict(payload),
    )


def validate_canonical_records(records: Sequence[CanonicalLedgerRecord]) -> None:
    for record in records:
        if not record.currency or not record.amount.is_finite():
            raise ValueError("canonical records require a finite amount and currency")