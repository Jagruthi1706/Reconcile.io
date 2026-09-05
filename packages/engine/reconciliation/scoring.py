import re
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
_ZERO = Decimal("0")
_ONE = Decimal("1")
_THOUSANDTH = Decimal("0.001")


def absolute_amount_variance(left: Decimal, right: Decimal) -> Decimal:
    return abs(left - right).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def within_amount_tolerance(left: Decimal, right: Decimal, tolerance_pct: Decimal) -> bool:
    baseline = abs(left)
    if baseline == _ZERO:
        return right == _ZERO
    return absolute_amount_variance(left, right) <= baseline * tolerance_pct / Decimal("100")


def date_distance(left: date, right: date) -> int:
    return abs((left - right).days)


def within_date_window(left: date, right: date, window_days: int) -> bool:
    return date_distance(left, right) <= window_days


def description_similarity(left: str | None, right: str | None) -> Decimal:
    left_tokens = set(_TOKEN_PATTERN.findall((left or "").lower()))
    right_tokens = set(_TOKEN_PATTERN.findall((right or "").lower()))
    if not left_tokens or not right_tokens:
        return _ZERO
    intersection = len(left_tokens & right_tokens)
    union = len(left_tokens | right_tokens)
    return (Decimal(intersection) / Decimal(union)).quantize(_THOUSANDTH, rounding=ROUND_HALF_UP)


def tier_two_confidence(
    left: Decimal,
    right: Decimal,
    left_date: date,
    right_date: date,
    tolerance_pct: Decimal,
    date_window_days: int,
) -> Decimal:
    amount_ratio = _ZERO
    if abs(left) != _ZERO:
        amount_ratio = absolute_amount_variance(left, right) / (abs(left) * tolerance_pct / Decimal("100"))
    date_ratio = Decimal(date_distance(left_date, right_date)) / Decimal(max(date_window_days, 1))
    confidence = Decimal("0.95") - (amount_ratio * Decimal("0.03")) - (date_ratio * Decimal("0.02"))
    return max(_ZERO, min(_ONE, confidence)).quantize(_THOUSANDTH, rounding=ROUND_HALF_UP)


def tier_three_confidence(similarity: Decimal) -> Decimal:
    return (Decimal("0.70") + (similarity * Decimal("0.20"))).quantize(_THOUSANDTH, rounding=ROUND_HALF_UP)
