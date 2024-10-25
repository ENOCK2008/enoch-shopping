from django.urls import path, re_path, include
from django.contrib import admin
from django.contrib.auth import views as auth_views
from two_factor.views import setup_view, verify_view
from . import views
from . import consumers
from django.views.static import serve
from django.conf import settings
from .views import wishlist_view
from .views import account_settings_view
from .views import discount_code_list
from .views import OffersView 
from .views import feedback_view  # Ensure this import is present
from .views import loyalty_points_list  # Ensure this import is present
from .views import notification_list
from .views import add_payment_method
from .views import add_shipping_address
from .views import send_verification_email 
from .views import generate_referral_link
from .views import update_security_questions 
from .views import deactivate_account
from .views import update_theme_preferences
from .views import export_data
from .views import submit_feedback
from .views import link_social_account
from .views import music_list, upload_music 
from .views import submit_review 
from .views import ar_view   
from .views import update_two_factor 
from .views import cart_view
from .views import update_social_media
from .views import update_subscription 
from .views import update_language
from .views import update_privacy
from .views import returns_view
from .views import gift_cards_view
from .views import blog_view
from .views import PrivacyPolicyView, ContactView
from .views import profile 
from .views import ProfileView, EditProfileView 
from .views import AddCommentView
from .views import ProductDetailView
from .views import add_to_wishlist, remove_from_wishlist, wishlist
from . import views 
from .views import (
    link_social_account,
    update_accessibility,
    # Other views...
)

app_name = 'shop'

# WebSocket URL patterns
websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),
]

