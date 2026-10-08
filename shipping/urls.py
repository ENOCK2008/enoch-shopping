from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ShippingZoneViewSet, ShipmentViewSet, ReturnRequestViewSet, PublicTrackingViewSet

router = DefaultRouter()
router.register(r"zones", ShippingZoneViewSet, basename="shipping-zone")
router.register(r"shipments", ShipmentViewSet, basename="shipment")
router.register(r"returns", ReturnRequestViewSet, basename="return-request")
router.register(r"public", PublicTrackingViewSet, basename="public-tracking")

urlpatterns = [
    path("", include(router.urls)),
    path("track/<str:tracking_number>/", PublicTrackingViewSet.as_view({"get": "track"}), name="public_tracking"),
]
