from typing import List, Dict, Any
from django.http import HttpRequest

def get_cart_items(request: HttpRequest) -> List[Dict[str, Any]]:
    """Retrieve cart items stored in the session."""
    return request.session.get('cart', [])

def add_to_cart(request: HttpRequest, product_id: int, quantity: int) -> None:
    """Add items to the cart in the session."""
    cart = get_cart_items(request)

    # Check if the product is already in the cart
    for item in cart:
        if item['product_id'] == product_id:
            item['quantity'] += quantity  # Update quantity if product exists
            break
    else:
        # If the product is not found in the cart, add it
        cart.append({'product_id': product_id, 'quantity': quantity})

    # Update the session cart
    request.session['cart'] = cart

def clear_cart(request: HttpRequest) -> None:
    """Clear the cart from the session."""
    request.session['cart'] = []

def remove_from_cart(request: HttpRequest, product_id: int) -> None:
    """Remove a specific item from the cart."""
    cart = get_cart_items(request)
    # Filter out the item to remove
    cart = [item for item in cart if item['product_id'] != product_id]
    # Update the session cart
    request.session['cart'] = cart

def update_cart_item(request: HttpRequest, product_id: int, quantity: int) -> None:
    """Update the quantity of a specific item in the cart."""
    cart = get_cart_items(request)
    for item in cart:
        if item['product_id'] == product_id:
            if quantity > 0:
                item['quantity'] = quantity  # Update quantity
            else:
                cart.remove(item)  # Remove item if quantity is zero
            break
    # Update the session cart
    request.session['cart'] = cart
from typing import Dict, Any
from django.http import HttpRequest

class Cart:
    def __init__(self, request: HttpRequest):
        self.request = request
        self.cart = self.request.session.get('cart', {})

    def add(self, product_id: int, quantity: int):
        """Add items to the cart."""
        if product_id in self.cart:
            self.cart[product_id] += quantity
        else:
            self.cart[product_id] = quantity
        self.request.session['cart'] = self.cart

    def clear(self):
        """Clear the cart."""
        self.cart = {}
        self.request.session['cart'] = self.cart

    def remove(self, product_id: int):
        """Remove a specific item from the cart."""
        if product_id in self.cart:
            del self.cart[product_id]
        self.request.session['cart'] = self.cart

    # You can add more methods as needed