# Main URL patterns
urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('wishlist/', wishlist_view, name='wishlist'),
    path('account-settings/', account_settings_view, name='account_settings'),
    path('discount_codes/', views.discount_code_list, name='discount_code_list'),
    path('offers/', OffersView.as_view(), name='offer_list'),
    path('feedback/', feedback_view, name='feedback_form'), 
    path('loyalty-points/', loyalty_points_list, name='loyalty_points_list'),  # Adjust the path as necessary
    path('notification_list/', views.notification_list, name='notification_list'),
    path('faq/', views.faq_view, name='faq'),
    path('privacy/', views.privacy_policy, name='privacy'),
    path('privacy/', views.privacy_policy, name='privacy'),  # Check that this line exists
    path('register/', views.register, name='register'),
    path('notifications/', views.notification_view, name='notification'), 
    path('loyalty-points/', views.loyalty_points_list, name='loyalty_points_list'),
    path('redeem-points/', views.redeem_points_view, name='redeem_points'),
    path('loyalty-terms/', views.loyalty_terms_view, name='loyalty_terms'),
    path('add-payment-method/', add_payment_method, name='add_payment_method'),
    path('add-shipping-address/', add_shipping_address, name='add_shipping_address'), 
    path('send-verification-email/', send_verification_email, name='send_verification_email'),
    path('generate-referral-link/', generate_referral_link, name='generate_referral_link'),
    path('update-security-questions/', update_security_questions, name='update_security_questions'),
    path('deactivate-account/', deactivate_account, name='deactivate_account'),
    path('update-theme-preferences/', update_theme_preferences, name='update_theme_preferences'), 
    path('submit-feedback/', submit_feedback, name='submit_feedback'),
    path('export-data/', export_data, name='export_data'), 
    path('link-social-account/', link_social_account, name='link_social_account'),
    path('link-social-account/', link_social_account, name='link_social_account'),
    path('update-accessibility/', update_accessibility, name='update_accessibility'),
    path('music_list/', music_list, name='music_list'),  # Ensure this is correct
    path('upload_music/', upload_music, name='upload_music'),
    path('submit-review/<int:product_id>/', submit_review, name='submit_review'),
    path('ar-view/<int:product_id>/', ar_view, name='ar_view'),
    path('cart/', cart_view, name='cart_view'),
    path('update_social_media/', update_social_media, name='update_social_media'),
    path('update_two_factor/', update_two_factor, name='update_two_factor'),
    path('account/update-subscription/', update_subscription, name='update_subscription'),
    path('account/update-privacy/', update_privacy, name='update_privacy'),
    path('account/update-language/', update_language, name='update_language'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('track-order/', views.track_order, name='track_order'),
    path('returns/', returns_view, name='returns'),
    path('gift-cards/', gift_cards_view, name='gift_cards'),
    path('blog/', blog_view, name='blog'),
    path('', views.home, name='home'),  # Your home view
    path('subscribe/', views.subscribe, name='subscribe'),  
    path('category/<str:slug>/', views.CategoryView.as_view(), name='category'),
    path('privacy-policy/', PrivacyPolicyView.as_view(), name='privacy_policy'),
    path('contact/', ContactView.as_view(), name='contact'),
    path('profile/', profile , name='profile'),
    path('filtered-products/', views.FilteredProductsView.as_view(), name='filtered_products'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('edit_profile/', EditProfileView.as_view(), name='edit_profile'),
    path('add_comment/<int:product_id>/', AddCommentView.as_view(), name='add_comment'),
    path('ar-view/<int:product_id>/', ar_view, name='ar_view'),
    path("chat_response/", views.chat_response, name="chat_response"),
    #path('recommended-products/', views.recommended_products_view, name='recommended_products'),
    path('add-to-wishlist/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('remove-from-wishlist/<int:item_id>/', remove_from_wishlist, name='remove_from_wishlist'),  # Add this line
    path('product/<int:product_id>/', ProductDetailView.as_view(), name='product_detail'),  # Use product_id here




    
    

    
    





    # Authentication
    path('shop/login/', auth_views.LoginView.as_view(template_name='shop/login.html'), name='login'),
    path('shop/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', views.register_view, name='signup'),
    path('account/setup/', setup_view, name='setup'),
    path('account/verify/', verify_view, name='verify'),

    # User account management
    path('account/', views.account_home, name='account_home'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('account/settings/update/', views.update_account_settings, name='update_account_settings'),
    path('account/delete/', views.delete_account, name='delete_account'),
    path('edit_profile/', views.EditProfileView.as_view(), name='edit_profile'),
    path('update_profile_picture/', views.update_profile_picture, name='update_profile_picture'),
    path('password-change/', auth_views.PasswordChangeView.as_view(template_name='shop/password_change.html'), name='password_change'),
    path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='shop/password_change_done.html'), name='password_change_done'),
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='shop/password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='shop/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='shop/password_reset_confirm.html'), name='password_reset_confirm'),

    # Products and offers
    path('discount-codes/', views.DiscountCodeListView.as_view(), name='discount_code'),
    path('discount_codes/create/', views.create_discount_code, name='create_discount_code'),
    path('offers/', views.OffersView.as_view(), name='offers'),
    path('most_viewed/', views.most_viewed_view, name='most_viewed'),
    path('recommended/', views.recommended_products_view, name='recommended_products'),

    # Cart and checkout
    path('cart/', views.CartView.as_view(), name='cart'),
    #path('checkout/', views.checkout, name='checkout'),
    path('payment_success/', views.payment_success, name='payment_success'),
    path('payment_failure/', views.payment_failure, name='payment_failure'),
    path('remove_from_cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('update_cart_item/<int:item_id>/', views.update_cart_item, name='update_cart_item'),

    # Viewing products
    path('product/<int:id>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('viewed_products/', views.ViewedProductsView.as_view(), name='viewed_products'),

    # Chat and notifications
    path('chat/<str:room_name>/', views.chat_room, name='chat_room'),
    path('notifications/', views.notification_view, name='notifications'),
    path('notification/mark-as-read/<int:notification_id>/', views.mark_as_read, name='mark_as_read'),

    # Miscellaneous
    path('about/', views.about, name='about'),
    path('contact/', views.contact_us, name='contact'),
    path('feedback/', views.feedback_view, name='feedback'),
    path('loyalty_points/', views.loyalty_points_list, name='loyalty_points'),
    path('order-history/', views.order_history, name='order_history'),
    path('search/', views.search_view, name='search'),
    path('categories/', views.categories, name='categories'),
    path('shop/', views.shop, name='shop'),
    path('terms/', views.terms_of_service, name='terms'),
    path('privacy/', views.privacy_policy, name='privacy'),

    # Music views
    path('upload_music/', views.upload_music, name='upload_music'),
    path('music_list/', views.music_list, name='music_list'),
    path('music_view/<int:music_id>/', views.music_view, name='music_view'),
]

# Static and media files handling during development
if settings.DEBUG:
    urlpatterns += [
        re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]
