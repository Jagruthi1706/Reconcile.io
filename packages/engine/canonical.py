"""Source-neutral financial records consumed by deterministic engines.

Adapters normalize external or synthetic payloads into this contract before any
matching, tax, forecast, or accuracy logic runs. The engine never receives raw
provider-specific payloads as decision input.
"""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Mapping, Protocol, Sequence
from uuid import UUID


@dataclass(frozen=True, slots=True)
class CanonicalLedgerRecord:
    """Normalized representation of one persisted ``ledger_lines`` record."""

    id: UUID
    source: str
    amount: Decimal
    currency: str
    txn_date: date
    external_ref: str | None = None
    description: str | None = None
    entity: str | None = None
    raw_payload: Mapping[str, object] | None = None
    created_at: datetime | None = None


class SourceAdapter(Protocol):
    """Boundary implemented by synthetic and future external-source adapters."""

    def normalize(self, payload: object) -> Sequence[CanonicalLedgerRecord]:
        """Convert source payloads into canonical records without making decisions."""
        ...
