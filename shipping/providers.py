import os
import json
import base64
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class DHLProviderError(Exception):
    pass


class DHLExpressProvider:
    """DHL Express MyDHL REST adapter for rates/shipping/tracking expansion."""
    name = "dhl_express"

    def __init__(self):
        self.base_url = os.getenv("DHL_API_BASE_URL", "https://express.api.dhl.com/mydhlapi").rstrip("/")
        self.username = os.getenv("DHL_API_USERNAME", "")
        self.password = os.getenv("DHL_API_PASSWORD", "")
        self.account_number = os.getenv("DHL_ACCOUNT_NUMBER", "")
        self.timeout = int(os.getenv("DHL_API_TIMEOUT", "30"))

    def configured(self):
        return bool(self.username and self.password and self.account_number)

    def track(self, tracking_number):
        if not self.configured():
            raise DHLProviderError("DHL MyDHL credentials/account number are not configured.")
        token = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
        query = urlencode({"trackingNumber": tracking_number, "accountNumber": self.account_number})
        request = Request(
            f"{self.base_url}/track/shipments?{query}",
            method="GET",
            headers={"Authorization": f"Basic {token}", "Accept": "application/json"},
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise DHLProviderError(f"DHL HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise DHLProviderError(f"DHL connection failed: {exc.reason}") from exc
