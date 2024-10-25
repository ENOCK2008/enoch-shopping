from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify
import paypalrestsdk
from django.core.exceptions import ValidationError

# Configure PayPal
paypalrestsdk.configure({
    "mode": "sandbox",  # Change to "live" in production
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_CLIENT_SECRET
})

# Category Model
class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name="Category Name")
    slug = models.SlugField(max_length=255, unique=True, blank=True, verbose_name="Category Slug")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)  # Automatically generate slug from name
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"

# Product Model
from django.db import models
from django.utils import timezone

class Product(models.Model):
    name = models.CharField(max_length=255, verbose_name="Product Name")
    description = models.TextField(verbose_name="Product Description")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Product Price")
    stock = models.PositiveIntegerField(verbose_name="Stock Quantity")  # Use PositiveIntegerField for stock
    category = models.ForeignKey('Category', on_delete=models.CASCADE, verbose_name="Product Category")  # Use string reference for better readability
    image = models.ImageField(upload_to='products/', null=True, blank=True, verbose_name="Product Image")
    video_url = models.URLField(null=True, blank=True, verbose_name="Product Video URL")
    panoramic_image = models.ImageField(upload_to='products/panoramic/', null=True, blank=True, verbose_name="Panoramic Image")
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0, verbose_name="Product Rating")
    is_recommended = models.BooleanField(default=False, verbose_name="Recommended Product")  # Added verbose name for clarity
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")  # Changed to auto_now_add for creation time
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        ordering = ['-created_at']  # Order products by created_at descending
        verbose_name_plural = "Products"  # Optional: Defines the plural name for the model

    def is_in_stock(self):
        """Returns True if the product is available in stock."""
        return self.stock > 0

    def __str__(self):
        return self.name


    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ['-created_at']

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

# Cart Item Model
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)  # Reference to the Cart model
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # Reference to the Product model
    quantity = models.PositiveIntegerField(default=1)  # Quantity of the product

    def __str__(self):
        return f"{self.product.name} (x{self.quantity})"

# Feedback Model
class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
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
    discount_amount = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    payment_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ], default='pending')
    shipping_address = models.TextField()
    tracking_number = models.CharField(max_length=50, blank=True, null=True)

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
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    push_notifications = models.BooleanField(default=True)
    two_factor_auth = models.BooleanField(default=False)
    newsletter = models.BooleanField(default=False)
    privacy_settings = models.CharField(
        max_length=10,
        choices=[
            ('public', 'Public'),
            ('friends', 'Friends Only'),
            ('private', 'Private')
        ],
        default='public'
    )
    bio = models.TextField(blank=True, null=True)  # Added bio field

    def __str__(self):
        return self.user.username
# Other models...
# Feedback, Loyalty Points, Discount Codes, Order Items, Orders, User Preferences, Music, Profile, etc.

# SMSMessage Model
class SMSMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sms_messages')
    message_content = models.TextField()
    phone_number = models.CharField(max_length=15)  # Adjust length as needed for international numbers
    sent_at = models.DateTimeField(auto_now_add=True)
    delivered = models.BooleanField(default=False)  # To track if the SMS was delivered

    def __str__(self):
        return f"Message to {self.phone_number} at {self.sent_at}: {self.message_content[:20]}..."

# ViewedProduct Model
class ViewedProduct(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} viewed {self.product.name}"

# In this structure, all relationships should work correctly.
class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.DecimalField(max_digits=2, decimal_places=1)  # e.g., 1.0 to 5.0 rating
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Review of {self.product.name} by {self.user.username}'
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message}"
class UserRegistrationStatistic(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    registration_date = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device_info = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} registered on {self.registration_date}"
class PageView(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='page_views')  # Optional user
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='page_views')  # If tracking product views
    timestamp = models.DateTimeField(auto_now_add=True)  # Automatically set the timestamp of the view

    def __str__(self):
        return f"View of {self.product.name} by {self.user.username if self.user else 'Guest'} at {self.timestamp}"
