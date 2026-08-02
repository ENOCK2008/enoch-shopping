from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Product


@login_required
def add_to_cart(request, product_id):
    """Add a product to the user's cart."""
    try:
        product = get_object_or_404(Product, id=product_id)
    except:
        messages.error(request, f"Product with ID {product_id} does not exist. Please check the product ID.")
        return redirect('shop:shop')

    if product.stock <= 0:
        messages.warning(request, "Sorry, this product is out of stock.")
        return redirect('shop:product_detail', product_id=product.id)

    cart = request.session.get('cart', {})

    if str(product_id) in cart:
        cart[str(product_id)]['quantity'] += 1
    else:
        cart[str(product_id)] = {
            'name': product.name,
            'price': str(product.price),
            'quantity': 1,
        }

    request.session['cart'] = cart

    messages.success(request, f"{product.name} has been added to your cart.")
    return redirect('shop:cart_view')
