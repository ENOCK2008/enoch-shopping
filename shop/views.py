```python
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

from .models import Product


def shop(request):
    """Display all products."""
    products = Product.objects.all()

    return render(request, "shop/shop.html", {
        "products": products,
    })


def product_detail(request, product_id):
    """Display a single product."""
    product = get_object_or_404(Product, id=product_id)

    return render(request, "shop/product_detail.html", {
        "product": product,
    })


def search(request):
    """Search products by name and description."""
    query = request.GET.get("q", "").strip()

    products = Product.objects.all()

    if query:
        filters = Q(name__icontains=query)

        # Only use description if your Product model has this field.
        try:
            filters |= Q(description__icontains=query)
        except Exception:
            pass

        products = products.filter(filters)

    return render(request, "shop/search.html", {
        "products": products,
        "query": query,
    })


@login_required
def add_to_cart(request, product_id):
    """Add a product to the user's cart."""
    product = get_object_or_404(Product, id=product_id)

    if product.stock <= 0:
        messages.warning(
            request,
            "Sorry, this product is out of stock."
        )
        return redirect(
            "shop:product_detail",
            product_id=product.id
        )

    cart = request.session.get("cart", {})

    product_key = str(product_id)

    if product_key in cart:
        cart[product_key]["quantity"] += 1
    else:
        cart[product_key] = {
            "name": product.name,
            "price": str(product.price),
            "quantity": 1,
        }

    request.session["cart"] = cart
    request.session.modified = True

    messages.success(
        request,
        f"{product.name} has been added to your cart."
    )

    return redirect("shop:cart_view")


@login_required
def cart_view(request):
    """Display the user's shopping cart."""
    cart = request.session.get("cart", {})

    cart_items = []
    total = 0

    for product_id, item in cart.items():
        try:
            product = Product.objects.get(id=product_id)

            quantity = int(item.get("quantity", 1))
            price = float(product.price)
            subtotal = price * quantity

            cart_items.append({
                "product": product,
                "quantity": quantity,
                "price": price,
                "subtotal": subtotal,
            })

            total += subtotal

        except Product.DoesNotExist:
            continue

    return render(request, "shop/cart.html", {
        "cart_items": cart_items,
        "total": total,
    })


@login_required
def remove_from_cart(request, product_id):
    """Remove a product from the cart."""
    cart = request.session.get("cart", {})

    product_key = str(product_id)

    if product_key in cart:
        del cart[product_key]

    request.session["cart"] = cart
    request.session.modified = True

    messages.success(request, "Product removed from your cart.")

    return redirect("shop:cart_view")


@login_required
def clear_cart(request):
    """Remove all products from the cart."""
    request.session["cart"] = {}
    request.session.modified = True

    messages.success(request, "Your cart has been cleared.")

    return redirect("shop:cart_view")
```

## `shop/urls.py`

Replace the current contents with:

```python
from django.urls import path

from . import views


app_name = "shop"


urlpatterns = [
    path("", views.shop, name="shop"),

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

    path(
        "cart/",
        views.cart_view,
        name="cart_view",
    ),

    path(
        "cart/add/<int:product_id>/",
        views.add_to_cart,
        name="add_to_cart",
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
]
```

### The important change

Your old code had:

```python
from .views import SearchView
```

but there was no `SearchView`.

The new code uses:

```python
from . import views
```

and:

```python
path("search/", views.search, name="search")
```

So the specific `ImportError` that Render reported is removed.

**Before deploying**, send me your current **`shop/models.py`**. I can then build the rest of the shopping app around your actual Product model instead of guessing its fields.
