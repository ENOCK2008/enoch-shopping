from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone


CENT = Decimal("0.01")


def money(value):
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


class Commission(models.Model):
    """A commission ledger entry for one seller and one order."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        PAID = "paid", "Paid to seller"
        CANCELLED = "cancelled", "Cancelled"

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="seller_commissions",
    )
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="buyer_commissions",
    )
    order_reference = models.CharField(max_length=100)
    currency = models.CharField(max_length=8, default="UGX")
    order_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("5.00"),
        validators=[
            MinValueValidator(Decimal("0.00")),
            MaxValueValidator(Decimal("100.00")),
        ],
        help_text="Percentage charged by the platform. For example, 5.00 means 5%.",
    )
    commission_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    seller_earnings = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["seller", "order_reference"],
                name="unique_commission_per_seller_order",
            ),
        ]
        indexes = [
            models.Index(fields=["seller", "status"]),
            models.Index(fields=["created_at"]),
        ]

    def calculate_totals(self):
        self.order_amount = money(self.order_amount)
        self.commission_amount = money(
            self.order_amount * self.commission_rate / Decimal("100")
        )
        self.seller_earnings = money(self.order_amount - self.commission_amount)

    def save(self, *args, **kwargs):
        self.calculate_totals()
        if self.status == self.Status.PAID and self.paid_at is None:
            self.paid_at = timezone.now()
        elif self.status != self.Status.PAID:
            self.paid_at = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order_reference} — {self.commission_amount} {self.currency}"
