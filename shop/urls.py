from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

app_name = "shop"


urlpatterns = [

    

    path(
        "",
        views.shop,
        name="home",
    ),

    path(
        "shop/",
        views.shop,
        name="shop",
    ),


    # ==================================================
    # AUTHENTICATION
    # ==================================================

    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="shop/login.html"
        ),
        name="login",
    ),

    path(
        "logout/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),


    # ==================================================
    # PRODUCTS
    # ==================================================

    path(
        "products/",
        views.shop,
        name="product_list",
    ),

    path(
        "product/<int:product_id>/",
        views.product_detail,
        name="product_detail",
    ),

    path(
        "search/",
        views.search,
        name="search",
    ),


    # ==================================================
    # CART
    # ==================================================

    path(
        "cart/",
        views.cart_view,
        name="cart",
    ),

    path(
        "cart/view/",
        views.cart_view,
        name="cart_view",
    ),

    path(
        "add-to-cart/<int:product_id>/",
        views.add_to_cart,
        name="add_to_cart",
    ),

    path(
        "cart/update/<int:product_id>/",
        views.update_cart,
        name="update_cart",
    ),

    path(
        "cart/remove/<int:product_id>/",
        views.remove_from_cart,
        name="remove_from_cart",
    ),

    path(
        "cart/clear/",
        views.clear_cart,
        name="clear_cart",
    ),


    # ==================================================
    # PRODUCT DISCOVERY
    # ==================================================

    path(
        "recently-viewed/",
        views.recently_viewed_products,
        name="recently_viewed",
    ),

    path(
        "recommended/",
        views.recommended_products,
        name="recommended",
    ),


    # ==================================================
    # ACCOUNT
    # ==================================================

    # Temporary account page.
    # We can connect your real account system later.
    path(
        "account/",
        auth_views.LoginView.as_view(
            template_name="shop/login.html"
        ),
        name="account_home",
    ),


    # ==================================================
    # ORDERS
    # ==================================================

    # Temporary placeholder until the order system
    # is connected to your real Order model.
    path(
        "orders/",
        views.shop,
        name="order_history",
    ),

]
