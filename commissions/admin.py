from django.contrib import admin
from django.utils import timezone

from .models import Commission


@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = (
        "order_reference", "seller", "order_amount", "commission_rate",
        "commission_amount", "seller_earnings", "currency", "status", "created_at",
    )
    list_filter = ("status", "currency", "created_at")
    search_fields = ("order_reference", "seller__username", "seller__email", "buyer__username")
    readonly_fields = ("commission_amount", "seller_earnings", "created_at", "updated_at", "paid_at")
    list_select_related = ("seller", "buyer")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    actions = ("mark_approved", "mark_paid")

    @admin.action(description="Mark selected commissions as approved")
    def mark_approved(self, request, queryset):
        queryset.exclude(status=Commission.Status.CANCELLED).update(
            status=Commission.Status.APPROVED, paid_at=None
        )

    @admin.action(description="Mark selected commissions as paid to sellers")
    def mark_paid(self, request, queryset):
        queryset.exclude(status=Commission.Status.CANCELLED).update(
            status=Commission.Status.PAID, paid_at=timezone.now()
        )
