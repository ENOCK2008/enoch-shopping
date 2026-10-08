from django.db.models import Count, Sum
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import SellerProfile
from .serializers import SellerProfileSerializer
from .permissions import SellerOwnerOrReadOnly
from catalog.models import Product
from orders.models import OrderItem, Order

class SellerProfileViewSet(viewsets.ModelViewSet):
    queryset = SellerProfile.objects.select_related("user").all().order_by("-created_at")
    serializer_class = SellerProfileSerializer
    permission_classes = [SellerOwnerOrReadOnly]

    def perform_create(self, serializer):
        if hasattr(self.request.user, "seller_profile"):
            raise permissions.PermissionDenied("You already have a seller profile.")
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["get"], url_path="dashboard")
    def dashboard(self, request):
        if not request.user.is_authenticated:
            return Response({"detail":"Authentication required."}, status=401)
        try:
            seller = request.user.seller_profile
        except Exception:
            return Response({"detail":"Create a seller profile first."}, status=400)

        products = Product.objects.filter(seller=seller)
        item_qs = OrderItem.objects.filter(product__seller=seller)
        order_ids = item_qs.values_list("order_id", flat=True).distinct()
        orders = Order.objects.filter(id__in=order_ids)

        revenue = item_qs.aggregate(total=Sum("unit_price"))["total"] or 0
        return Response({
            "seller": SellerProfileSerializer(seller).data,
            "metrics": {
                "products": products.count(),
                "stock_units": products.aggregate(total=Sum("stock_quantity"))["total"] or 0,
                "orders": orders.count(),
                "revenue_snapshot": str(revenue),
            },
            "products": list(products.values("id","name","price","currency","stock_quantity","active")[:50]),
        })
