```python
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

from .models import Product


def shop(request):
    products = Product.objects.all()

    return render(
        request,
        "shop/shop.html",
        {
            "products": products,
        }
    )


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    return render(
        request,
        "shop/product_detail.html",
        {
            "product": product,
        }
    )


def search(request):
    query = request.GET.get("q", "").strip()

    products = Product.objects.all()

    if query:
        products = products.filter(
            Q(name__icontains=query)
        )

    return render(
        request,
        "shop/search.html",
        {
            "products": products,
            "query": query,
        }
    )


@login_required
def add_to_cart(request, product_id):
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

    product_id = str(product_id)

    if product_id in cart:
        cart[product_id]["quantity"] += 1
    else:
        cart[product_id] = {
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
    cart = request.session.get("cart", {})

    cart_items = []
    total = 0

    for product_id, item in cart.items():

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            continue

        quantity = int(item.get("quantity", 1))
        price = float(product.price)
        subtotal = price * quantity

        cart_items.append(
            {
                "product": product,
                "quantity": quantity,
                "price": price,
                "subtotal": subtotal,
            }
        )

        total += subtotal

    return render(
        request,
        "shop/cart.html",
        {
            "cart_items": cart_items,
            "total": total,
        }
    )


@login_required
def remove_from_cart(request, product_id):
    cart = request.session.get("cart", {})

    product_id = str(product_id)

    if product_id in cart:
        del cart[product_id]

    request.session["cart"] = cart
    request.session.modified = True

    messages.success(
        request,
        "Product removed from your cart."
    )

    return redirect("shop:cart_view")


@login_required
def clear_cart(request):
    request.session["cart"] = {}
    request.session.modified = True

    messages.success(
        request,
        "Your cart has been cleared."
    )

    return redirect("shop:cart_view")
```
