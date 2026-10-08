from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import CountryViewSet, CurrencyRateViewSet
router = DefaultRouter()
router.register("countries", CountryViewSet, basename="country")
router.register("rates", CurrencyRateViewSet, basename="rate")
urlpatterns = [path("", include(router.urls))]
