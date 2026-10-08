from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import PaymentViewSet, provider_webhook

router = DefaultRouter()
router.register("", PaymentViewSet, basename="payment")
urlpatterns = router.urls + [path("webhooks/<str:provider>/", provider_webhook, name="provider-webhook")]
