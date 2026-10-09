from django.conf import settings
from django.db import models
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator
class SellerProfile(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending verification"
        VERIFIED = "verified", "Verified"
        SUSPENDED = "suspended", "Suspended"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="seller_profile",
    )
    store_name = models.CharField(max_length=180, unique=True)
    store_slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    country_code = models.CharField(max_length=2, default="UG")
    default_currency = models.CharField(max_length=3, default="UGX")

    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.PENDING,
    )

    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("5.00"),
        validators=[
            MinValueValidator(Decimal("0.00")),
            MaxValueValidator(Decimal("100.00")),
        ],
        help_text="Commission percentage for this seller.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.store_name


class SellerPayout(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    seller = models.ForeignKey(
        SellerProfile,
        on_delete=models.PROTECT,
        related_name="payouts",
    )
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    currency = models.CharField(max_length=3, default="UGX")
    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.PENDING,
    )
    provider_reference = models.CharField(max_length=180, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.seller.store_name} — "
            f"{self.amount} {self.currency}"
        )
class SellerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="seller_profile")
    store_name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    verified = models.BooleanField(default=False)
    phone = models.CharField(max_length=30, blank=True)
    country = models.CharField(max_length=80, default="Uganda")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.store_name
