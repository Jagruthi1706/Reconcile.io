import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from uuid import UUID

import pytest

from api.integrations.razorpay import RazorpayAdapter
from packages.engine.reconciliation import MatchStatus, reconcile


FIXTURES = Path("data/fixtures/razorpay")


def load_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_payment_normalizes_amount_id_date_and_raw_payload() -> None:
    payload = load_fixture("payments.json")
    record = RazorpayAdapter().normalize(payload)[0]
    assert record.source == "razorpay"
    assert record.amount == Decimal("125.00")
    assert record.currency == "INR"
    assert record.external_ref == "order_test_001"
    assert record.txn_date == date(2024, 9, 4)
    assert record.id == UUID("fb0cf1e2-372b-5d19-bb92-0d69ac7eb9b8")
    assert record.raw_payload == payload


def test_settlement_normalizes_utr_and_refund_preserves_payment_reference() -> None:
    adapter = RazorpayAdapter()
    settlement = adapter.normalize(load_fixture("settlements.json"))[0]
    refund = adapter.normalize(load_fixture("refunds.json"))[0]
    assert settlement.external_ref == "utr_test_001"
    assert settlement.amount == Decimal("123.00")
    assert refund.external_ref == "pay_test_001"
    assert refund.amount == Decimal("2.00")


def test_collection_and_optional_fields() -> None:
    payload = {"entity": "collection", "items": [load_fixture("payments.json") | {"description": None}]}
    record = RazorpayAdapter().normalize(payload)[0]
    assert record.description is None
    assert record.entity is None


@pytest.mark.parametrize(
    "payload, message",
    [
        ({"entity": "payment", "id": "pay_1", "currency": "INR", "created_at": 1}, "amount"),
        ({"entity": "payment", "id": "pay_1", "amount": 100, "currency": "INR"}, "created_at or settled_at"),
        ({"entity": "payment", "id": "pay_1", "amount": 100.5, "currency": "INR", "created_at": 1}, "integer"),
        ({"entity": "unknown", "id": "x", "amount": 100, "currency": "INR", "created_at": 1}, "entity"),
    ],
)
def test_malformed_required_data_is_rejected(payload: dict[str, object], message: str) -> None:
    with pytest.raises((TypeError, ValueError), match=message):
        RazorpayAdapter().normalize(payload)


def test_adapter_has_no_reconciliation_decision_and_works_with_existing_matcher() -> None:
    payment = load_fixture("payments.json") | {"order_id": "order_match", "description": "Captured order"}
    settlement = load_fixture("settlements.json") | {"amount": 12500, "utr": "order_match", "description": "Cleared order"}
    left = RazorpayAdapter().normalize(payment)
    right = RazorpayAdapter().normalize(settlement)
    result = reconcile(left, right)
    assert len(result.matches) == 1
    assert result.matches[0].tier == 1
    assert result.matches[0].status == MatchStatus.AUTO_MATCHED
    assert not result.exceptions