from django.urls import path, re_path
from django.contrib.auth import views as auth_views
from two_factor import views as two_factor_views
from . import views
from . import consumers

app_name = 'shop'

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),
]

urlpatterns = [
    # Chat bot view
    path('bot/', views.chat_bot_view, name='chat_bot'),

    # Home and profile views
    path('', views.home, name='home'),
    path('profile/', views.profile, name='profile'),

    # Cart views
    path('update_cart_item/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('remove_from_cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/', views.CartView.as_view(), name='cart_view'),
    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),

    # Product views
    path('product/<int:pk>/', views.product_detail, name='product_detail'),

    # Checkout and payment views
    path('checkout/', views.checkout, name='checkout'),
    path('payment_success/', views.payment_success, name='payment_success'),
    path('payment_failure/', views.payment_failure, name='payment_failure'),

    # AR view and preferences
    path('ar_view/<int:pk>/', views.ar_view, name='ar_view'),
    path('update_preferences/', views.update_preferences, name='update_preferences'),

    # Music upload and list
    path('upload_music/', views.upload_music, name='upload_music'),
    path('music_list/', views.music_list, name='music_list'),

    # Chat room view
    path('chat/<str:room_name>/', views.chat_room, name='chat_room'),

    # Shop-related views
    path('shop/', views.shop, name='shop'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),

    # Authentication views
    path('login/', auth_views.LoginView.as_view(template_name='shop/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),

    # Password reset views
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='shop/password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='shop/password_reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='shop/password_reset_confirm.html'), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='shop/password_reset_complete.html'), name='password_reset_complete'),

    # Two-factor authentication setup
    path('setup/', two_factor_views.setup_view, name='setup'),

    # Order history
    path('orders/', views.order_history, name='order_history'),
]
