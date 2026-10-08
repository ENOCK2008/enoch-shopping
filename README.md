# Enock Shopping Center

An international C2C + B2C marketplace foundation built with Django, PostgreSQL and Django REST Framework.

## Included now

- Responsive Enock marketplace storefront
- Product catalog, categories and search
- Individual C2C and business/B2C seller profiles
- Seller verification flag
- Customer registration, login, logout and account
- Local wishlist
- Local shopping cart
- Authenticated checkout
- Inventory validation and stock deduction
- Orders and order history
- Product reviews API
- Buyer/seller messaging API foundation
- Countries and currency-rate API foundation
- Payment model/API foundation
- Shipping zones and shipment tracking API foundation
- Render deployment configuration
- WhiteNoise production static files
- Optional demo data command

## Run locally

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

# Start PostgreSQL and configure DATABASE_URL, or use the included docker-compose.
python manage.py makemigrations users sellers catalog cart orders reviews messaging localization payments shipping
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Open http://127.0.0.1:8000/

Demo seller accounts are created by `seed_demo`; change their passwords before real use.

## API

- `/api/users/`
- `/api/sellers/`
- `/api/catalog/products/`
- `/api/catalog/categories/`
- `/api/cart/`
- `/api/orders/`
- `/api/reviews/`
- `/api/messages/`
- `/api/localization/countries/`
- `/api/localization/rates/`
- `/api/payments/`
- `/api/shipping/`

## Render

The included `render.yaml` creates the web service and PostgreSQL database. The build script creates migrations, migrates the database and collects static files.

For production, configure a real payment provider, object storage for product images/media, email/SMS/WhatsApp providers, courier integrations, domain/DNS, monitoring, backups and marketplace legal/tax rules.

## Important production note

This repository is a substantial marketplace foundation, not a claim that every external service is already live. Payment gateways, KYC/identity verification, AI providers, courier APIs, tax engines and country-specific compliance must be connected with their respective credentials and commercial/legal configuration.


## Production commerce phase added

- Seller Center dashboard endpoint: `/api/sellers/dashboard/`
- Payment initialization abstraction: `/api/payments/initialize/`
- Refund request workflow: `/api/orders/<id>/request-refund/`
- Return request API: `/api/shipping/returns/`
- Shipment tracking API
- Notification API
- International currency conversion endpoint
- Country tax-rate field
- Admin operations dashboard: `/api/admin/dashboard/`
- Expanded order pricing fields: subtotal, shipping fee, tax and total

### Real provider integrations

The application now has provider-neutral interfaces, but live money movement must be connected to licensed/approved providers and credentials. Do not treat the placeholder/manual payment provider as a production payment gateway.

Recommended integration layers:
- Payment gateway adapter
- Mobile-money adapter
- Card processor
- Courier adapter
- Email/SMS/WhatsApp notification adapter
- Currency-rate provider
- Tax/compliance provider
- Identity/KYC provider

These adapters should be configured per country and enabled only after testing, legal review and provider approval.

## Payment and DHL integrations

The production-commerce layer now includes provider adapters for:

- **MTN MoMo Uganda** collections and transaction-status checks. Configure `MTN_MOMO_*` variables. MTN's Uganda Open API provides RequestToPay/collection and transaction-status capabilities.
- **Airtel Money** collections using the Airtel Africa Developer Portal. Configure `AIRTEL_MONEY_*` variables and use the country-specific application credentials issued by Airtel.
- **International cards** through a Stripe-compatible PaymentIntent architecture. Configure `STRIPE_SECRET_KEY`; card details stay with the processor rather than Enock's database.
- **DHL Express MyDHL** shipment tracking. Configure `DHL_API_*` and `DHL_ACCOUNT_NUMBER` for an active DHL Express customer account.

New endpoints include:

- `POST /api/payments/initialize/` with `provider=card|mtn_momo|airtel_money`
- `POST /api/payments/{id}/refresh-status/`
- `POST /api/payments/webhooks/{provider}/`
- `POST /api/shipping/shipments/{id}/refresh/`

Provider credentials are deliberately excluded from source control. Live activation still requires the provider's onboarding, business/compliance approval and production credentials.
