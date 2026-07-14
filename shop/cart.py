from typing import List, Dict, Any, Optional
from django.http import HttpRequest
from django.core.exceptions import ValidationError


class Cart:
    """
    A robust shopping cart implementation using Django sessions.
    Handles product management with validation and performance optimization.
    """

    CART_SESSION_KEY = 'cart'
    MIN_QUANTITY = 1
    MAX_QUANTITY = 999

    def __init__(self, request: HttpRequest):
        """Initialize cart from session."""
        self.request = request
        self.cart = self.request.session.get(self.CART_SESSION_KEY, {})
        if not isinstance(self.cart, dict):
            self.cart = {}

    def _validate_product_id(self, product_id: int) -> None:
        """Validate product ID."""
        if not isinstance(product_id, int) or product_id <= 0:
            raise ValidationError("Invalid product ID. Must be a positive integer.")

    def _validate_quantity(self, quantity: int) -> None:
        """Validate quantity."""
        if not isinstance(quantity, int):
            raise ValidationError("Quantity must be an integer.")
        if quantity < self.MIN_QUANTITY or quantity > self.MAX_QUANTITY:
            raise ValidationError(
                f"Quantity must be between {self.MIN_QUANTITY} and {self.MAX_QUANTITY}."
            )

    def _save_cart(self) -> None:
        """Save cart to session and mark it as modified."""
        self.request.session[self.CART_SESSION_KEY] = self.cart
        self.request.session.modified = True

    def add(self, product_id: int, quantity: int = 1) -> Dict[str, Any]:
        """
        Add item to cart or update quantity if already exists.
        
        Args:
            product_id: Product identifier
            quantity: Quantity to add (default: 1)
            
        Returns:
            Dictionary with success status and updated quantity
            
        Raises:
            ValidationError: If product_id or quantity is invalid
        """
        self._validate_product_id(product_id)
        self._validate_quantity(quantity)

        product_id = str(product_id)  # Use string keys for JSON compatibility
        
        if product_id in self.cart:
            new_quantity = self.cart[product_id] + quantity
            if new_quantity > self.MAX_QUANTITY:
                self.cart[product_id] = self.MAX_QUANTITY
            else:
                self.cart[product_id] = new_quantity
        else:
            self.cart[product_id] = quantity

        self._save_cart()
        return {
            'success': True,
            'product_id': product_id,
            'quantity': self.cart[product_id],
            'message': 'Product added to cart'
        }

    def remove(self, product_id: int) -> Dict[str, Any]:
        """
        Remove a specific item from cart.
        
        Args:
            product_id: Product identifier
            
        Returns:
            Dictionary with success status
            
        Raises:
            ValidationError: If product_id is invalid
        """
        self._validate_product_id(product_id)
        product_id = str(product_id)

        if product_id in self.cart:
            del self.cart[product_id]
            self._save_cart()
            return {
                'success': True,
                'message': 'Product removed from cart'
            }
        
        return {
            'success': False,
            'message': 'Product not found in cart'
        }

    def update(self, product_id: int, quantity: int) -> Dict[str, Any]:
        """
        Update quantity of a specific item.
        
        Args:
            product_id: Product identifier
            quantity: New quantity (0 to remove)
            
        Returns:
            Dictionary with success status and updated quantity
            
        Raises:
            ValidationError: If product_id or quantity is invalid
        """
        self._validate_product_id(product_id)
        product_id = str(product_id)

        if product_id not in self.cart:
            return {
                'success': False,
                'message': 'Product not found in cart'
            }

        if quantity <= 0:
            return self.remove(int(product_id))

        self._validate_quantity(quantity)
        self.cart[product_id] = quantity
        self._save_cart()

        return {
            'success': True,
            'product_id': product_id,
            'quantity': quantity,
            'message': 'Cart updated'
        }

    def get_items(self) -> List[Dict[str, Any]]:
        """
        Get all cart items as a list.
        
        Returns:
            List of dictionaries with product_id and quantity
        """
        return [
            {'product_id': int(product_id), 'quantity': qty}
            for product_id, qty in self.cart.items()
        ]

    def get_item(self, product_id: int) -> Optional[int]:
        """
        Get quantity of a specific item.
        
        Args:
            product_id: Product identifier
            
        Returns:
            Quantity if found, None otherwise
        """
        self._validate_product_id(product_id)
        return self.cart.get(str(product_id))

    def get_total_items(self) -> int:
        """Get total number of items (sum of quantities)."""
        return sum(self.cart.values())

    def get_item_count(self) -> int:
        """Get number of unique products in cart."""
        return len(self.cart)

    def clear(self) -> Dict[str, Any]:
        """
        Clear the entire cart.
        
        Returns:
            Dictionary with success status
        """
        self.cart = {}
        self._save_cart()
        return {
            'success': True,
            'message': 'Cart cleared'
        }

    def is_empty(self) -> bool:
        """Check if cart is empty."""
        return len(self.cart) == 0

    def contains(self, product_id: int) -> bool:
        """Check if a product is in the cart."""
        self._validate_product_id(product_id)
        return str(product_id) in self.cart

    def __len__(self) -> int:
        """Return number of unique products."""
        return self.get_item_count()

    def __iter__(self):
        """Iterate over cart items."""
        return iter(self.get_items())

    def __repr__(self) -> str:
        """String representation of cart."""
        return f"Cart(items={self.get_item_count()}, total_qty={self.get_total_items()})"


# Backward compatibility: Functional API wrapper
def get_cart(request: HttpRequest) -> Cart:
    """Get cart instance for the request."""
    return Cart(request)


def get_cart_items(request: HttpRequest) -> List[Dict[str, Any]]:
    """Retrieve cart items (functional API)."""
    return get_cart(request).get_items()


def add_to_cart(request: HttpRequest, product_id: int, quantity: int = 1) -> Dict[str, Any]:
    """Add items to the cart (functional API)."""
    return get_cart(request).add(product_id, quantity)


def remove_from_cart(request: HttpRequest, product_id: int) -> Dict[str, Any]:
    """Remove a specific item from the cart (functional API)."""
    return get_cart(request).remove(product_id)


def update_cart_item(request: HttpRequest, product_id: int, quantity: int) -> Dict[str, Any]:
    """Update the quantity of a specific item (functional API)."""
    return get_cart(request).update(product_id, quantity)


def clear_cart(request: HttpRequest) -> Dict[str, Any]:
    """Clear the cart (functional API)."""
    return get_cart(request).clear()
