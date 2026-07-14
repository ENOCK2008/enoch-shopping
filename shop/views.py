@login_required
def add_to_cart(request, product_id):
    """Add a product to the user's cart."""
    try:
        product = get_object_or_404(Product, id=product_id)
    except:
        messages.error(request, f"Product with ID {product_id} does not exist. Please check the product ID.")
        return redirect('shop:shop')  # Redirect to shop page

    if product.stock <= 0:
        messages.warning(request, "Sorry, this product is out of stock.")
        return redirect('shop:product_detail', product_id=product.id)

    # Retrieve the cart from the session
    cart = request.session.get('cart', {})

    # Update cart
    if product_id in cart:
        cart[product_id]['quantity'] += 1
    else:
        cart[product_id] = {
            'name': product.name,
            'price': str(product.price),
            'quantity': 1,
        }

    request.session['cart'] = cart  # Save the updated cart to the session

    messages.success(request, f"{product.name} has been added to your cart.")
    return redirect('shop:cart_view')
