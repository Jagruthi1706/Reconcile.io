import base64
import os
from http.client import RemoteDisconnected
from pathlib import Path

import pytest
from pydantic import SecretStr

from api.config import Settings
from api.integrations.razorpay import (
    RazorpayAdapter,
    RazorpayClient,
    RazorpayConfigurationError,
    RazorpayHTTPError,
    RazorpayNetworkError,
    RazorpayResponseError,
)
from packages.engine.canonical import CanonicalLedgerRecord
from packages.engine.reconciliation import reconcile


class FakeResponse:
    def __init__(self, body: bytes) -> None:
        self.body = body

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.body


def settings(**overrides: object) -> Settings:
    values: dict[str, object] = {"razorpay_key_id": "k", "razorpay_key_secret": "x"}
    values.update(overrides)
    return Settings(**values)


def test_authenticated_request_is_bounded_and_does_not_expose_secret() -> None:
    requests: list[object] = []

    def opener(request: object, **kwargs: object) -> FakeResponse:
        requests.append((request, kwargs))
        return FakeResponse(b'{"entity":"collection","items":[]}')

    response = RazorpayClient(settings(), opener=opener).list_payments(count=2)
    request, kwargs = requests[0]
    header = request.headers["Authorization"]
    assert request.full_url.endswith("/payments?count=2")
    assert header == "Basic " + base64.b64encode(b"k:x").decode("ascii")
    assert header not in str(request)
    assert kwargs == {"timeout": 10.0}
    assert response["items"] == []


def test_client_supports_bounded_entity_endpoints() -> None:
    paths: list[str] = []

    def opener(request: object, **kwargs: object) -> FakeResponse:
        paths.append(request.full_url)
        return FakeResponse(b'{"entity":"collection","items":[]}')

    client = RazorpayClient(settings(), opener=opener)
    client.list_payments(count=1)
    client.list_orders(count=1)
    client.list_settlements(count=1)
    client.list_refunds(count=1)
    client.settlement_reconciliation(count=1)
    assert [path.split("?")[0].split("/v1/")[1] for path in paths] == ["payments", "orders", "settlements", "refunds", "settlements/recon/combined"]


def test_client_creates_test_mode_order_without_exposing_credentials() -> None:
    requests: list[object] = []

    def opener(request: object, **kwargs: object) -> FakeResponse:
        requests.append(request)
        return FakeResponse(b'{"id":"order_test"}')

    response = RazorpayClient(settings(), opener=opener).create_order(amount=1000, currency="INR", receipt="receipt-1")
    assert response["id"] == "order_test"
    assert requests[0].full_url.endswith("/orders")
    assert b'"amount": 1000' in requests[0].data


@pytest.mark.parametrize("mode", ["live", "LIVE"])
def test_client_refuses_non_test_mode(mode: str) -> None:
    invalid_settings = Settings.model_construct(
        razorpay_mode=mode,
        razorpay_key_id="k",
        razorpay_key_secret=SecretStr("x"),
    )
    with pytest.raises(RazorpayConfigurationError, match="RAZORPAY_MODE"):
        RazorpayClient(invalid_settings)


def test_client_requires_credentials_and_valid_count() -> None:
    with pytest.raises(RazorpayConfigurationError, match="credentials"):
        RazorpayClient(settings(razorpay_key_id=""))
    client = RazorpayClient(settings())
    with pytest.raises(ValueError, match="between 1 and 100"):
        client.list_payments(count=101)


def test_timeout_and_network_errors_are_typed_and_redacted() -> None:
    def timeout_opener(request: object, **kwargs: object) -> FakeResponse:
        raise TimeoutError("secret should not escape")

    with pytest.raises(RazorpayNetworkError, match="could not be completed"):
        RazorpayClient(settings(), opener=timeout_opener).list_payments()

    def disconnect_opener(request: object, **kwargs: object) -> FakeResponse:
        raise RemoteDisconnected("connection closed")

    with pytest.raises(RazorpayNetworkError):
        RazorpayClient(settings(), opener=disconnect_opener).list_payments()


def test_malformed_json_response_is_typed() -> None:
    def opener(request: object, **kwargs: object) -> FakeResponse:
        return FakeResponse(b"not-json")

    with pytest.raises(RazorpayResponseError, match="non-JSON"):
        RazorpayClient(settings(), opener=opener).list_payments()


def test_real_http_error_is_typed_without_response_body() -> None:
    from urllib.error import HTTPError

    def opener(request: object, **kwargs: object) -> FakeResponse:
        raise HTTPError(request.full_url, 401, "Unauthorized", {}, None)

    with pytest.raises(RazorpayHTTPError, match="HTTP 401") as error:
        RazorpayClient(settings(), opener=opener).list_payments()
    assert "Basic" not in str(error.value)


def test_real_test_mode_boundary_is_opt_in_and_network_free_by_default() -> None:
    key_id = os.getenv("RAZORPAY_KEY_ID")
    key_secret = os.getenv("RAZORPAY_KEY_SECRET")
    if not key_id or not key_secret:
        pytest.skip("RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET are required for the live Test Mode check")
    client = RazorpayClient(Settings(razorpay_mode="test", razorpay_key_id=key_id, razorpay_key_secret=key_secret))
    payments = client.list_payments(count=1)
    records = RazorpayAdapter().normalize(payments)
    assert all(isinstance(record, CanonicalLedgerRecord) for record in records)
    assert all(record.source == "razorpay" for record in records)
    if records:
        result = reconcile(records, records)
        assert len(result.matches) <= len(records)