from django.urls import path
from . import views

app_name = "storefront"
urlpatterns = [
    path("", views.home, name="home"),
    path("marketplace/", views.page, {"template": "storefront/marketplace.html"}, name="marketplace"),
    path("sellers/", views.page, {"template": "storefront/sellers.html"}, name="sellers"),
    path("cart/", views.page, {"template": "storefront/cart.html"}, name="cart"),
    path("wishlist/", views.page, {"template": "storefront/wishlist.html"}, name="wishlist"),
    path("account/", views.page, {"template": "storefront/account.html"}, name="account"),
    path("login/", views.page, {"template": "storefront/login.html"}, name="login"),
    path("register/", views.page, {"template": "storefront/register.html"}, name="register"),
    path("orders/", views.page, {"template": "storefront/orders.html"}, name="orders"),
    path("orders/<int:order_id>/", views.page, {"template": "storefront/order_detail.html"}, name="order_detail"),
    path("checkout/", views.page, {"template": "storefront/checkout.html"}, name="checkout"),
    path("payment/", views.page, {"template": "storefront/payment.html"}, name="payment"),
    path("tracking/", views.page, {"template": "storefront/tracking.html"}, name="tracking"),
    path("seller-center/", views.page, {"template": "storefront/seller_dashboard.html"}, name="seller_dashboard"),
    path("seller-center/products/", views.page, {"template": "storefront/seller_products.html"}, name="seller_products"),
    path("seller-center/orders/", views.page, {"template": "storefront/seller_orders.html"}, name="seller_orders"),
    path("returns/", views.page, {"template": "storefront/returns.html"}, name="returns"),
]
