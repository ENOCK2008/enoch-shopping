from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .models import Product


# ============================================================
# HOME / SHOP
# ============================================================

def shop(request):
    """
    Main international marketplace.

    Supports:
    - Product search
    - Price filtering
    - Sorting
    - Pagination
    - Safe product display
    """

    products = Product.objects.all()

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    query = request.GET.get("q", "").strip()

    if query:
        products = products.filter(
            Q(name__icontains=query)
        )

    # --------------------------------------------------------
    # PRICE FILTER
    # --------------------------------------------------------

    min_price = request.GET.get("min_price", "").strip()
    max_price = request.GET.get("max_price", "").strip()

    if min_price:
        try:
            min_value = Decimal(min_price)

            if min_value >= 0:
                products = products.filter(
                    price__gte=min_value
                )

        except (InvalidOperation, ValueError):
            pass

    if max_price:
        try:
            max_value = Decimal(max_price)

            if max_value >= 0:
                products = products.filter(
                    price__lte=max_value
                )

        except (InvalidOperation, ValueError):
            pass

    # --------------------------------------------------------
    # SORTING
    # --------------------------------------------------------

    sort = request.GET.get("sort", "newest")

    if sort == "price_low":
        products = products.order_by("price")

    elif sort == "price_high":
        products = products.order_by("-price")

    elif sort == "name":
        products = products.order_by("name")

    else:
        # Default
        products = products.order_by("-id")

    # --------------------------------------------------------
    # PAGINATION
    # --------------------------------------------------------

    paginator = Paginator(products, 24)

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "shop/shop.html",
        {
            "products": page_obj.object_list,
            "page_obj": page_obj,
            "paginator": paginator,
            "query": query,
            "min_price": min_price,
            "max_price": max_price,
            "sort": sort,
        },
    )


# ============================================================
# PRODUCT DETAIL
# ============================================================

def product_detail(request, product_id):
    """
    Display detailed information about a product.
    """

    product = get_object_or_404(
        Product,
        id=product_id,
    )

    # --------------------------------------------------------
    # RECENTLY VIEWED PRODUCTS
    # --------------------------------------------------------

    recently_viewed = request.session.get(
        "recently_viewed",
        [],
    )

    product_id_string = str(product.id)

    # Remove duplicate
    recently_viewed = [
        item
        for item in recently_viewed
        if str(item) != product_id_string
    ]

    # Add current product to beginning
    recently_viewed.insert(
        0,
        product.id,
    )

    # Keep only latest 10 products
    recently_viewed = recently_viewed[:10]

    request.session["recently_viewed"] = recently_viewed
    request.session.modified = True

    # --------------------------------------------------------
    # RECOMMENDED PRODUCTS
    # --------------------------------------------------------

    recommended_products = (
        Product.objects
        .exclude(id=product.id)
        .order_by("-id")[:8]
    )

    return render(
        request,
        "shop/product_detail.html",
        {
            "product": product,
            "recommended_products": recommended_products,
        },
    )


# ============================================================
# SEARCH
# ============================================================

def search(request):
    """
    Global product search.

    Searches product names and supports sorting
    and pagination.
    """

    query = request.GET.get("q", "").strip()

    products = Product.objects.all()

    if query:
        products = products.filter(
            Q(name__icontains=query)
        )
    else:
        products = products.none()

    # --------------------------------------------------------
    # SORTING
    # --------------------------------------------------------

    sort = request.GET.get(
        "sort",
        "relevance",
    )

    if sort == "price_low":
        products = products.order_by("price")

    elif sort == "price_high":
        products = products.order_by("-price")

    elif sort == "name":
        products = products.order_by("name")

    else:
        products = products.order_by("-id")

    # --------------------------------------------------------
    # PAGINATION
    # --------------------------------------------------------

    paginator = Paginator(
        products,
        24,
    )

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(
        page_number
    )

    return render(
        request,
        "shop/search.html",
        {
            "products": page_obj.object_list,
            "page_obj": page_obj,
            "paginator": paginator,
            "query": query,
            "sort": sort,
        },
    )


# ============================================================
# CART HELPERS
# ============================================================

def _get_cart(request):
    """
    Get the current session shopping cart.
    """

    return request.session.get(
        "cart",
        {},
    )


def _save_cart(request, cart):
    """
    Save shopping cart safely.
    """

    request.session["cart"] = cart
    request.session.modified = True


# ============================================================
# ADD TO CART
# ============================================================

@login_required
def add_to_cart(request, product_id):
    """
    Add a product to the shopping cart.
    """

    product = get_object_or_404(
        Product,
        id=product_id,
    )

    # --------------------------------------------------------
    # STOCK CHECK
    # --------------------------------------------------------

    if product.stock <= 0:

        messages.warning(
            request,
            "Sorry, this product is currently out of stock.",
        )

        return redirect(
            "shop:product_detail",
            product_id=product.id,
        )

    # --------------------------------------------------------
    # CART
    # --------------------------------------------------------

    cart = _get_cart(request)

    product_id = str(
        product.id
    )

    if product_id in cart:

        current_quantity = int(
            cart[product_id].get(
                "quantity",
                1,
            )
        )

        # Prevent buying more than available stock
        if current_quantity >= product.stock:

            messages.warning(
                request,
                "You cannot add more than the available stock.",
            )

            return redirect(
                "shop:product_detail",
                product_id=product.id,
            )

        cart[product_id][
            "quantity"
        ] = current_quantity + 1

    else:

        cart[product_id] = {
            "name": product.name,
            "price": str(product.price),
            "quantity": 1,
        }

    _save_cart(
        request,
        cart,
    )

    messages.success(
        request,
        f"{product.name} has been added to your cart.",
    )

    return redirect(
        "shop:cart_view"
    )


