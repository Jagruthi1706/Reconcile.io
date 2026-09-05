"""Small Razorpay Test Mode HTTP client with no financial decision logic."""

import json
import socket
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from json import JSONDecodeError
from urllib.error import HTTPError as UrllibHTTPError
from urllib.error import URLError
from urllib.request import Request, urlopen

from api.config import Settings

TEST_API_BASE_URL = "https://api.razorpay.com/v1"
_DEFAULT_TIMEOUT_SECONDS = 10.0
_MAX_COUNT = 100


class RazorpayIntegrationError(Exception):
    """Base error for safe, provider-facing integration failures."""


class RazorpayConfigurationError(RazorpayIntegrationError):
    """The client is not configured for an authenticated Test Mode request."""


class RazorpayNetworkError(RazorpayIntegrationError):
    """The provider could not be reached within the request timeout."""


class RazorpayHTTPError(RazorpayIntegrationError):
    """The provider returned a non-success HTTP response."""

    def __init__(self, status: int, reason: str) -> None:
        super().__init__(f"Razorpay Test Mode request failed with HTTP {status}: {reason}")
        self.status = status


class RazorpayResponseError(RazorpayIntegrationError):
    """The provider response was not valid JSON or had an unexpected shape."""


@dataclass(frozen=True, slots=True)
class RazorpayClient:
    settings: Settings
    timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS
    opener: Callable[..., object] = urlopen
    base_url: str = TEST_API_BASE_URL

    def __post_init__(self) -> None:
        if self.settings.razorpay_mode != "test":
            raise RazorpayConfigurationError('RAZORPAY_MODE must be "test"')
        if not self.settings.razorpay_key_id or not self.settings.razorpay_key_secret.get_secret_value():
            raise RazorpayConfigurationError("Razorpay Test Mode credentials are not configured")
        if self.timeout_seconds <= 0:
            raise RazorpayConfigurationError("Razorpay request timeout must be positive")

    def list_payments(self, *, count: int = 10) -> Mapping[str, object]:
        return self._get("/payments", count=count)

    def list_orders(self, *, count: int = 10) -> Mapping[str, object]:
        return self._get("/orders", count=count)

    def list_settlements(self, *, count: int = 10) -> Mapping[str, object]:
        return self._get("/settlements", count=count)

    def list_refunds(self, *, count: int = 10) -> Mapping[str, object]:
        return self._get("/refunds", count=count)

    def settlement_reconciliation(self, *, count: int = 10) -> Mapping[str, object]:
        return self._get("/settlements/recon/combined", count=count)

    def create_order(self, *, amount: int, currency: str, receipt: str) -> Mapping[str, object]:
        if amount <= 0 or not currency or not receipt:
            raise ValueError("amount, currency, and receipt are required")
        return self._post("/orders", {"amount": amount, "currency": currency, "receipt": receipt})

    def create_payment(self, *, order_id: str, email: str = "test@example.com", contact: str = "9999999999") -> Mapping[str, object]:
        """Create a payment for an order using test mode credentials."""
        if not order_id:
            raise ValueError("order_id is required")
        # In test mode, we simulate a payment with test card details
        return self._post("/payments/create/json", {
            "order_id": order_id,
            "email": email,
            "contact": contact,
            "amount": "0",  # Amount is from order
            "currency": "INR",
        })

    def capture_payment(self, *, payment_id: str, amount: int) -> Mapping[str, object]:
        """Capture a payment that was created but not yet captured."""
        if not payment_id or amount <= 0:
            raise ValueError("payment_id and positive amount are required")
        return self._post(f"/payments/{payment_id}/capture", {"amount": amount})

    def _get(self, path: str, *, count: int) -> Mapping[str, object]:
        if not 1 <= count <= _MAX_COUNT:
            raise ValueError(f"count must be between 1 and {_MAX_COUNT}")
        request = Request(
            f"{self.base_url.rstrip('/')}{path}?count={count}",
            headers={"Authorization": self._authorization_header(), "Accept": "application/json"},
            method="GET",
        )
        try:
            with self.opener(request, timeout=self.timeout_seconds) as response:
                body = response.read()
        except UrllibHTTPError as error:
            raise RazorpayHTTPError(error.code, "provider rejected the request") from error
        except (URLError, TimeoutError, socket.timeout, OSError) as error:
            raise RazorpayNetworkError("Razorpay Test Mode request could not be completed") from error
        try:
            decoded = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, JSONDecodeError) as error:
            raise RazorpayResponseError("Razorpay returned a non-JSON response") from error
        if not isinstance(decoded, dict):
            raise RazorpayResponseError("Razorpay response must be a JSON object")
        return decoded

    def _post(self, path: str, payload: Mapping[str, object]) -> Mapping[str, object]:
        request = Request(
            f"{self.base_url.rstrip('/')}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": self._authorization_header(), "Accept": "application/json", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with self.opener(request, timeout=self.timeout_seconds) as response:
                body = response.read()
        except UrllibHTTPError as error:
            raise RazorpayHTTPError(error.code, "provider rejected the request") from error
        except (URLError, TimeoutError, socket.timeout, OSError) as error:
            raise RazorpayNetworkError("Razorpay Test Mode request could not be completed") from error
        try:
            decoded = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, JSONDecodeError) as error:
            raise RazorpayResponseError("Razorpay returned a non-JSON response") from error
        if not isinstance(decoded, dict):
            raise RazorpayResponseError("Razorpay response must be a JSON object")
        return decoded

    def _authorization_header(self) -> str:
        import base64

        credentials = f"{self.settings.razorpay_key_id}:{self.settings.razorpay_key_secret.get_secret_value()}".encode("utf-8")
        return f"Basic {base64.b64encode(credentials).decode('ascii')}"