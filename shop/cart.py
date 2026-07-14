from typing import List, Dict, Any, Optional, Tuple
from django.http import HttpRequest
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import datetime, timedelta


class Cart:
    """
    A comprehensive shopping cart implementation with pricing, discounts, and analytics.
    """

    CART_SESSION_KEY = 'cart'
    ABANDONED_CART_KEY = 'abandoned_cart'
    MIN_QUANTITY = 1
    MAX_QUANTITY = 999
    SESSION_TIMEOUT_HOURS = 24

    def __init__(self, request: HttpRequest):
        """Initialize cart from session."""
        self.request = request
        self.cart = self.request.session.get(self.CART_SESSION_KEY, {})
        self.discounts = self.request.session.get('cart_discounts', {})
        self.cart_metadata = self.request.session.get('cart_metadata', {
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'cart_id': self._generate_cart_id()
        })
        
        if not isinstance(self.cart, dict):
            self.cart = {}

    def _generate_cart_id(self) -> str:
        """Generate unique cart ID."""
        import uuid
        return str(uuid.uuid4())

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

    def _validate_price(self, price: Any) -> Decimal:
        """Validate and convert price to Decimal."""
        try:
            price_decimal = Decimal(str(price))
            if price_decimal < 0:
                raise ValidationError("Price cannot be negative.")
            return price_decimal
        except:
            raise ValidationError("Invalid price format. Must be a number.")

    def _save_cart(self) -> None:
        """Save cart to session and mark it as modified."""
        self.request.session[self.CART_SESSION_KEY] = self.cart
        self.request.session['cart_discounts'] = self.discounts
        self.cart_metadata['last_updated'] = datetime.now().isoformat()
        self.request.session['cart_metadata'] = self.cart_metadata
        self.request.session.modified = True

    # ==================== CORE CART OPERATIONS ====================

    def add(self, product_id: int, quantity: int = 1, product_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Add item to cart with optional product details.
        
        Args:
            product_id: Product identifier
            quantity: Quantity to add (default: 1)
            product_data: Dict with 'name', 'price', 'image_url', 'stock' (optional)
            
        Returns:
            Dictionary with success status and updated quantity
        """
        self._validate_product_id(product_id)
        self._validate_quantity(quantity)

        product_id_str = str(product_id)
        
        # Validate stock if provided
        if product_data and 'stock' in product_data:
            if product_data['stock'] <= 0:
                return {
                    'success': False,
                    'message': f"{product_data.get('name', 'Product')} is out of stock"
                }
            if product_data['stock'] < quantity:
                return {
                    'success': False,
                    'message': f"Only {product_data['stock']} items available"
                }

        if product_id_str in self.cart:
            new_quantity = self.cart[product_id_str]['quantity'] + quantity
            if new_quantity > self.MAX_QUANTITY:
                self.cart[product_id_str]['quantity'] = self.MAX_QUANTITY
            else:
                self.cart[product_id_str]['quantity'] = new_quantity
        else:
            self.cart[product_id_str] = {
                'quantity': quantity,
                'product_data': product_data or {}
            }

        self._save_cart()
        return {
            'success': True,
            'product_id': product_id,
            'quantity': self.cart[product_id_str]['quantity'],
            'message': 'Product added to cart'
        }

    def remove(self, product_id: int) -> Dict[str, Any]:
        """Remove a specific item from cart."""
        self._validate_product_id(product_id)
        product_id_str = str(product_id)

        if product_id_str in self.cart:
            del self.cart[product_id_str]
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
        """Update quantity of a specific item."""
        self._validate_product_id(product_id)
        product_id_str = str(product_id)

        if product_id_str not in self.cart:
            return {
                'success': False,
                'message': 'Product not found in cart'
            }

        if quantity <= 0:
            return self.remove(product_id)

        self._validate_quantity(quantity)
        self.cart[product_id_str]['quantity'] = quantity
        self._save_cart()

        return {
            'success': True,
            'product_id': product_id,
            'quantity': quantity,
            'message': 'Cart updated'
        }

    def clear(self) -> Dict[str, Any]:
        """Clear the entire cart."""
        self.cart = {}
        self.discounts = {}
        self._save_cart()
        return {
            'success': True,
            'message': 'Cart cleared'
        }

    # ==================== PRICING & CALCULATIONS ====================

    def get_item_subtotal(self, product_id: int) -> Decimal:
        """Calculate subtotal for a single item."""
        product_id_str = str(product_id)
        if product_id_str not in self.cart:
            return Decimal('0')
        
        item = self.cart[product_id_str]
        price = self._validate_price(item['product_data'].get('price', 0))
        return price * item['quantity']

    def get_subtotal(self) -> Decimal:
        """Calculate cart subtotal (before tax and shipping)."""
        total = Decimal('0')
        for product_id_str, item in self.cart.items():
            price = self._validate_price(item['product_data'].get('price', 0))
            total += price * item['quantity']
        return total

    def get_total_discount(self) -> Decimal:
        """Calculate total discount from all applied coupons."""
        return sum(
            self._validate_price(discount.get('amount', 0)) 
            for discount in self.discounts.values()
        )

    def get_total_with_tax_shipping(self, tax_rate: Decimal = Decimal('0.1'), 
                                    shipping_cost: Decimal = Decimal('0')) -> Dict[str, Decimal]:
        """
        Calculate cart total with tax and shipping.
        
        Args:
            tax_rate: Tax rate as decimal (0.1 = 10%)
            shipping_cost: Shipping cost
            
        Returns:
            Dict with subtotal, discount, tax, shipping, and total
        """
        subtotal = self.get_subtotal()
        discount = self.get_total_discount()
        after_discount = subtotal - discount
        tax = after_discount * self._validate_price(tax_rate)
        final_total = after_discount + tax + self._validate_price(shipping_cost)

        return {
            'subtotal': subtotal,
            'discount': discount,
            'after_discount': after_discount,
            'tax': tax,
            'shipping': self._validate_price(shipping_cost),
            'total': final_total
        }

    # ==================== DISCOUNT/COUPON SYSTEM ====================

    def apply_discount(self, code: str, discount_type: str = 'percentage', 
                      amount: Decimal = Decimal('0')) -> Dict[str, Any]:
        """
        Apply a discount code to cart.
        
        Args:
            code: Coupon code
            discount_type: 'percentage' or 'fixed'
            amount: Discount amount/percentage
            
        Returns:
            Dictionary with success status and discount details
        """
        if not code or not isinstance(code, str):
            return {
                'success': False,
                'message': 'Invalid coupon code'
            }

        code = code.upper().strip()
        amount = self._validate_price(amount)

        if discount_type == 'percentage':
            if amount > 100 or amount <= 0:
                return {
                    'success': False,
                    'message': 'Percentage must be between 1 and 100'
                }
            discount_value = self.get_subtotal() * (amount / 100)
        elif discount_type == 'fixed':
            discount_value = amount
        else:
            return {
                'success': False,
                'message': 'Invalid discount type'
            }

        self.discounts[code] = {
            'type': discount_type,
            'amount': discount_value,
            'original_amount': amount,
            'applied_at': datetime.now().isoformat()
        }
        self._save_cart()

        return {
            'success': True,
            'code': code,
            'discount_amount': discount_value,
            'message': f'Coupon {code} applied successfully'
        }

    def remove_discount(self, code: str) -> Dict[str, Any]:
        """Remove a discount code."""
        code = code.upper().strip()
        if code in self.discounts:
            del self.discounts[code]
            self._save_cart()
            return {
                'success': True,
                'message': f'Coupon {code} removed'
            }
        return {
            'success': False,
            'message': 'Coupon not found'
        }

    def get_applied_discounts(self) -> List[Dict[str, Any]]:
        """Get all applied discount codes."""
        return [
            {
                'code': code,
                **discount
            }
            for code, discount in self.discounts.items()
        ]

    # ==================== INVENTORY/STOCK VALIDATION ====================

    def validate_stock(self) -> Tuple[bool, str]:
        """
        Validate that all items in cart have sufficient stock.
        
        Returns:
            Tuple of (is_valid, message)
        """
        for product_id_str, item in self.cart.items():
            stock = item['product_data'].get('stock')
            if stock is not None and item['quantity'] > stock:
                name = item['product_data'].get('name', f'Product {product_id_str}')
                return (False, f"{name} has insufficient stock. Available: {stock}, Requested: {item['quantity']}")
        
        return (True, 'All items in stock')

    def check_product_availability(self, product_id: int) -> Dict[str, Any]:
        """Check availability of a product in cart."""
        product_id_str = str(product_id)
        if product_id_str not in self.cart:
            return {
                'in_cart': False,
                'message': 'Product not in cart'
            }
        
        item = self.cart[product_id_str]
        stock = item['product_data'].get('stock')
        
        return {
            'in_cart': True,
            'quantity': item['quantity'],
            'stock_available': stock,
            'available': stock is None or item['quantity'] <= stock
        }

    # ==================== CART INFO & RETRIEVAL ====================

    def get_items(self) -> List[Dict[str, Any]]:
        """Get all cart items with complete details."""
        return [
            {
                'product_id': int(product_id),
                'quantity': item['quantity'],
                'product_data': item['product_data'],
                'subtotal': self.get_item_subtotal(int(product_id))
            }
            for product_id, item in self.cart.items()
        ]

    def get_item(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get details of a specific item."""
        product_id_str = str(product_id)
        if product_id_str not in self.cart:
            return None
        
        item = self.cart[product_id_str]
        return {
            'product_id': product_id,
            'quantity': item['quantity'],
            'product_data': item['product_data'],
            'subtotal': self.get_item_subtotal(product_id)
        }

    def get_total_items(self) -> int:
        """Get total number of items (sum of quantities)."""
        return sum(item['quantity'] for item in self.cart.values())

    def get_item_count(self) -> int:
        """Get number of unique products in cart."""
        return len(self.cart)

    def get_cart_summary(self) -> Dict[str, Any]:
        """Get complete cart summary."""
        summary = self.get_total_with_tax_shipping()
        is_valid, stock_msg = self.validate_stock()
        
        return {
            'items': self.get_items(),
            'item_count': self.get_item_count(),
            'total_quantity': self.get_total_items(),
            'discounts': self.get_applied_discounts(),
            'pricing': summary,
            'stock_valid': is_valid,
            'stock_message': stock_msg,
            'cart_id': self.cart_metadata['cart_id'],
            'created_at': self.cart_metadata['created_at'],
            'last_updated': self.cart_metadata['last_updated']
        }

    # ==================== CART STATE CHECKS ====================

    def is_empty(self) -> bool:
        """Check if cart is empty."""
        return len(self.cart) == 0

    def contains(self, product_id: int) -> bool:
        """Check if a product is in the cart."""
        self._validate_product_id(product_id)
        return str(product_id) in self.cart

    # ==================== BULK OPERATIONS ====================

    def add_multiple(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Add multiple items to cart at once.
        
        Args:
            items: List of dicts with 'product_id', 'quantity', 'product_data' (optional)
            
        Returns:
            Dict with results for each item
        """
        results = []
        for item in items:
            result = self.add(
                item['product_id'],
                item.get('quantity', 1),
                item.get('product_data')
            )
            results.append(result)
        
        return {
            'success': all(r['success'] for r in results),
            'results': results,
            'message': f'Added {len([r for r in results if r["success"]])} items'
        }

    def merge_cart(self, other_cart_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge another cart into this one (useful for guest to user conversion).
        
        Args:
            other_cart_items: Items from another cart
            
        Returns:
            Dict with merge results
        """
        return self.add_multiple(other_cart_items)

    # ==================== CART EXPORT & PERSISTENCE ====================

    def export_to_dict(self) -> Dict[str, Any]:
        """Export complete cart as dictionary."""
        return {
            'cart': self.cart,
            'discounts': self.discounts,
            'metadata': self.cart_metadata,
            'summary': self.get_cart_summary()
        }

    def export_to_json(self) -> str:
        """Export cart as JSON string."""
        import json
        data = self.export_to_dict()
        # Convert Decimal to string for JSON serialization
        return json.dumps(data, default=str)

    def save_as_abandoned(self) -> Dict[str, Any]:
        """Save current cart as abandoned cart for recovery."""
        abandoned_data = {
            'cart_id': self.cart_metadata['cart_id'],
            'cart_data': self.export_to_dict(),
            'abandoned_at': datetime.now().isoformat(),
            'recovery_url': f'/cart/recover/{self.cart_metadata["cart_id"]}'
        }
        self.request.session[self.ABANDONED_CART_KEY] = abandoned_data
        self.request.session.modified = True
        
        return {
            'success': True,
            'message': 'Cart saved for recovery',
            'recovery_url': abandoned_data['recovery_url']
        }

    def restore_from_dict(self, cart_data: Dict[str, Any]) -> Dict[str, Any]:
        """Restore cart from exported dictionary."""
        try:
            self.cart = cart_data.get('cart', {})
            self.discounts = cart_data.get('discounts', {})
            self._save_cart()
            return {
                'success': True,
                'message': 'Cart restored successfully'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to restore cart: {str(e)}'
            }

    # ==================== ANALYTICS & STATISTICS ====================

    def get_cart_analytics(self) -> Dict[str, Any]:
        """Get cart analytics and statistics."""
        items = self.get_items()
        prices = [item['subtotal'] for item in items]
        
        return {
            'total_items': self.get_total_items(),
            'unique_products': self.get_item_count(),
            'subtotal': self.get_subtotal(),
            'total_discount': self.get_total_discount(),
            'average_item_price': sum(prices) / len(prices) if prices else Decimal('0'),
            'highest_priced_item': max(prices) if prices else Decimal('0'),
            'lowest_priced_item': min(prices) if prices else Decimal('0'),
            'cart_id': self.cart_metadata['cart_id'],
            'age_hours': self._get_cart_age_hours()
        }

    def _get_cart_age_hours(self) -> float:
        """Get cart age in hours."""
        created = datetime.fromisoformat(self.cart_metadata['created_at'])
        return (datetime.now() - created).total_seconds() / 3600

    def is_abandoned(self, hours: int = 24) -> bool:
        """Check if cart is abandoned (no updates in X hours)."""
        return self._get_cart_age_hours() > hours

    # ==================== ORDER CONVERSION ====================

    def convert_to_order(self, tax_rate: Decimal = Decimal('0.1'), 
                        shipping_cost: Decimal = Decimal('0')) -> Dict[str, Any]:
        """
        Convert cart to order snapshot.
        
        Returns:
            Complete order data ready for processing
        """
        is_valid, stock_msg = self.validate_stock()
        if not is_valid:
            return {
                'success': False,
                'message': f'Cannot create order: {stock_msg}'
            }

        pricing = self.get_total_with_tax_shipping(tax_rate, shipping_cost)
        
        return {
            'success': True,
            'order': {
                'order_id': self.cart_metadata['cart_id'],
                'items': self.get_items(),
                'pricing': pricing,
                'discounts_applied': self.get_applied_discounts(),
                'created_at': datetime.now().isoformat(),
                'status': 'pending'
            }
        }

    # ==================== MAGIC METHODS ====================

    def __len__(self) -> int:
        """Return number of unique products."""
        return self.get_item_count()

    def __iter__(self):
        """Iterate over cart items."""
        return iter(self.get_items())

    def __repr__(self) -> str:
        """String representation of cart."""
        return f"Cart(items={self.get_item_count()}, total_qty={self.get_total_items()}, total={self.get_subtotal()})"

    def __bool__(self) -> bool:
        """Cart is truthy if not empty."""
        return not self.is_empty()


# ==================== BACKWARD COMPATIBILITY FUNCTIONS ====================

def get_cart(request: HttpRequest) -> Cart:
    """Get cart instance for the request."""
    return Cart(request)


def get_cart_items(request: HttpRequest) -> List[Dict[str, Any]]:
    """Retrieve cart items (functional API)."""
    return get_cart(request).get_items()


def add_to_cart(request: HttpRequest, product_id: int, quantity: int = 1, 
                product_data: Optional[Dict] = None) -> Dict[str, Any]:
    """Add items to the cart (functional API)."""
    return get_cart(request).add(product_id, quantity, product_data)


def remove_from_cart(request: HttpRequest, product_id: int) -> Dict[str, Any]:
    """Remove a specific item from the cart (functional API)."""
    return get_cart(request).remove(product_id)


def update_cart_item(request: HttpRequest, product_id: int, quantity: int) -> Dict[str, Any]:
    """Update the quantity of a specific item (functional API)."""
    return get_cart(request).update(product_id, quantity)


def clear_cart(request: HttpRequest) -> Dict[str, Any]:
    """Clear the cart (functional API)."""
    return get_cart(request).clear()


def get_cart_summary(request: HttpRequest) -> Dict[str, Any]:
    """Get complete cart summary (functional API)."""
    return get_cart(request).get_cart_summary()
