from django.contrib import admin
from .models import ShippingZone, Shipment, ShipmentLocation, ShipmentEvent, ReturnRequest


@admin.register(ShippingZone)
class ShippingZoneAdmin(admin.ModelAdmin):
    list_display = ["name", "active"]
    search_fields = ["name"]


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ["tracking_number", "order", "carrier", "status", "estimated_delivery", "last_location_update"]
    list_filter = ["status", "carrier", "created_at"]
    search_fields = ["tracking_number", "order__id"]
    readonly_fields = ["created_at", "updated_at", "last_location_update", "tracking_number"]


@admin.register(ShipmentLocation)
class ShipmentLocationAdmin(admin.ModelAdmin):
    list_display = ["shipment", "address", "latitude", "longitude", "status", "timestamp"]
    list_filter = ["status", "timestamp"]
    search_fields = ["shipment__tracking_number", "address"]
    readonly_fields = ["timestamp"]


@admin.register(ShipmentEvent)
class ShipmentEventAdmin(admin.ModelAdmin):
    list_display = ["shipment", "event_type", "title", "location", "timestamp"]
    list_filter = ["event_type", "timestamp"]
    search_fields = ["shipment__tracking_number", "title", "location"]
    readonly_fields = ["timestamp"]


@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):
    list_display = ["order", "user", "status", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["order__id", "user__username"]
    readonly_fields = ["created_at", "updated_at"]
