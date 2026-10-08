from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import ShippingZone, Shipment, ShipmentLocation, ShipmentEvent, ReturnRequest
from .serializers import ShippingZoneSerializer, ShipmentSerializer, ShipmentLocationSerializer, ShipmentEventSerializer, ReturnRequestSerializer


class ShippingZoneViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ShippingZone.objects.filter(active=True)
    serializer_class = ShippingZoneSerializer


class ShipmentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ShipmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Shipment.objects.all().prefetch_related("locations", "events")
        return Shipment.objects.filter(order__user=user).prefetch_related("locations", "events")

    @action(detail=True, methods=["get"], url_path="track")
    def track(self, request, pk=None):
        shipment = self.get_object()
        if shipment.order.user != request.user and not request.user.is_staff:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        latest_location = shipment.locations.first()
        return Response(
            {
                "tracking_number": shipment.tracking_number,
                "status": shipment.status,
                "status_display": shipment.get_status_display(),
                "carrier": shipment.carrier,
                "estimated_delivery": shipment.estimated_delivery,
                "current_latitude": shipment.current_latitude,
                "current_longitude": shipment.current_longitude,
                "last_location_update": shipment.last_location_update,
                "address": latest_location.address if latest_location else shipment.destination_address,
                "events": ShipmentEventSerializer(shipment.events.all()[:10], many=True).data,
                "locations": ShipmentLocationSerializer(shipment.locations.all()[:20], many=True).data,
            }
        )

    @action(detail=True, methods=["post"], url_path="update-location")
    def update_location(self, request, pk=None):
        shipment = self.get_object()
        if not request.user.is_staff:
            return Response({"detail": "Only admins can update shipment locations."}, status=status.HTTP_403_FORBIDDEN)

        latitude = request.data.get("latitude")
        longitude = request.data.get("longitude")
        status_value = request.data.get("status", shipment.status)
        status_note = request.data.get("status_note", "")
        address = request.data.get("address", "")

        if latitude is None or longitude is None:
            return Response({"detail": "latitude and longitude are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except (TypeError, ValueError):
            return Response({"detail": "Latitude and longitude must be valid numbers."}, status=status.HTTP_400_BAD_REQUEST)

        location = ShipmentLocation.objects.create(
            shipment=shipment,
            latitude=latitude,
            longitude=longitude,
            accuracy=request.data.get("accuracy"),
            address=address,
            status=status_value,
            status_note=status_note,
        )

        shipment.status = status_value
        shipment.current_latitude = latitude
        shipment.current_longitude = longitude
        shipment.last_location_update = location.timestamp
        shipment.save(update_fields=["status", "current_latitude", "current_longitude", "last_location_update", "updated_at"])

        event_type = ShipmentEvent.EventType.CREATED
        if status_value == Shipment.Status.PICKED_UP:
            event_type = ShipmentEvent.EventType.PICKED_UP
        elif status_value == Shipment.Status.IN_TRANSIT:
            event_type = ShipmentEvent.EventType.DEPARTURE
        elif status_value == Shipment.Status.OUT_FOR_DELIVERY:
            event_type = ShipmentEvent.EventType.OUT_FOR_DELIVERY
        elif status_value == Shipment.Status.DELIVERED:
            event_type = ShipmentEvent.EventType.DELIVERED

        ShipmentEvent.objects.create(
            shipment=shipment,
            event_type=event_type,
            title=f"Shipment status updated to {shipment.get_status_display()}",
            description=status_note or "Location updated by the delivery team.",
            location=address,
            latitude=latitude,
            longitude=longitude,
        )

        return Response({"shipment": ShipmentSerializer(shipment).data, "location": ShipmentLocationSerializer(location).data})


class ReturnRequestViewSet(viewsets.ModelViewSet):
    serializer_class = ReturnRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ReturnRequest.objects.filter(user=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PublicTrackingViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=["get"], url_path=r"track/(?P<tracking_number>[^/.]+)")
    def track(self, request, tracking_number=None):
        try:
            shipment = Shipment.objects.get(tracking_number=tracking_number)
        except Shipment.DoesNotExist:
            return Response({"detail": "Tracking number not found."}, status=status.HTTP_404_NOT_FOUND)

        latest_location = shipment.locations.first()
        return Response(
            {
                "tracking_number": shipment.tracking_number,
                "status": shipment.status,
                "status_display": shipment.get_status_display(),
                "carrier": shipment.carrier,
                "estimated_delivery": shipment.estimated_delivery,
                "current_latitude": shipment.current_latitude,
                "current_longitude": shipment.current_longitude,
                "last_location_update": shipment.last_location_update,
                "address": latest_location.address if latest_location else shipment.destination_address,
                "events": ShipmentEventSerializer(shipment.events.all()[:10], many=True).data,
            }
        )
