from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from config.health import health
from admin_api import dashboard

urlpatterns = [
    path("", include("storefront.urls")),
    path("admin/", admin.site.urls),
    path("health/", health),
    path("api/admin/dashboard/", dashboard),
    path("api/users/", include("users.urls")),
    path("api/sellers/", include("sellers.urls")),
    path("api/catalog/", include("catalog.urls")),
    path("api/cart/", include("cart.urls")),
    path("api/orders/", include("orders.urls")),
    path("api/reviews/", include("reviews.urls")),
    path("api/messages/", include("messaging.urls")),
    path("api/localization/", include("localization.urls")),
    path("api/payments/", include("payments.urls")),
    path("api/shipping/", include("shipping.urls")),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
