rom django.urls import path, re_path, include
from django.contrib import admin
from .views import BlogView  
from django.contrib.auth import views as auth_views
from two_factor.views import setup_view, verify_view
from django.views.static import serve
from django.conf import settings
from .views import UpdateAccountSettingsView 

from . import views, consumers
from .views import (
    wishlist_view,
    account_settings_view,
    discount_code_list,
    OffersView,
    feedback_view,
    loyalty_points_list,
    notification_list,
    add_payment_method,
    add_shipping_address,
    send_verification_email,
    generate_referral_link,
    update_security_questions,
    deactivate_account,
    update_theme_preferences,
    export_data,
    submit_feedback,
    link_social_account,
    music_list,
    upload_music,
    submit_review,
    ar_view,
    update_two_factor,
    cart_view,
    update_social_media,
    update_subscription,
    update_language,
    update_privacy,
    returns_view,
    gift_cards_view,
    blog_view,
    PrivacyPolicyView,
    ContactView,
    profile,
    ProfileView,
    EditProfileView,
    AddCommentView,
    ProductDetailView,
    SendVerificationEmailView,
    ResetVerificationStatusView,
    AccountVerificationView,
    add_to_wishlist,
    remove_from_wishlist,
    wishlist,
    update_accessibility,
    


    # Other views...
)

from django.urls import path, re_path, include
from django.contrib import admin
from django.contrib.auth import views as auth_views
from .views import TrackOrderView
from .views import CartView  
from .views import ChatRoomView 
from .views import AddPaymentMethodView
from .views import CheckoutView 
from .views import RecommendedProductsView 
from two_factor.views import setup_view, verify_view
from django.views.static import serve
from .views import GiftCardsView
from .views import UpdateSecurityQuestionsView  
from .views import GenerateReferralLinkView 
from .views import ReturnsView
from .views import ResetVerificationView 
from .views import AddShippingAddressView
from .views import DeleteAccountView
from .views import UpdateAccessibilityView 
from .views import LinkSocialAccountView  
from .views import SubmitFeedbackView 
from .views import SubscribeView 
from .views import ProductListView
from .views import FeedbackThankYouView
from .views import order_history
from .views import MostViewedProductsView  
from .views import redeem_loyalty_points_view
from .views import NotificationView 
from .views import add_to_cart 
from django.conf import settings


