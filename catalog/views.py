from rest_framework import viewsets
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer
from .permissions import CatalogWritePermission, CategoryWritePermission

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by("name")
    serializer_class = CategorySerializer
    permission_classes = [CategoryWritePermission]

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("seller", "category").filter(active=True)
    serializer_class = ProductSerializer
    permission_classes = [CatalogWritePermission]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "description", "sku", "seller__store_name", "category__name"]
    ordering_fields = ["price", "created_at", "name", "stock_quantity"]
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_staff and self.request.query_params.get("include_inactive") == "1":
            qs = Product.objects.select_related("seller", "category").all()
        seller = self.request.query_params.get("seller")
        category = self.request.query_params.get("category")
        min_price = self.request.query_params.get("min_price")
        max_price = self.request.query_params.get("max_price")
        if seller:
            qs = qs.filter(seller_id=seller)
        if category:
            qs = qs.filter(category_id=category)
        if min_price:
            qs = qs.filter(price__gte=min_price)
        if max_price:
            qs = qs.filter(price__lte=max_price)
        return qs

    def perform_create(self, serializer):
        if self.request.user.is_staff and not hasattr(self.request.user, "seller_profile"):
            # Staff can create on behalf of an explicitly supplied seller.
            serializer.save()
        else:
            try:
                seller = self.request.user.seller_profile
            except Exception:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("Create a seller profile before listing products.")
            serializer.save(seller=seller)
