from decimal import Decimal
from django.db import transaction
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Order, OrderItem
from .serializers import OrderSerializer
from catalog.models import Product

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related("items").order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["post"], url_path="checkout")
    @transaction.atomic
    def checkout(self, request):
        items = request.data.get("items") or []
        address = (request.data.get("shipping_address") or "").strip()
        country = (request.data.get("shipping_country") or "").strip()
        payment_method = (request.data.get("payment_method") or "cash_on_delivery").strip()
        notes = (request.data.get("notes") or "").strip()

        if not items:
            return Response({"detail": "Your cart is empty."}, status=400)
        if not address or not country:
            return Response({"detail": "Shipping address and country are required."}, status=400)

        currency = None
        subtotal = Decimal("0")
        prepared = []

        for raw in items:
            try:
                product_id = int(raw.get("product_id"))
                quantity = int(raw.get("quantity", 1))
            except (TypeError, ValueError):
                return Response({"detail": "Invalid cart item."}, status=400)
            if quantity < 1:
                return Response({"detail": "Quantity must be at least 1."}, status=400)

            try:
                product = Product.objects.select_for_update().select_related("seller").get(
                    pk=product_id, active=True
                )
            except Product.DoesNotExist:
                return Response({"detail": f"Product {product_id} is unavailable."}, status=400)

            if product.stock_quantity < quantity:
                return Response({"detail": f"Not enough stock for {product.name}."}, status=400)
            if currency and product.currency != currency:
                return Response({"detail": "All checkout items must use the same currency."}, status=400)

            currency = product.currency
            subtotal += product.price * quantity
            prepared.append((product, quantity))

        # Pricing engine placeholder: tax and shipping are explicit fields so
        # country/provider rules can be plugged in without changing checkout.
        shipping_fee = Decimal(str(request.data.get("shipping_fee", "0") or "0"))
        tax = Decimal(str(request.data.get("tax", "0") or "0"))
        total = subtotal + shipping_fee + tax

        order = Order.objects.create(
            user=request.user,
            currency=currency or "UGX",
            subtotal=subtotal,
            shipping_fee=shipping_fee,
            tax=tax,
            total=total,
            shipping_address=address,
            shipping_country=country,
            payment_method=payment_method,
            notes=notes,
        )

        for product, quantity in prepared:
            OrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.name,
                seller_name=product.seller.store_name,
                unit_price=product.price,
                quantity=quantity,
            )
            product.stock_quantity -= quantity
            product.save(update_fields=["stock_quantity", "updated_at"])

        return Response(OrderSerializer(order).data, status=201)

    @action(detail=True, methods=["post"], url_path="request-refund")
    def request_refund(self, request, pk=None):
        order = self.get_object()
        if order.status in [Order.Status.CANCELLED, Order.Status.REFUNDED]:
            return Response({"detail": "This order cannot be refunded."}, status=400)
        order.status = Order.Status.REFUND_REQUESTED
        order.notes = (order.notes + "\nRefund request: " + str(request.data.get("reason", ""))).strip()
        order.save(update_fields=["status", "notes", "updated_at"])
        return Response(OrderSerializer(order).data)
