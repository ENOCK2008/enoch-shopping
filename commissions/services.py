from decimal import Decimal

from django.db import transaction

from .models import Commission


@transaction.atomic
def create_commission(
    *, seller, order_reference, order_amount, commission_rate=Decimal("5.00"),
    buyer=None, currency="UGX", notes=""
):
    """Create one commission record per seller/order pair without duplicates.

    Call this only at the appropriate point in your order flow, commonly after
    successful payment confirmation. Adapt seller to your actual user relation.
    """
    amount = Decimal(str(order_amount))
    rate = Decimal(str(commission_rate))
    if amount <= 0:
        raise ValueError("order_amount must be greater than zero")
    if rate < 0 or rate > 100:
        raise ValueError("commission_rate must be between 0 and 100")

    return Commission.objects.get_or_create(
        seller=seller,
        order_reference=str(order_reference),
        defaults={
            "buyer": buyer,
            "currency": currency,
            "order_amount": amount,
            "commission_rate": rate,
            "notes": notes,
        },
    )
