from rest_framework.routers import DefaultRouter
from .views import SellerProfileViewSet

router = DefaultRouter()
router.register("", SellerProfileViewSet, basename="sellers")
urlpatterns = router.urls
