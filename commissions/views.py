from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render

from .models import Commission


@login_required
def my_commissions(request):
    """Show only commission records belonging to the signed-in seller."""
    records = Commission.objects.filter(seller=request.user)
    totals = records.aggregate(
        order_total=Sum("order_amount"),
        commission_total=Sum("commission_amount"),
        earnings_total=Sum("seller_earnings"),
    )
    return render(request, "commissions/my_commissions.html", {
        "commissions": records,
        "order_total": totals["order_total"] or 0,
        "commission_total": totals["commission_total"] or 0,
        "earnings_total": totals["earnings_total"] or 0,
    })
