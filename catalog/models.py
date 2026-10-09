
from decimal import Decimal

from django.core.validators import (
    MinValueValidator,
    MaxValueValidator,
)
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="children",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Product(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING = "pending", "Pending approval"
        ACTIVE = "active", "Active"
        REJECTED = "rejected", "Rejected"
        ARCHIVED = "archived", "Archived"

    name = models.CharField(max_length=220)
    slug = models.SlugField(max_length=240, unique=True)
    description = models.TextField(blank=True)

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
    )

    # NULL means the product belongs to Enock Shopping Center.
    # A seller profile means it belongs to an outside seller.
    seller = models.ForeignKey(
        "sellers.SellerProfile",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="products",
    )

    sku = models.CharField(max_length=80, unique=True)

    price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    currency = models.CharField(max_length=3, default="UGX")

    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(Decimal("0.00")),
            MaxValueValidator(Decimal("100.00")),
        ],
        help_text="Percentage charged on outside-seller sales.",
    )

    stock_quantity = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "category"]),
            models.Index(fields=["currency", "status"]),
        ]

    @property
    def is_platform_owned(self):
        return self.seller_id is None

    def commission_for_amount(self, amount):
        # Enock's own products always have zero commission.
        if self.is_platform_owned:
            return Decimal("0.00")

        amount = Decimal(str(amount))

        return (
            amount * self.commission_rate / Decimal("100")
        ).quantize(Decimal("0.01"))

    def __str__(self):
        return self.name