# ============================================================
# CART
# ============================================================

@login_required
def cart_view(request):
    """
    Display the customer's shopping cart.
    """

    cart = _get_cart(request)

    cart_items = []

    total = Decimal("0.00")

    # --------------------------------------------------------
    # BUILD CART
    # --------------------------------------------------------

    for product_id, item in cart.items():

        try:
            product = Product.objects.get(
                id=product_id,
            )

        except Product.DoesNotExist:

            continue

        # ----------------------------------------------------
        # QUANTITY
        # ----------------------------------------------------

        try:
            quantity = int(
                item.get(
                    "quantity",
                    1,
                )
            )

        except (
            TypeError,
            ValueError,
        ):

            quantity = 1

        if quantity < 1:
            quantity = 1

        # ----------------------------------------------------
        # STOCK VALIDATION
        # ----------------------------------------------------

        if product.stock <= 0:
            continue

        if quantity > product.stock:
            quantity = product.stock

        # ----------------------------------------------------
        # PRICE
        # ----------------------------------------------------

        price = Decimal(
            str(product.price)
        )

        subtotal = (
            price * quantity
        )

        total += subtotal

        cart_items.append(
            {
                "product": product,
                "quantity": quantity,
                "price": price,
                "subtotal": subtotal,
            }
        )

    # --------------------------------------------------------
    # SAVE CORRECTED QUANTITIES
    # --------------------------------------------------------

    corrected_cart = {}

    for item in cart_items:

        product = item["product"]

        corrected_cart[
            str(product.id)
        ] = {
            "name": product.name,
            "price": str(product.price),
            "quantity": item["quantity"],
        }

    if corrected_cart != cart:

        _save_cart(
            request,
            corrected_cart,
        )

    return render(
        request,
        "shop/cart.html",
        {
            "cart_items": cart_items,
            "total": total,
            "cart_count": sum(
                item["quantity"]
                for item in cart_items
            ),
        },
    )


# ============================================================
# UPDATE CART QUANTITY
# ============================================================

@login_required
def update_cart(request, product_id):
    """
    Update the quantity of a product in the cart.
    """

    if request.method != "POST":

        return redirect(
            "shop:cart_view"
        )

    product = get_object_or_404(
        Product,
        id=product_id,
    )

    cart = _get_cart(request)

    product_id = str(
        product.id
    )

    if product_id not in cart:

        messages.warning(
            request,
            "This product is not in your cart.",
        )

        return redirect(
            "shop:cart_view"
        )

    try:

        quantity = int(
            request.POST.get(
                "quantity",
                1,
            )
        )

    except (
        TypeError,
        ValueError,
    ):

        quantity = 1

    # --------------------------------------------------------
    # REMOVE
    # --------------------------------------------------------

    if quantity <= 0:

        del cart[product_id]

        _save_cart(
            request,
            cart,
        )

        messages.success(
            request,
            "Product removed from your cart.",
        )

        return redirect(
            "shop:cart_view"
        )

    # --------------------------------------------------------
    # STOCK LIMIT
    # --------------------------------------------------------

    if quantity > product.stock:

        quantity = product.stock

        messages.warning(
            request,
            "Quantity adjusted to the available stock.",
        )

    cart[product_id][
        "quantity"
    ] = quantity

    cart[product_id][
        "price"
    ] = str(product.price)

    _save_cart(
        request,
        cart,
    )

    messages.success(
        request,
        "Your cart has been updated.",
    )

    return redirect(
        "shop:cart_view"
    )


# ============================================================
# REMOVE FROM CART
# ============================================================

@login_required
def remove_from_cart(request, product_id):
    """
    Remove a product from the shopping cart.
    """

    cart = _get_cart(request)

    product_id = str(
        product_id
    )

    if product_id in cart:

        product_name = cart[
            product_id
        ].get(
            "name",
            "Product",
        )

        del cart[product_id]

        _save_cart(
            request,
            cart,
        )

        messages.success(
            request,
            f"{product_name} has been removed from your cart.",
        )

    else:

        messages.info(
            request,
            "The product was not found in your cart.",
        )

    return redirect(
        "shop:cart_view"
    )


# ============================================================
# CLEAR CART
# ============================================================

@login_required
def clear_cart(request):
    """
    Remove all products from the customer's cart.
    """

    _save_cart(
        request,
        {},
    )

    messages.success(
        request,
        "Your shopping cart has been cleared.",
    )

    return redirect(
        "shop:cart_view"
    )


# ============================================================
# RECENTLY VIEWED PRODUCTS
# ============================================================

def recently_viewed_products(request):
    """
    Display products recently viewed by the customer.
    """

    product_ids = request.session.get(
        "recently_viewed",
        [],
    )

    products = []

    for product_id in product_ids:

        try:

            product = Product.objects.get(
                id=product_id,
            )

            products.append(
                product
            )

        except Product.DoesNotExist:

            continue

    return render(
        request,
        "shop/recently_viewed.html",
        {
            "products": products,
        },
    )


# ============================================================
# RECOMMENDED PRODUCTS
# ============================================================

def recommended_products(request):
    """
    Display recommended products.

    This is the foundation for the future
    Enock Shopping AI recommendation system.
    """

    products = (
        Product.objects
        .order_by("-id")[:24]
    )

    return render(
        request,
        "shop/recommended_products.html",
        {
            "products": products,
        },
    )
