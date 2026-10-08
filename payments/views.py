from django.db import transaction
from django.utils.crypto import get_random_string
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response

from orders.models import Order
from .models import Payment
from .providers import ProviderError, get_payment_provider
from .serializers import PaymentSerializer


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user).order_by("-created_at")

    @action(detail=False, methods=["post"], url_path="initialize")
    @transaction.atomic
    def initialize(self, request):
        order_id = request.data.get("order_id")
        provider_name = (request.data.get("provider") or "card").strip().lower()
        phone = (request.data.get("phone") or request.user.phone or "").strip()
        try:
            order = Order.objects.get(pk=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({"detail": "Order not found."}, status=404)

        payment, _ = Payment.objects.get_or_create(
            order=order,
            defaults={
                "user": request.user,
                "provider": provider_name,
                "amount": order.total,
                "currency": order.currency,
                "customer_phone": phone,
                "status": Payment.Status.CREATED,
                "reference": f"ENOCK-{order.id}-{get_random_string(10).upper()}",
            },
        )
        if payment.status == Payment.Status.SUCCEEDED:
            return Response(PaymentSerializer(payment).data)

        payment.provider = provider_name
        payment.customer_phone = phone
        payment.save(update_fields=["provider", "customer_phone", "updated_at"])
        try:
            provider = get_payment_provider(provider_name)
            if provider_name == "mtn_momo":
                result = provider.collect(amount=order.total, currency=order.currency, phone=phone, reference=payment.reference)
                payment.reference = result["reference"]
                payment.metadata = result
            elif provider_name == "airtel_money":
                result = provider.collect(amount=order.total, currency=order.currency, phone=phone, reference=payment.reference)
                payment.metadata = result
            elif provider_name == "card":
                result = provider.create_intent(amount=order.total, currency=order.currency, reference=payment.reference)
                payment.reference = result["reference"]
                payment.metadata = result
            else:
                return Response({"detail": "Unsupported payment provider."}, status=400)
            payment.status = Payment.Status.PENDING
            payment.save()
            return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)
        except ProviderError as exc:
            return Response({
                "payment": PaymentSerializer(payment).data,
                "integration_status": "configuration_required",
                "detail": str(exc),
            }, status=503)

    @action(detail=True, methods=["post"], url_path="refresh-status")
    def refresh_status(self, request, pk=None):
        payment = self.get_object()
        if payment.provider not in {"mtn_momo"} or not payment.reference:
            return Response({"payment": PaymentSerializer(payment).data, "detail": "Provider status refresh is not configured for this provider."})
        try:
            result = get_payment_provider(payment.provider).status(payment.reference)
            provider_status = (result.get("provider_status") or "").upper()
            if provider_status == "SUCCESSFUL":
                payment.status = Payment.Status.SUCCEEDED
            elif provider_status in {"FAILED", "REJECTED"}:
                payment.status = Payment.Status.FAILED
            payment.metadata = result
            payment.save()
            return Response(PaymentSerializer(payment).data)
        except ProviderError as exc:
            return Response({"detail": str(exc)}, status=503)


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def provider_webhook(request, provider):
    """Generic webhook receiver. Provider-specific signature verification can be enabled via gateway adapters."""
    if provider not in {"mtn_momo", "airtel_money", "stripe", "card"}:
        return Response({"detail": "Unsupported provider."}, status=404)
    reference = request.data.get("reference") or request.data.get("externalId") or request.data.get("id")
    if not reference:
        return Response({"received": True, "detail": "No payment reference supplied."})
    payment = Payment.objects.filter(reference=reference).first()
    if not payment:
        return Response({"received": True, "detail": "Payment not found."})
    event_status = str(request.data.get("status") or request.data.get("payment_status") or "").lower()
    if event_status in {"success", "successful", "succeeded", "paid"}:
        payment.status = Payment.Status.SUCCEEDED
    elif event_status in {"failed", "rejected", "cancelled", "canceled"}:
        payment.status = Payment.Status.FAILED
    payment.metadata = {"webhook": request.data}
    payment.save()
    return Response({"received": True})
