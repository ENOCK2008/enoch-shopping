from django.urls import path, re_path
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.views.static import serve
from django.conf import settings

from . import views, consumers

from .views import (
    # Account
    UpdateAccountSettingsView,
    account_settings_view,
    deactivate_account,
    DeleteAccountView,

    # Authentication / verification
    SendVerificationEmailView,
    AccountVerificationView,
    ResetVerificationView,

    # Profile
    ProfileView,
    EditProfileView,

    # Products
    ProductListView,
    ProductDetailView,
    MostViewedProductsView,
    RecommendedProductsView,
    OffersView,

    # Cart / checkout
    CartView,
    CheckoutView,
    add_to_cart,

    # Wishlist
    wishlist,
    wishlist_view,
    add_to_wishlist,
    remove_from_wishlist,

    # Orders
    TrackOrderView,
    order_history,
    ReturnsView,

    # Payments / shipping
    AddPaymentMethodView,
    AddShippingAddressView,

    # Feedback
    feedback_view,
    SubmitFeedbackView,
    FeedbackThankYouView,

    # Loyalty / discounts
    discount_code_list,
    loyalty_points_list,
    redeem_loyalty_points_view,

    # Notifications
    NotificationView,

    # Gift cards
    GiftCardsView,

    # Social / account
    LinkSocialAccountView,
    GenerateReferralLinkView,
    UpdateSecurityQuestionsView,
    UpdateAccessibilityView,

    # Subscription
    SubscribeView,

    # Music
    music_list,
    upload_music,

    # Reviews
    submit_review,

    # AR
    ar_view,

    # Blog
    blog_view,

    # General pages
    PrivacyPolicyView,
    ContactView,

    # Chat
    ChatRoomView,
)

app_name = "shop"


# ============================================================
# WEBSOCKET URLS
# ============================================================

websocket_urlpatterns = [
    re_path(
        r"^ws/chat/(?P<room_name>\w+)/$",
        consumers.ChatConsumer.as_asgi(),
    ),
]


# ============================================================
# HTTP URLS
# ============================================================

