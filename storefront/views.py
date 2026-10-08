from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie


# ============================================================
# ENOCK SHOPPING CENTER - STOREFRONT VIEWS
# ============================================================

@ensure_csrf_cookie
def home(request):
    """
    Modern homepage for Enock Shopping Center.

    Kept intentionally lightweight so the homepage can render
    even when the database has no products yet.
    """

    context = {
        "site_name": "Enock Shopping Center",
        "site_tagline": "Shop. Sell. Discover.",
        "currency": "UGX",

        "categories": [
            {
                "name": "Phones & Electronics",
                "url": "/marketplace/",
                "icon": "fa-mobile-screen-button",
            },
            {
                "name": "Solar Products",
                "url": "/marketplace/",
                "icon": "fa-solar-panel",
            },
            {
                "name": "Vehicles & Bikes",
                "url": "/marketplace/",
                "icon": "fa-motorcycle",
            },
            {
                "name": "Fashion",
                "url": "/marketplace/",
                "icon": "fa-shirt",
            },
            {
                "name": "Home & Living",
                "url": "/marketplace/",
                "icon": "fa-house",
            },
            {
                "name": "Agriculture & Animals",
                "url": "/marketplace/",
                "icon": "fa-leaf",
            },
        ],

        "features": [
            {
                "title": "Shop Online",
                "description": "Discover products from sellers across Uganda.",
                "icon": "fa-cart-shopping",
            },
            {
                "title": "Sell With Us",
                "description": "Create your seller profile and reach more customers.",
                "icon": "fa-store",
            },
            {
                "title": "Secure Payments",
                "description": "Convenient payment options for your purchases.",
                "icon": "fa-shield-halved",
            },
            {
                "title": "Fast Delivery",
                "description": "Get your purchases delivered to your location.",
                "icon": "fa-truck-fast",
            },
        ],

        "quick_links": [
            {
                "name": "Marketplace",
                "url": "/marketplace/",
            },
            {
                "name": "Sellers",
                "url": "/sellers/",
            },
            {
                "name": "Cart",
                "url": "/cart/",
            },
            {
                "name": "Wishlist",
                "url": "/wishlist/",
            },
        ],
    }

    return render(
        request,
        "storefront/home.html",
        context,
    )


def page(request, template):
    """
    Generic storefront page renderer.

    Used by simple pages such as marketplace, cart,
    wishlist, account, checkout and seller center.
    """

    context = {
        "site_name": "Enock Shopping Center",
        "currency": "UGX",
    }

    return render(
        request,
        template,
        context,
    )
