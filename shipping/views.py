from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ShippingZone, Shipment, ReturnRequest
from .serializers import ShippingZoneSerializer, ShipmentSerializer, ReturnRequestSerializer
from .providers import DHLExpressProvider, DHLProviderError


class ShippingZoneViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ShippingZone.objects.filter(active=True)
    serializer_class = ShippingZoneSerializer


class ShipmentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ShipmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Shipment.objects.filter(order__user=self.request.user)

    @action(detail=True, methods=["post"], url_path="refresh")
    def refresh(self, request, pk=None):
        shipment = self.get_object()
        if shipment.carrier.lower() not in {"dhl", "dhl express", "dhl_express"}:
            return Response({"detail": "This refresh endpoint currently supports DHL Express shipments."}, status=400)
        if not shipment.tracking_number:
            return Response({"detail": "Shipment has no tracking number."}, status=400)
        try:
            result = DHLExpressProvider().track(shipment.tracking_number)
        except DHLProviderError as exc:
            return Response({"detail": str(exc)}, status=503)

        events = result.get("shipments") or []
        if events:
            latest = events[0]
            status_code = str((latest.get("status") or {}).get("statusCode") or "").lower()
            mapping = {
                "delivered": Shipment.Status.DELIVERED,
                "transit": Shipment.Status.IN_TRANSIT,
                "outfordelivery": Shipment.Status.OUT_FOR_DELIVERY,
                "pickup": Shipment.Status.PICKED_UP,
            }
            for key, value in mapping.items():
                if key in status_code:
                    shipment.status = value
                    break
            shipment.save()
        return Response({"shipment": ShipmentSerializer(shipment).data, "provider_response": result})


class ReturnRequestViewSet(viewsets.ModelViewSet):
    serializer_class = ReturnRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ReturnRequest.objects.filter(user=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
