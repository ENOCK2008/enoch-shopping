from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify
import paypalrestsdk

# Configure PayPal
paypalrestsdk.configure({
    "mode": "sandbox",  # Change to "live" in production
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_CLIENT_SECRET
})

class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name="Category Name")
    slug = models.SlugField(max_length=255, unique=True, blank=True, verbose_name="Category Slug")  # For SEO-friendly URLs

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)  # Automatically generate slug from name
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"

class Product(models.Model):
    name = models.CharField(max_length=255, verbose_name="Product Name")
    description = models.TextField(verbose_name="Product Description")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Product Price")
    stock = models.IntegerField(verbose_name="Stock Quantity")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Product Category")
    image = models.ImageField(upload_to='products/', null=True, blank=True, verbose_name="Product Image")
    video_url = models.URLField(null=True, blank=True, verbose_name="Product Video URL")
    panoramic_image = models.ImageField(upload_to='products/panoramic/', null=True, blank=True, verbose_name="Panoramic Image")
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0, verbose_name="Product Rating")
    is_recommended = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Created At")  # Default value set
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")      # Timestamp when product is updated

    def is_in_stock(self):
        """Returns True if the product is available in stock."""
        return self.stock > 0

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ['-created_at']  # Orders products by creation date, most recent first# Feedback Model
class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()  # Use 'content' to match with the form
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Feedback from {self.user.username} on {self.created_at}'

# Loyalty Points Model
class LoyaltyPoints(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    points = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f'{self.user.username} - {self.points} points'

# Discount Code Model
class DiscountCode(models.Model):
    code = models.CharField(max_length=50)
    discount_amount = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # Optional field
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.code

# Order Item Model
class OrderItem(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Price at Purchase")

    def __str__(self):
        return f"{self.product.name} - Quantity: {self.quantity}"

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"

# Order Model
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)  # Automatically set when the order is created
    updated_at = models.DateTimeField(auto_now=True)  # Automatically set when the order is updated
    payment_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ], default='pending')
    shipping_address = models.TextField()  # You can use a separate model for addresses if needed
    tracking_number = models.CharField(max_length=50, blank=True, null=True)  # For shipment tracking

    def __str__(self):
        return f"Order #{self.id} by {self.user.username} - Total: {self.total_price}"

# User Preferences Model
class UserPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    preferred_categories = models.ManyToManyField(Category, blank=True)
    recommended_products = models.ManyToManyField(Product, blank=True)

    def __str__(self):
        return f'{self.user.username} Preferences'

# Music Model
class Music(models.Model):
    title = models.CharField(max_length=255)
    artist = models.CharField(max_length=255, default='Unknown Artist')
    album = models.CharField(max_length=255, default='Unknown Album')
    audio_file = models.FileField(upload_to='audio/')
    video_file = models.FileField(upload_to='videos/', blank=True, null=True)
    cover_image = models.ImageField(upload_to='covers/', blank=True, null=True)

    def __str__(self):
        return self.title

# Profile Model
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True, default='profile_pictures/default.jpg')

    def __str__(self):
        return f'{self.user.username} Profile'

# Cart Item Model
class CartItem(models.Model):
    cart = models.ForeignKey('Cart', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product.name} - Quantity: {self.quantity}"

    class Meta:
        verbose_name = "Cart Item"
        verbose_name_plural = "Cart Items"

# Cart Model
class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="User")
    items = models.ManyToManyField(Product, through='CartItem', blank=True, verbose_name="Items in Cart")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")

    def __str__(self):
        return f"Cart of {self.user.username}"

    class Meta:
        verbose_name = "Cart"
        verbose_name_plural = "Carts"

# Review Model
class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews', verbose_name="Product")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="User")
    rating = models.IntegerField(verbose_name="Rating")
    comment = models.TextField(verbose_name="Comment")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")

    def __str__(self):
        return f"Review by {self.user.username} on {self.product.name}"

    class Meta:
        verbose_name = "Review"
        verbose_name_plural = "Reviews"

# Notification Model
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message[:20]}"

# Menu Item Model
class MenuItem(models.Model):
    name = models.CharField(max_length=100)
    url_name = models.CharField(max_length=100)  # Name of the URL pattern

    def __str__(self):
        return self.name

# Product Rating Model
class ProductRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    rating = models.IntegerField(default= 1-5)  # Simple rating scale 1-5
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} rated {self.product.name} - {self.rating}'

# Chat Message Model
class ChatMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages')
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Message from {self.sender.username} to {self.recipient.username}'

# Order Tracking Model
class OrderTracking(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    status = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Tracking for Order #{self.order.id} - Status: {self.status}"

# SMS Message Model
class SMSMessage(models.Model):
    recipient = models.CharField(max_length=15)  # Phone number
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'SMS to {self.recipient} - Sent at {self.sent_at}'

# Payment Model
class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ])
    payment_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment of {self.amount} for Order #{self.order.id} by {self.user.username}"

# Address Model
class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    street_address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.street_address}, {self.city}, {self.country}"

# Discounted Product Model
class DiscountedProduct(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    discount_code = models.ForeignKey(DiscountCode, on_delete=models.CASCADE)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} - Discounted Price: {self.discount_price}"
class UserRegistrationStatistic(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    registration_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Registration Stats for {self.user.username}"
class PageView(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    view_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.product.name} viewed by {self.user.username if self.user else 'Anonymous'}"

class ViewedProduct(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product') 
class Message(models.Model):
    content = models.TextField()  # Content of the message
    room_name = models.CharField(max_length=100)  # Name of the chat room
    timestamp = models.DateTimeField(auto_now_add=True)  # Time when the message was created

    def __str__(self):
        return f"{self.content[:20]}... at {self.timestamp}"  # String representation of the message
class Offer(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user}'s Wishlist"

class WishlistProduct(models.Model):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE)
    product = models.ForeignKey('Product', on_delete=models.CASCADE)  # Assuming you have a Product model

    def __str__(self):
        return f"{self.product.name} in {self.wishlist.user}'s Wishlist"

