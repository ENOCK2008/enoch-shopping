from django.db import models
from django.utils import timezone
import uuid


class ShippingZone(models.Model):
    name = models.CharField(max_length=120)
    country_codes = models.JSONField(default=list)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Shipment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PICKED_UP = "picked_up", "Picked up"
        IN_TRANSIT = "in_transit", "In transit"
        OUT_FOR_DELIVERY = "out_for_delivery", "Out for delivery"
        DELIVERED = "delivered", "Delivered"
        RETURNED = "returned", "Returned"

    order = models.OneToOneField("orders.Order", on_delete=models.CASCADE, related_name="shipment")
    carrier = models.CharField(max_length=120, blank=True, default="Local Courier")
    tracking_number = models.CharField(max_length=120, blank=True, unique=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING)
    estimated_delivery = models.DateField(null=True, blank=True)
    actual_delivery_date = models.DateField(null=True, blank=True)

    origin_address = models.CharField(max_length=500, blank=True)
    origin_latitude = models.FloatField(null=True, blank=True)
    origin_longitude = models.FloatField(null=True, blank=True)

    destination_address = models.CharField(max_length=500, blank=True)
    destination_latitude = models.FloatField(null=True, blank=True)
    destination_longitude = models.FloatField(null=True, blank=True)

    current_latitude = models.FloatField(null=True, blank=True)
    current_longitude = models.FloatField(null=True, blank=True)
    last_location_update = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.tracking_number:
            self.tracking_number = f"EN-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Shipment {self.tracking_number} - {self.get_status_display()}"


class ShipmentLocation(models.Model):
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name="locations")
    latitude = models.FloatField()
    longitude = models.FloatField()
    accuracy = models.FloatField(null=True, blank=True)
    address = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=30, choices=Shipment.Status.choices, default=Shipment.Status.IN_TRANSIT)
    status_note = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.shipment.tracking_number} - {self.timestamp}"


class ShipmentEvent(models.Model):
    class EventType(models.TextChoices):
        CREATED = "created", "Order Created"
        PICKED_UP = "picked_up", "Picked Up"
        DEPARTURE = "departure", "Departed"
        ARRIVAL = "arrival", "Arrived"
        OUT_FOR_DELIVERY = "out_for_delivery", "Out for Delivery"
        ATTEMPTED_DELIVERY = "attempted_delivery", "Delivery Attempted"
        DELIVERED = "delivered", "Delivered"
        EXCEPTION = "exception", "Exception"
        RETURNED = "returned", "Returned"
        LOST = "lost", "Lost"

    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField(max_length=30, choices=EventType.choices)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=500, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.shipment.tracking_number} - {self.title}"


class ReturnRequest(models.Model):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        RECEIVED = "received", "Received"
        REFUNDED = "refunded", "Refunded"

    order = models.ForeignKey("orders.Order", on_delete=models.CASCADE, related_name="returns")
    user = models.ForeignKey("users.User", on_delete=models.CASCADE)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REQUESTED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Return request for order {self.order_id}"
