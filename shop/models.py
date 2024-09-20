from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
import paypalrestsdk

# Configure PayPal
paypalrestsdk.configure({
    "mode": "sandbox",  # Change to "live" in production
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_CLIENT_SECRET
})

# Feedback Model
class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Feedback from {self.user.username} on {self.created_at}'

# LoyaltyPoints Model
class LoyaltyPoints(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    points = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f'{self.user.username} - {self.points} points'

# DiscountCode Model
class DiscountCode(models.Model):
    code = models.CharField(max_length=20, unique=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.code

# Category Model
class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name="Category Name")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"

# Product Model
class Product(models.Model):
    name = models.CharField(max_length=255, verbose_name="Product Name")
    description = models.TextField(verbose_name="Product Description")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Product Price")
    stock = models.IntegerField(verbose_name="Stock Quantity")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Product Category")
    image = models.ImageField(upload_to='products/', null=True, blank=True, verbose_name="Product Image")
    video_url = models.URLField(null=True, blank=True, verbose_name="Product Video URL")
    panoramic_image = models.ImageField(upload_to='products/panoramic/', null=True, blank=True, verbose_name="Panoramic Image")
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0, verbose_name="Product Rating")  # Rating field added

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"

# OrderItem Model
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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="User")
    products = models.ManyToManyField(Product, through='OrderItem', verbose_name="Products")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total Price")
    status = models.CharField(max_length=50, default='Pending', verbose_name="Order Status")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")

    def __str__(self):
        return f"Order {self.id} - {self.user.username}"

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"

# User Preferences Model
class UserPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    preferred_categories = models.ManyToManyField(Category, blank=True)
    recommended_products = models.ManyToManyField(Product, blank=True)

    def __str__(self):
        return f'{self.user.username} Preferences'

# Music Model
class Music(models.Model):
    title = models.CharField(max_length=200)
    audio_file = models.FileField(upload_to='music/')
    cover_image = models.ImageField(upload_to='music_covers/', null=True, blank=True)

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

# CartItem Model
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
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Notification for {self.user.username} on {self.created_at}'

# MenuItem Model
class MenuItem(models.Model):
    name = models.CharField(max_length=100)
    url_name = models.CharField(max_length=100)  # Name of the URL pattern

    def __str__(self):
        return self.name

# ProductRating Model
class ProductRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    rating = models.IntegerField(default=0)  # Simple rating scale 1-5
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} rated {self.product.name} - {self.rating}'
