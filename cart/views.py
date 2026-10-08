from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Cart, CartItem
from .serializers import CartSerializer
from catalog.models import Product

class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user).prefetch_related("items__product")

    def _cart(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return cart

    def list(self, request, *args, **kwargs):
        cart = self._cart()
        return Response(self.get_serializer(cart).data)

    def create(self, request, *args, **kwargs):
        cart = self._cart()
        return Response(self.get_serializer(cart).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="add")
    def add(self, request):
        cart = self._cart()
        product = get_object_or_404(Product, pk=request.data.get("product_id"), active=True)
        quantity = int(request.data.get("quantity", 1))
        if quantity < 1 or quantity > product.stock_quantity:
            return Response({"detail": "Invalid quantity or insufficient stock."}, status=400)
        item, _ = CartItem.objects.get_or_create(cart=cart, product=product)
        item.quantity = min(item.quantity + quantity, product.stock_quantity)
        item.save(update_fields=["quantity"])
        return Response(self.get_serializer(cart).data)

    @action(detail=False, methods=["patch"], url_path="items/(?P<item_id>[^/.]+)")
    def update_item(self, request, item_id=None):
        cart = self._cart()
        item = get_object_or_404(CartItem, pk=item_id, cart=cart)
        quantity = int(request.data.get("quantity", 1))
        if quantity <= 0:
            item.delete()
        else:
            if quantity > item.product.stock_quantity:
                return Response({"detail": "Insufficient stock."}, status=400)
            item.quantity = quantity
            item.save(update_fields=["quantity"])
        return Response(self.get_serializer(cart).data)

    @action(detail=False, methods=["delete"], url_path="items/(?P<item_id>[^/.]+)")
    def remove_item(self, request, item_id=None):
        cart = self._cart()
        item = get_object_or_404(CartItem, pk=item_id, cart=cart)
        item.delete()
        return Response(self.get_serializer(cart).data)