class Offer(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    def is_active(self):
        """Check if the offer is currently active based on dates."""
        now = timezone.now().date()
        return self.active and self.start_date <= now <= self.end_date

class Meta:
        ordering = ['start_date']  # Orders offers by start date by default


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlists')
    products = models.ManyToManyField(Product, blank=True, related_name='wishlists')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Wishlist"


from django.core.exceptions import ValidationError

class LoyaltyPointHistory(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('earned', 'Earned'),
        ('redeemed', 'Redeemed'),
    ]

    REASON_CHOICES = [
        ('reward', 'Reward'),
        ('promotion', 'Promotion'),
        ('referral', 'Referral'),
        ('purchase', 'Purchase'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loyalty_point_history', verbose_name="User")
    points_changed = models.IntegerField(verbose_name="Points Changed")  # Positive for points earned, negative for points redeemed
    reason = models.CharField(max_length=50, choices=REASON_CHOICES, verbose_name="Reason for Change")  # Reason for the points change
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES, verbose_name="Transaction Type")  # Type of transaction
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date Created")  # Timestamp of the change

    class Meta:
        verbose_name = "Loyalty Point History"
        verbose_name_plural = "Loyalty Point Histories"
        ordering = ['-created_at']  # Orders history entries by creation date, most recent first
        indexes = [
            models.Index(fields=['user']),  # Index on user for faster queries
        ]

    def clean(self):
        """Custom validation to ensure points_changed is non-zero and transaction_type is set."""
        # Ensure points_changed is an integer and not zero
        if not isinstance(self.points_changed, int):
            raise ValidationError("Points changed must be an integer.")
        if self.points_changed == 0:
            raise ValidationError("Points changed must be either positive or negative.")
        
        # Ensure transaction_type is specified
        if not self.transaction_type:
            raise ValidationError("Transaction type must be specified.")

        # Check if transaction_type is valid
        if self.transaction_type not in dict(self.TRANSACTION_TYPE_CHOICES):
            raise ValidationError("Invalid transaction type specified.")

    def __str__(self):
        return f"{self.user.username} - {self.points_changed} points ({self.transaction_type}) on {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"

class ReturnRequest(models.Model):
    REASON_CHOICES = [
        ('damaged', 'Damaged Item'),
        ('wrong_item', 'Wrong Item Sent'),
        ('not_satisfied', 'Not Satisfied with the Item'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_id = models.CharField(max_length=100)
    reason = models.CharField(max_length=50, choices=REASON_CHOICES)
    additional_comments = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', 'Pending'),
        ('processed', 'Processed'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ])

    def __str__(self):
        return f'Return request for order {self.order_id} by {self.user.username} - Status: {self.status}'

    class Meta:
        ordering = ['-created_at']
class GiftCard(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    expiration_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Gift Card - ${self.amount}'

    def is_expired(self):
        if self.expiration_date:
            return timezone.now().date() > self.expiration_date
        return False

    class Meta:
        verbose_name = "Gift Card"
        verbose_name_plural = "Gift Cards"
        ordering = ['-created_at']
class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
from django.core.validators import EmailValidator
from django.utils import timezone

class NewsletterSubscription(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    
    email = models.EmailField(unique=True, validators=[EmailValidator()])
    name = models.CharField(max_length=100, blank=True)  # Optional name field
    subscribed_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default='active')  # Subscription status
    frequency = models.CharField(max_length=50, choices=[('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')], default='weekly')  # Frequency of newsletters

    def __str__(self):
        return f"{self.name} <{self.email}>"

    def is_active(self):
        """Check if the subscription is active."""
        return self.status == 'active'

    def unsubscribe(self):
        """Method to unsubscribe the user."""
        self.status = 'inactive'
        self.save()

    def subscribe(self):
        """Method to resubscribe the user."""
        self.status = 'active'
        self.save()

    class Meta:
        verbose_name = "Newsletter Subscription"
        verbose_name_plural = "Newsletter Subscriptions"
        ordering = ['-subscribed_at']  # Order subscriptions by most recent
class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} on {self.product.name}"
class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_user = models.BooleanField(default=True)