urlpatterns = [

    # --------------------------------------------------------
    # ADMIN
    # --------------------------------------------------------

    path("admin/", admin.site.urls),


    # --------------------------------------------------------
    # HOME / GENERAL PAGES
    # --------------------------------------------------------

    path("", views.home, name="home"),

    path("about/", views.about, name="about"),

    path("contact/", ContactView.as_view(), name="contact"),

    path("faq/", views.faq_view, name="faq"),

    path(
        "privacy-policy/",
        PrivacyPolicyView.as_view(),
        name="privacy_policy",
    ),

    path(
        "privacy/",
        PrivacyPolicyView.as_view(),
        name="privacy",
    ),

    path(
        "terms/",
        views.terms_of_service,
        name="terms",
    ),


    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    path(
        "search/",
        views.search,
        name="search",
    ),


    # --------------------------------------------------------
    # AUTHENTICATION
    # --------------------------------------------------------

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

    path(
        "register/",
        views.register,
        name="register",
    ),

    path(
        "signup/",
        views.SignupView.as_view(),
        name="signup",
    ),

    path(
        "password-change/",
        auth_views.PasswordChangeView.as_view(
            template_name="shop/password_change.html"
        ),
        name="password_change",
    ),

    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="shop/password_reset.html"
        ),
        name="password_reset",
    ),


    # --------------------------------------------------------
    # ACCOUNT
    # --------------------------------------------------------

    path(
        "account/",
        views.account_home,
        name="account_home",
    ),

    path(
        "account-settings/",
        account_settings_view,
        name="account_settings",
    ),

    path(
        "account-settings/update/",
        UpdateAccountSettingsView.as_view(),
        name="update_account_settings",
    ),

    path(
        "deactivate-account/",
        deactivate_account,
        name="deactivate_account",
    ),

    path(
        "account/delete/",
        DeleteAccountView.as_view(),
        name="delete_account",
    ),


    # --------------------------------------------------------
    # PROFILE
    # --------------------------------------------------------

    path(
        "profile/",
        ProfileView.as_view(),
        name="profile",
    ),

    path(
        "edit-profile/",
        EditProfileView.as_view(),
        name="edit_profile",
    ),

    path(
        "update-profile-picture/",
        views.update_profile_picture,
        name="update_profile_picture",
    ),


    # --------------------------------------------------------
    # ACCOUNT VERIFICATION
    # --------------------------------------------------------

    path(
        "send-verification-email/",
        SendVerificationEmailView.as_view(),
        name="send_verification_email",
    ),

    path(
        "account-verification/",
        AccountVerificationView.as_view(),
        name="account_verification",
    ),

    path(
        "reset-verification/",
        ResetVerificationView.as_view(),
        name="reset_verification",
    ),


    # --------------------------------------------------------
    # PRODUCTS
    # --------------------------------------------------------

    path(
        "products/",
        ProductListView.as_view(),
        name="product_list",
    ),

    path(
        "product/<int:pk>/",
        ProductDetailView.as_view(),
        name="product_detail",
    ),

    path(
        "most-viewed-products/",
        MostViewedProductsView.as_view(),
        name="most_viewed_products",
    ),

    path(
        "recommended-products/",
        RecommendedProductsView.as_view(),
        name="recommended_products",
    ),

    path(
        "offers/",
        OffersView.as_view(),
        name="offers",
    ),


    # --------------------------------------------------------
    # CART
    # --------------------------------------------------------

    path(
        "cart/",
        CartView.as_view(),
        name="cart",
    ),

    # Alias for templates that use shop:cart_view
    path(
        "cart/view/",
        views.cart_view,
        name="cart_view",
    ),

    path(
        "add-to-cart/<int:product_id>/",
        add_to_cart,
        name="add_to_cart",
    ),

    path(
        "cart/remove/<int:item_id>/",
        views.remove_from_cart,
        name="remove_from_cart",
    ),


    # --------------------------------------------------------
    # WISHLIST
    # --------------------------------------------------------

    path(
        "wishlist/",
        wishlist_view,
        name="wishlist",
    ),

    path(
        "wishlist/legacy/",
        wishlist,
        name="wishlist_legacy",
    ),

    path(
        "add-to-wishlist/<int:product_id>/",
        add_to_wishlist,
        name="add_to_wishlist",
    ),

    path(
        "remove-from-wishlist/<int:item_id>/",
        remove_from_wishlist,
        name="remove_from_wishlist",
    ),


    # --------------------------------------------------------
    # CHECKOUT
    # --------------------------------------------------------

    path(
        "checkout/",
        CheckoutView.as_view(),
        name="checkout",
    ),


    # --------------------------------------------------------
    # PAYMENTS
    # --------------------------------------------------------

    path(
        "account/add-payment-method/",
        AddPaymentMethodView.as_view(),
        name="add_payment_method",
    ),


    # --------------------------------------------------------
    # SHIPPING
    # --------------------------------------------------------

    path(
        "add-shipping-address/",
        AddShippingAddressView.as_view(),
        name="add_shipping_address",
    ),


    # --------------------------------------------------------
    # ORDERS
    # --------------------------------------------------------

    path(
        "track-order/",
        TrackOrderView.as_view(),
        name="track_order",
    ),

    path(
        "order-history/",
        order_history,
        name="order_history",
    ),

    path(
        "returns/",
        ReturnsView.as_view(),
        name="returns",
    ),


    # --------------------------------------------------------
    # REVIEWS
    # --------------------------------------------------------

    path(
        "submit-review/<int:product_id>/",
        submit_review,
        name="submit_review",
    ),


    # --------------------------------------------------------
    # DISCOUNTS
    # --------------------------------------------------------

    path(
        "discount-codes/",
        discount_code_list,
        name="discount_code_list",
    ),


    # --------------------------------------------------------
    # LOYALTY
    # --------------------------------------------------------

    path(
        "loyalty-points/",
        loyalty_points_list,
        name="loyalty_points_list",
    ),

    path(
        "redeem-loyalty-points/",
        redeem_loyalty_points_view,
        name="redeem_loyalty_points",
    ),

    path(
        "redeem-points/",
        views.redeem_points_view,
        name="redeem_points",
    ),

    path(
        "loyalty-terms/",
        views.loyalty_terms_view,
        name="loyalty_terms",
    ),


    # --------------------------------------------------------
    # GIFT CARDS
    # --------------------------------------------------------

    path(
        "gift-cards/",
        GiftCardsView.as_view(),
        name="gift_cards",
    ),


    # --------------------------------------------------------
    # NOTIFICATIONS
    # --------------------------------------------------------

    path(
        "notifications/",
        NotificationView.as_view(),
        name="notification",
    ),


    # --------------------------------------------------------
    # FEEDBACK
    # --------------------------------------------------------

    path(
        "feedback/",
        feedback_view,
        name="feedback",
    ),

    path(
        "submit-feedback/",
        SubmitFeedbackView.as_view(),
        name="submit_feedback",
    ),

    path(
        "feedback/thank-you/",
        FeedbackThankYouView.as_view(),
        name="feedback_thank_you",
    ),


    # --------------------------------------------------------
    # SUBSCRIPTION
    # --------------------------------------------------------

    path(
        "subscribe/",
        SubscribeView.as_view(),
        name="subscribe",
    ),


    # --------------------------------------------------------
    # SOCIAL ACCOUNTS
    # --------------------------------------------------------

    path(
        "link-social-account/",
        LinkSocialAccountView.as_view(),
        name="link_social_account",
    ),

    path(
        "update-social-media/",
        views.update_social_media,
        name="update_social_media",
    ),


    # --------------------------------------------------------
    # SECURITY
    # --------------------------------------------------------

    path(
        "update-security-questions/",
        UpdateSecurityQuestionsView.as_view(),
        name="update_security_questions",
    ),

    path(
        "generate-referral-link/",
        GenerateReferralLinkView.as_view(),
        name="generate_referral_link",
    ),

    path(
        "update-two-factor/",
        views.update_two_factor,
        name="update_two_factor",
    ),


    # --------------------------------------------------------
    # ACCESSIBILITY
    # --------------------------------------------------------

    path(
        "update-accessibility/",
        UpdateAccessibilityView.as_view(),
        name="update_accessibility",
    ),


    # --------------------------------------------------------
    # LANGUAGE / PRIVACY / THEME
    # --------------------------------------------------------

    path(
        "update-language/",
        views.update_language,
        name="update_language",
    ),

    path(
        "update-privacy/",
        views.update_privacy,
        name="update_privacy",
    ),

    path(
        "update-theme/",
        views.update_theme_preferences,
        name="update_theme_preferences",
    ),


    # --------------------------------------------------------
    # MUSIC
    # --------------------------------------------------------

    path(
        "music/",
        music_list,
        name="music_list",
    ),

    path(
        "music/upload/",
        upload_music,
        name="upload_music",
    ),


    # --------------------------------------------------------
    # AR / 3D
    # --------------------------------------------------------

    path(
        "ar-view/<int:product_id>/",
        ar_view,
        name="ar_view",
    ),


    # --------------------------------------------------------
    # BLOG
    # --------------------------------------------------------

    path(
        "blog/",
        blog_view,
        name="blog",
    ),


    # --------------------------------------------------------
    # CHAT
    # --------------------------------------------------------

    path(
        "chat/<str:room_name>/",
        ChatRoomView.as_view(),
        name="chat_room",
    ),


    # --------------------------------------------------------
    # DATA / ACCOUNT
    # --------------------------------------------------------

    path(
        "export-data/",
        views.export_data,
        name="export_data",
    ),


    # --------------------------------------------------------
    # STATIC / MEDIA
    # --------------------------------------------------------

    re_path(
        r"^static/(?P<path>.*)$",
        serve,
        {
            "document_root": settings.STATIC_ROOT,
        },
    ),

    re_path(
        r"^media/(?P<path>.*)$",
        serve,
        {
            "document_root": settings.MEDIA_ROOT,
        },
    ),
]
