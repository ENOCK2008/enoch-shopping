from django.urls import path, re_path, include
from django.contrib import admin
from django.contrib.auth import views as auth_views
from two_factor.views import setup_view, verify_view  # Assuming these are function-based views
from . import views
from . import consumers
from django.views.static import serve
from django.conf import settings

app_name = 'shop'

# WebSocket URL patterns
websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),
]

# Main URL patterns
urlpatterns = [
    path('admin/', admin.site.urls),
    
    # User authentication using class-based views
    path('shop/login/', auth_views.LoginView.as_view(template_name='shop/login.html'), name='login'),
    path('shop/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('shop/register/', views.register_view, name='register_view'),  # Assuming register_view exists in views.py

    # Bot and home views
    path('bot/', views.chat_bot_view, name='chat_bot'),
    path('', views.home, name='home'),
    path('account/', views.account_home, name='account_home'),

    # Profile and cart management
    path('profile/', views.profile, name='profile'),
    path('update_cart_item/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('remove_from_cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/', views.CartView.as_view(), name='cart_view'),
    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),

    # Product and category views
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('categories/', views.categories, name='categories'),
    path('shop/', views.shop, name='shop'),

    # Checkout and payment
    path('checkout/', views.checkout, name='checkout'),
    path('payment_success/', views.payment_success, name='payment_success'),
    path('payment_failure/', views.payment_failure, name='payment_failure'),

    # AR and music views
    path('ar_view/<int:pk>/', views.ar_view, name='ar_view'),
    path('upload_music/', views.upload_music, name='upload_music'),
    path('music_list/', views.music_list, name='music_list'),

    # Chat views
    path('chat/<str:room_name>/', views.chat_room, name='chat_room'),

    # Miscellaneous views
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('music/', views.music_list, name='music'),

    # New views (feedback, notification, loyalty points)
    path('feedback/', views.feedback_view, name='feedback'),
    path('music/', views.music_view, name='music'),
    path('loyalty_points/', views.loyalty_points_list, name='loyalty_points_list'),
    path('notification/', views.notification_view, name='notification'),
     path('notifications/', views.notification_view, name='notification_view'),
     path('order_history/', views.order_history, name='order_history'),
     path('discount_codes/create/', views.create_discount_code, name='create_discount_code'),
     

    # Discount management views
    path('discount_codes/', views.discount_code_list, name='discount_code_list'),
    path('discount_codes/create/', views.create_discount_code, name='create_discount_code'),
    path('discount_codes/delete/<int:code_id>/', views.delete_discount_code, name='delete_discount_code'),
    path('discount_codes/update/<int:code_id>/', views.update_discount_code, name='update_discount_code'),
    path('update_loyalty_points/', views.update_loyalty_points, name='update_loyalty_points'),

    # Test view
    path('test/', views.test_view, name='test_view'),

    # Built-in auth views (login, logout, register)
    path('login/', auth_views.LoginView.as_view(template_name='shop/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),  # Assuming register exists in views.py

    # Password reset views
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='shop/password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='shop/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='shop/password_reset_confirm.html'), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='shop/password_reset_complete.html'), name='password_reset_complete'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),

    # Two-factor authentication
    path('two_factor/', include('two_factor.urls', namespace='two_factor')),
    path('create_discount_code/', views.create_discount_code, name='create_discount_code'),
    path('music_view/', views.music_view, name='music_view'),
    path('account_home/', views.account_home, name='account_home'),
    path('discount_codes/update/<int:code_id>/', views.update_discount_code, name='update_discount_code'),
    
]

# Adding two-factor authentication views if they are function-based views (setup and verify)
urlpatterns += [
    path('account/setup/', setup_view, name='setup'),
    path('account/verify/', verify_view, name='verify'),
]

# Static and media files handling during development
if settings.DEBUG:
    urlpatterns += [
        re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]
