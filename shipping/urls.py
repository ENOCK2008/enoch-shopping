from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import ShippingZoneViewSet, ShipmentViewSet, ReturnRequestViewSet
router=DefaultRouter()
router.register("zones",ShippingZoneViewSet,basename="zone")
router.register("shipments",ShipmentViewSet,basename="shipment")
router.register("returns",ReturnRequestViewSet,basename="return")
urlpatterns=[path("",include(router.urls))]
