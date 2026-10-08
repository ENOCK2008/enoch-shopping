from rest_framework import serializers
from .models import ShippingZone, Shipment, ReturnRequest
class ShippingZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model=ShippingZone
        fields="__all__"
class ShipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model=Shipment
        fields="__all__"
class ReturnRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model=ReturnRequest
        fields="__all__"
        read_only_fields=["user","status","created_at","updated_at"]
