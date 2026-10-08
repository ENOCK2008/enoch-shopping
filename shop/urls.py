from django.urls import path
from django.contrib.auth import views as auth_views

app_name = "shop"

urlpatterns = [
    # Home
    path("", lambda request: __import__('django.http', fromlist=['HttpResponse']).HttpResponse("<h1>Enock Shopping Center</h1>"), name="home"),
    
    # Auth
    path("login/", auth_views.LoginView.as_view(template_name="shop/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("register/", lambda request: __import__('django.http', fromlist=['HttpResponse']).HttpResponse("<h1>Register</h1>"), name="register"),
    
    # Account
    path("account/", lambda request: __import__('django.http', fromlist=['HttpResponse']).HttpResponse("<h1>Account</h1>"), name="account_home"),
    
    # Products
    path("products/", lambda request: __import__('django.http', fromlist=['HttpResponse']).HttpResponse("<h1>Products</h1>"), name="product_list"),
    
    # Cart
    path("cart/", lambda request: __import__('django.http', fromlist=['HttpResponse']).HttpResponse("<h1>Cart</h1>"), name="cart"),
    
    # Orders
    path("orders/", lambda request: __import__('django.http', fromlist=['HttpResponse']).HttpResponse("<h1>Orders</h1>"), name="order_history"),
]
