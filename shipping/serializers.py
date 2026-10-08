from rest_framework import serializers
from .models import ShippingZone, Shipment, ShipmentLocation, ShipmentEvent, ReturnRequest


class ShippingZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingZone
        fields = "__all__"


class ShipmentLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShipmentLocation
        fields = [
            "id",
            "latitude",
            "longitude",
            "accuracy",
            "address",
            "status",
            "status_note",
            "timestamp",
        ]


class ShipmentEventSerializer(serializers.ModelSerializer):
    event_type_display = serializers.CharField(source="get_event_type_display", read_only=True)

    class Meta:
        model = ShipmentEvent
        fields = [
            "id",
            "event_type",
            "event_type_display",
            "title",
            "description",
            "location",
            "latitude",
            "longitude",
            "timestamp",
        ]


class ShipmentSerializer(serializers.ModelSerializer):
    locations = ShipmentLocationSerializer(many=True, read_only=True)
    events = ShipmentEventSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Shipment
        fields = [
            "id",
            "order",
            "carrier",
            "tracking_number",
            "status",
            "status_display",
            "estimated_delivery",
            "actual_delivery_date",
            "origin_address",
            "origin_latitude",
            "origin_longitude",
            "destination_address",
            "destination_latitude",
            "destination_longitude",
            "current_latitude",
            "current_longitude",
            "last_location_update",
            "locations",
            "events",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["tracking_number", "created_at", "updated_at"]


class ReturnRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReturnRequest
        fields = "__all__"
        read_only_fields = ["user", "status", "created_at", "updated_at"]
