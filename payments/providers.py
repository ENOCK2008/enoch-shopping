"""Provider adapters for Enock Shopping Center payments.

Credentials are read only from environment variables.  Adapters raise ProviderError
when credentials are missing or a provider rejects a request, allowing the API layer
to expose a safe, provider-neutral response.
"""
import base64
import json
import os
import uuid
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class ProviderError(Exception):
    pass


def _json_request(method, url, *, headers=None, payload=None, timeout=30):
    body = json.dumps(payload).encode() if payload is not None else None
    request = Request(url, data=body, method=method, headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw) if raw else {}
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(raw)
        except json.JSONDecodeError:
            detail = {"raw": raw}
        raise ProviderError(f"Provider HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise ProviderError(f"Provider connection failed: {exc.reason}") from exc


class MTNMoMoProvider:
    name = "mtn_momo"

    def __init__(self):
        self.base_url = os.getenv("MTN_MOMO_BASE_URL", "https://sandbox.momodeveloper.mtn.com").rstrip("/")
        self.subscription_key = os.getenv("MTN_MOMO_SUBSCRIPTION_KEY", "")
        self.api_user = os.getenv("MTN_MOMO_API_USER", "")
        self.api_key = os.getenv("MTN_MOMO_API_KEY", "")
        self.target_environment = os.getenv("MTN_MOMO_TARGET_ENVIRONMENT", "sandbox")
        self.currency = os.getenv("MTN_MOMO_CURRENCY", "EUR")

    def configured(self):
        return all([self.subscription_key, self.api_user, self.api_key])

    def _token(self):
        if not self.configured():
            raise ProviderError("MTN MoMo credentials are not configured.")
        raw = f"{self.api_user}:{self.api_key}".encode()
        auth = base64.b64encode(raw).decode()
        status, data = _json_request(
            "POST",
            f"{self.base_url}/collection/token/",
            headers={
                "Authorization": f"Basic {auth}",
                "Ocp-Apim-Subscription-Key": self.subscription_key,
            },
            payload={"grant_type": "client_credentials"},
        )
        token = data.get("access_token")
        if not token:
            raise ProviderError(f"MTN token response did not contain access_token: {data}")
        return token

    def collect(self, *, amount: Decimal, currency: str, phone: str, reference: str):
        token = self._token()
        transaction_id = str(uuid.uuid4())
        status, data = _json_request(
            "POST",
            f"{self.base_url}/collection/v1_0/requesttopay",
            headers={
                "Authorization": f"Bearer {token}",
                "Ocp-Apim-Subscription-Key": self.subscription_key,
                "X-Reference-Id": transaction_id,
                "X-Target-Environment": self.target_environment,
            },
            payload={
                "amount": str(amount),
                "currency": currency or self.currency,
                "externalId": reference,
                "payer": {"partyIdType": "MSISDN", "partyId": phone},
                "payerMessage": f"Enock Shopping Center payment {reference}",
                "payeeNote": f"Order payment {reference}",
            },
        )
        return {"reference": transaction_id, "provider_response": data, "http_status": status}

    def status(self, reference: str):
        token = self._token()
        status, data = _json_request(
            "GET",
            f"{self.base_url}/collection/v1_0/requesttopay/{reference}",
            headers={
                "Authorization": f"Bearer {token}",
                "Ocp-Apim-Subscription-Key": self.subscription_key,
                "X-Target-Environment": self.target_environment,
            },
        )
        return {"provider_status": data.get("status"), "provider_response": data, "http_status": status}


class AirtelMoneyProvider:
    name = "airtel_money"

    def __init__(self):
        self.base_url = os.getenv("AIRTEL_MONEY_BASE_URL", "https://openapi.airtel.africa").rstrip("/")
        self.client_id = os.getenv("AIRTEL_MONEY_CLIENT_ID", "")
        self.client_secret = os.getenv("AIRTEL_MONEY_CLIENT_SECRET", "")
        self.country = os.getenv("AIRTEL_MONEY_COUNTRY", "UG")
        self.currency = os.getenv("AIRTEL_MONEY_CURRENCY", "UGX")
        self.collection_path = os.getenv("AIRTEL_MONEY_COLLECTION_PATH", "/merchant/v1/payments/")

    def configured(self):
        return all([self.client_id, self.client_secret])

    def _token(self):
        if not self.configured():
            raise ProviderError("Airtel Money credentials are not configured.")
        status, data = _json_request(
            "POST",
            f"{self.base_url}/auth/oauth2/token",
            headers={"Authorization": "Basic " + base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()},
            payload={"client_id": self.client_id, "client_secret": self.client_secret, "grant_type": "client_credentials"},
        )
        token = data.get("access_token")
        if not token:
            raise ProviderError(f"Airtel token response did not contain access_token: {data}")
        return token

    def collect(self, *, amount: Decimal, currency: str, phone: str, reference: str):
        token = self._token()
        status, data = _json_request(
            "POST",
            f"{self.base_url}{self.collection_path}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Country": self.country,
                "X-Currency": currency or self.currency,
            },
            payload={
                "reference": reference,
                "subscriber": {"country": self.country, "currency": currency or self.currency, "msisdn": phone},
                "transaction": {"amount": float(amount), "country": self.country, "currency": currency or self.currency, "id": reference},
            },
        )
        return {"reference": reference, "provider_response": data, "http_status": status}


class CardProvider:
    """Stripe-compatible card architecture.

    The SDK is optional at runtime. When STRIPE_SECRET_KEY is set, the adapter
    creates a PaymentIntent; otherwise it reports configuration_required.
    """
    name = "card"

    def __init__(self):
        self.secret_key = os.getenv("STRIPE_SECRET_KEY", "")
        self.api_version = os.getenv("STRIPE_API_VERSION", "")

    def configured(self):
        return bool(self.secret_key)

    def create_intent(self, *, amount: Decimal, currency: str, reference: str):
        if not self.configured():
            raise ProviderError("Card processor credentials are not configured.")
        try:
            import stripe
        except ImportError as exc:
            raise ProviderError("The optional Stripe SDK is not installed.") from exc
        stripe.api_key = self.secret_key
        intent = stripe.PaymentIntent.create(
            amount=int(Decimal(amount) * 100),
            currency=currency.lower(),
            automatic_payment_methods={"enabled": True},
            metadata={"enock_reference": reference},
            idempotency_key=reference,
        )
        return {
            "reference": intent.id,
            "client_secret": intent.client_secret,
            "provider_response": intent.to_dict_recursive(),
        }


def get_payment_provider(name):
    providers = {"mtn_momo": MTNMoMoProvider, "airtel_money": AirtelMoneyProvider, "card": CardProvider}
    try:
        return providers[name]()
    except KeyError as exc:
        raise ProviderError(f"Unsupported payment provider: {name}") from exc