from . import consumers, views
from .views import (
    wishlist_view, account_settings_view, discount_code_list, OffersView, feedback_view,
    loyalty_points_list, notification_list, add_payment_method, add_shipping_address,
    send_verification_email, generate_referral_link, update_security_questions,
    deactivate_account, update_theme_preferences, export_data, submit_feedback,
    link_social_account, music_list, upload_music, submit_review, ar_view,
    update_two_factor, cart_view, update_social_media, update_subscription,
    update_language, update_privacy, returns_view, gift_cards_view, blog_view,
    PrivacyPolicyView, ContactView, profile, ProfileView, EditProfileView,
    AddCommentView, ProductDetailView, SendVerificationEmailView,
    ResetVerificationStatusView, AccountVerificationView, add_to_wishlist,
    remove_from_wishlist, update_accessibility
    
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
    #search
     path('signup/', views.SignupView.as_view(), name='signup'),
     path('wishlist/', wishlist, name='wishlist'),
     path('login/', views.login_view, name='login'), 
     path('most-viewed-products/', MostViewedProductsView.as_view(), name='most_viewed_products'),  # Add this line
     path('loyalty-terms/', views.loyalty_terms_view, name='loyalty_terms'), 
     path('redeem-loyalty-points/', redeem_loyalty_points_view, name='redeem_loyalty_points'),
     path('feedback/', feedback_view, name='feedback'),
     path('feedback/thank-you/', FeedbackThankYouView.as_view(), name='feedback_thank_you'),  # Define the URL pattern
     path('track-order/', TrackOrderView.as_view(), name='track_order'), 
     path('returns/', ReturnsView.as_view(), name='returns'),
     path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
     path('gift-cards/', GiftCardsView.as_view(), name='gift_cards'),
     #path('product/<int:id>/', ProductDetailView.as_view(), name='product_detail'),
     path('product/<int:pk>/', ProductDetailView.as_view(), name='product_detail'),
     path('add-to-cart/<int:product_id>/', add_to_cart, name='add_to_cart'),
     path('update-accessibility/', UpdateAccessibilityView.as_view(), name='update_accessibility'),  # URL for updating accessibility settings
    path('link-social-account/', LinkSocialAccountView.as_view(), name='link_social_account'),  # URL for linking social account 
     path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('submit-feedback/', SubmitFeedbackView.as_view(), name='submit_feedback'),  # URL for submitting feedback
     path('subscribe/', SubscribeView.as_view(), name='subscribe'),
     path('update-security-questions/', UpdateSecurityQuestionsView.as_view(), name='update_security_questions'),  # URL for updating security questions
     path('generate-referral-link/', GenerateReferralLinkView.as_view(), name='generate_referral_link'),  # URL for generating a referral link
     path('reset-verification/', ResetVerificationView.as_view(), name='reset_verification'),  # URL for resetting verification status
     path('add-shipping-address/', AddShippingAddressView.as_view(), name='add_shipping_address'),  # URL for adding shipping address  
     path('notifications/', NotificationView.as_view(), name='notification'), 
     path('account-settings/update/', UpdateAccountSettingsView.as_view(), name='update_account_settings'),  # Add this line for updating account settings  
    path('account/delete/', DeleteAccountView.as_view(), name='delete_account'),  
     path('account/add_payment_method/', AddPaymentMethodView.as_view(), name='add_payment_method'),  # Add this line for adding payment method
    # General Views
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', ContactView.as_view(), name='contact'),
    path('faq/', views.faq_view, name='faq'),
    path('privacy-policy/', PrivacyPolicyView.as_view(), name='privacy_policy'),
    path('terms/', views.terms_of_service, name='terms'),
    path('ar_view/<int:product_id>/', ar_view, name='ar_view'),
    
    # Account and Authentication
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='shop/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('account/', views.account_home, name='account_home'),
    path('account-settings/', account_settings_view, name='account_settings'),
    path('deactivate-account/', deactivate_account, name='deactivate_account'),
    path('password-change/', auth_views.PasswordChangeView.as_view(template_name='shop/password_change.html'), name='password_change'),
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='shop/password_reset.html'), name='password_reset'),
    path('send-verification-email/', SendVerificationEmailView.as_view(), name='send_verification_email'),
    path('account-verification/', AccountVerificationView.as_view(), name='account_verification'),
    
    # Profile
    path('profile/', ProfileView.as_view(), name='profile'),
    path('edit_profile/', EditProfileView.as_view(), name='edit_profile'),
    path('update-profile-picture/', views.update_profile_picture, name='update_profile_picture'),

    # Wishlist and Cart
    path('wishlist/', wishlist_view, name='wishlist'),
    path('login/', auth_views.LoginView.as_view(), name='login'),

    path('cart/', cart_view, name='cart_view'),
    path('cart/', CartView.as_view(), name='cart'),
    path('add-to-wishlist/<int:product_id>/', add_to_wishlist, name='add_to_wishlist'),
    path('remove-from-wishlist/<int:item_id>/', remove_from_wishlist, name='remove_from_wishlist'),

    # Products and Offers
    path('product/<int:product_id>/', ProductDetailView.as_view(), name='product_detail'),
    path('submit-review/<int:product_id>/', submit_review, name='submit_review'),
    path('discount-codes/', discount_code_list, name='discount_code_list'),
    path('offers/', OffersView.as_view(), name='offers'),
     path('products/', ProductListView.as_view(), name='product_list'), 

    # Feedback and Loyalty
    path('feedback/', feedback_view, name='feedback_form'),
    path('loyalty-points/', loyalty_points_list, name='loyalty_points_list'),
    path('redeem-points/', views.redeem_points_view, name='redeem_points'),
    
    # Miscellaneous
    path('music_list/', music_list, name='music_list'),
    path('upload_music/', upload_music, name='upload_music'),
    path('ar-view/<int:product_id>/', ar_view, name='ar_view'),
    path('recommended-products/', RecommendedProductsView.as_view(), name='recommended_products'),
    path('blog/', BlogView.as_view(), name='blog'),
    path('chat/<str:room_name>/', ChatRoomView.as_view(), name='chat_room'), 
    path('privacy/', PrivacyPolicyView.as_view(), name='privacy'), 
    path('order-history/', order_history, name='order_history'),
    
    # Static and Media Files during Development
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
