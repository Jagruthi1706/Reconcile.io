"""Normalize Razorpay API entities without making reconciliation decisions."""

from collections.abc import Mapping, Sequence
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID, uuid5

from packages.engine.canonical import CanonicalLedgerRecord, SourceAdapter

_RAZORPAY_NAMESPACE = UUID("2f1c0d3d-3b88-4e2a-a8f5-8f4a6e2b1c90")
_PAISE_PER_RUPEE = Decimal("100")


class RazorpayAdapter(SourceAdapter):
    """Normalize payment, settlement, refund, and adjustment entities."""

    def normalize(self, payload: object) -> Sequence[CanonicalLedgerRecord]:
        if not isinstance(payload, Mapping):
            raise TypeError("Razorpay payload must be a mapping")
        if payload.get("entity") == "collection":
            items = payload.get("items")
            if not isinstance(items, list):
                raise ValueError("Razorpay collection requires an items list")
            return tuple(self._normalize_entity(item) for item in items)
        return (self._normalize_entity(payload),)

    def _normalize_entity(self, payload: object) -> CanonicalLedgerRecord:
        if not isinstance(payload, Mapping):
            raise TypeError("Razorpay entity must be a mapping")
        entity_type = _entity_type(payload)
        provider_id = _required_text(payload, "id")
        amount = _amount(payload)
        currency = _required_text(payload, "currency")
        timestamp = payload.get("created_at") if payload.get("created_at") is not None else payload.get("settled_at")
        txn_date = _timestamp_date(timestamp)
        reference = _reference(entity_type, payload, provider_id)
        description = _description(entity_type, payload, provider_id)
        return CanonicalLedgerRecord(
            id=uuid5(_RAZORPAY_NAMESPACE, f"{entity_type}:{provider_id}"),
            source="razorpay",
            amount=amount,
            currency=currency,
            txn_date=txn_date,
            external_ref=reference,
            description=description,
            entity=_optional_text(payload, "account_id"),
            raw_payload=dict(payload),
        )


def _entity_type(payload: Mapping[str, Any]) -> str:
    value = payload.get("entity")
    if value in {"payment", "settlement", "refund", "adjustment"}:
        return str(value)
    if "payment_id" in payload and "refund_status" in payload:
        return "refund"
    raise ValueError("Razorpay entity must identify payment, settlement, refund, or adjustment")


def _required_text(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"Razorpay payload requires non-empty {key}")
    return value


def _optional_text(payload: Mapping[str, Any], key: str) -> str | None:
    value = payload.get(key)
    return value if isinstance(value, str) and value else None


def _amount(payload: Mapping[str, Any]) -> Decimal:
    value = payload.get("amount")
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ValueError("Razorpay payload requires an integer smallest-unit amount")
    try:
        smallest_unit = Decimal(str(value))
    except InvalidOperation as error:
        raise ValueError("Razorpay amount must be numeric") from error
    if not smallest_unit.is_finite() or smallest_unit != smallest_unit.to_integral_value():
        raise ValueError("Razorpay amount must be an integer smallest-unit amount")
    return smallest_unit / _PAISE_PER_RUPEE


def _timestamp_date(value: object) -> date:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ValueError("Razorpay payload requires created_at or settled_at")
    try:
        timestamp = datetime.fromtimestamp(int(value), tz=UTC) if isinstance(value, int) else datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("Razorpay timestamp must be an epoch or ISO-8601 value") from error
    return timestamp.date()


def _reference(entity_type: str, payload: Mapping[str, Any], provider_id: str) -> str:
    if entity_type == "payment":
        return _optional_text(payload, "order_id") or provider_id
    if entity_type == "refund":
        return _optional_text(payload, "payment_id") or provider_id
    return _optional_text(payload, "utr") or provider_id


def _description(entity_type: str, payload: Mapping[str, Any], provider_id: str) -> str:
    return _optional_text(payload, "description")