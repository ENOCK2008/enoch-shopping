from django.urls import path, re_path, include
from django.contrib import admin
from django.contrib.auth import views as auth_views
from two_factor.views import setup_view, verify_view
from . import views
from . import consumers
from django.views.static import serve
from django.conf import settings
from django.contrib.auth.views import LogoutView
from .views import mtn_view, ProductDetailView, ProfileView, some_action, mark_as_read, notification_view
from shop.views import ViewedProductsView, HomeView, OrderHistoryView, register
from .views import CartView, wishlist_view, OffersView, feedback_view
from .views import register_view
from django.contrib.auth.views import LoginView
app_name = 'shop'

# WebSocket URL patterns
websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),
]

# Main URL patterns
urlpatterns = [
    path('mtn/', mtn_view, name='mtn_view'),
    path('admin/', admin.site.urls),
    path('signup/', views.register_view, name='signup'),
    path('cart/', CartView.as_view(), name='cart'),
    path('offers/', OffersView.as_view(), name='offers'),

    path('shop/login/', auth_views.LoginView.as_view(template_name='shop/login.html'), name='login'),
    path('shop/logout/', LogoutView.as_view(), name='logout'),
    path('shop/register/', views.register_view, name='register_view'),  # Correct registration view
    path('viewed_products/', ViewedProductsView.as_view(), name='viewed_products'),

    # Other paths
    path('bot/', views.chat_bot_view, name='chat_bot'),
    path('', views.home, name='home'),
    path('account/', views.account_home, name='account_home'),
    path('profile/', views.profile, name='profile'),
    path('update_cart_item/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('remove_from_cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('product/<int:id>/', ProductDetailView.as_view(), name='product_detail'),
    path('categories/', views.categories, name='categories'),
    path('shop/', views.shop, name='shop'),
    path('shop/login/', LoginView.as_view(template_name='shop/login.html'), name='login'),
    path('notifications/', notification_view, name='notifications'),
    path('checkout/', views.checkout, name='checkout'),
    path('payment_success/', views.payment_success, name='payment_success'),
    path('payment_failure/', views.payment_failure, name='payment_failure'),
    path('ar_view/<int:pk>/', views.ar_view, name='ar_view'),
    path('upload_music/', views.upload_music, name='upload_music'),
    path('music_list/', views.music_list, name='music_list'),
    path('chat/<str:room_name>/', views.chat_room, name='chat_room'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),

    # Feedback, notification, loyalty points
    path('feedback/', feedback_view, name='feedback'),
    path('loyalty_points/', views.loyalty_points_list, name='loyalty_points_list'),
    path('notification/', views.notification_view, name='notification'),
    path('order-history/', OrderHistoryView.as_view(), name='order_history'),
     path('order-history/', views.order_history, name='order_history'),
    path('account-settings/', views.account_settings_view, name='account_settings'),
    path('wishlist/', wishlist_view, name='wishlist'),

    # Discount management
    path('discount_codes/create/', views.create_discount_code, name='create_discount_code'),
    path('account/settings/update/', views.update_account_settings, name='update_account_settings'),
    path('account/delete/', views.delete_account, name='delete_account'),

    # Built-in auth views
    path('login/', auth_views.LoginView.as_view(template_name='shop/login.html'), name='login'),
    path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='shop/password_change_done.html'), name='password_change_done'),
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='shop/password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='shop/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='shop/password_reset_confirm.html'), name='password_reset_confirm'),
    path('password-change/', auth_views.PasswordChangeView.as_view(template_name='shop/password_change.html'), name='password_change'),

    # Two-factor authentication
    path('two_factor/', include('two_factor.urls', namespace='two_factor')),
    path('music_view/<int:music_id>/', views.music_view, name='music_view'),
    path('account_home/', views.account_home, name='account_home'),
    path('recommended/', views.recommended_products_view, name='recommended_products'),
    path('update_profile_picture/', views.update_profile_picture, name='update_profile_picture'),
    path('edit_profile/', views.EditProfileView.as_view(), name='edit_profile'),
    path('some-action/', some_action, name='some_action'),
    path('notification/mark-as-read/<int:notification_id>/', mark_as_read, name='mark_as_read'),
    path('product/<int:product_id>/review/', views.submit_review, name='submit_review'),

    # Correct user registration path
    path('register/', views.register_view, name='register'),
    path('register/', register_view, name='register'),
    path('privacy/', views.privacy_policy, name='privacy'),
    path('terms/', views.terms_of_service, name='terms'),
    path('contact/', views.contact_us, name='contact'),


    # Two-factor authentication views
    path('account/setup/', setup_view, name='setup'),
    path('account/verify/', verify_view, name='verify'),
]

# Static and media files handling during development
if settings.DEBUG:
    urlpatterns += [
        re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]
