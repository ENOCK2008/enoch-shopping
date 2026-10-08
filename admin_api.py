from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from catalog.models import Product
from orders.models import Order
from sellers.models import SellerProfile

@api_view(["GET"])
@permission_classes([permissions.IsAdminUser])
def dashboard(request):
    User=get_user_model()
    return Response({
        "users": User.objects.count(),
        "sellers": SellerProfile.objects.count(),
        "products": Product.objects.count(),
        "orders": Order.objects.count(),
        "order_value": str(Order.objects.aggregate(total=Sum("total"))["total"] or 0),
        "orders_by_status": list(Order.objects.values("status").annotate(count=Count("id")).order_by("status")),
    })
