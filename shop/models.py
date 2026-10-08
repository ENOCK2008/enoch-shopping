from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
import paypalrestsdk
from .models import User  # Import the custom User model
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.views.generic import ListView
from django.views.generic import DetailView
# Configure PayPal
paypalrestsdk.configure({
    "mode": "sandbox",  # Change to "live" in production
    "client_id": "your_client_id",  # Set your PayPal client ID
    "client_secret": "your_client_secret"  # Set your PayPal client secret
})

# shop/models.py
class Category(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Reference to the custom User model
    name = models.CharField(max_length=255, verbose_name="Category Name")
    slug = models.SlugField(max_length=255, unique=True, blank=True, verbose_name="Category Slug")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)  # Automatically generate slug from name
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ['name']  # Order categories by name

class UserPoints(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    points = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} - {self.points} points"

class Product(models.Model):
    name = models.CharField(max_length=255, verbose_name="Product Name")
    description = models.TextField(verbose_name="Product Description")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Product Price")
    stock = models.PositiveIntegerField(verbose_name="Stock Quantity")
    category = models.ForeignKey('Category', on_delete=models.CASCADE, verbose_name="Product Category")
    image = models.ImageField(upload_to='products/', null=True, blank=True, verbose_name="Product Image")
    video_url = models.URLField(null=True, blank=True, verbose_name="Product Video URL")
    panoramic_image = models.ImageField(upload_to='products/panoramic/', null=True, blank=True, verbose_name="Panoramic Image")
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0, verbose_name="Product Rating")
    is_recommended = models.BooleanField(default=False, verbose_name="Recommended Product")
    view_count = models.PositiveIntegerField(default=0, verbose_name="View Count")  # Renamed field
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ['-created_at']

    def is_in_stock(self):
        return self.stock > 0

    def calculate_discounted_price(self, discount_percentage):
        if discount_percentage < 0:
            raise ValueError("Discount percentage cannot be negative.")
        return self.price * (1 - discount_percentage / 100)

    def __str__(self):
        return self.name

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/images/')
    
class ProductDetailView(DetailView):
    model = Product
    template_name = 'shop/product_detail.html'
    context_object_name = 'product'

    def get_object(self, queryset=None):
        product = super().get_object(queryset)
        print(f"Fetching product: {product}")  # Debugging line
        return product
    
class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Last Updated")  # New field for tracking updates

    class Meta:
        verbose_name = "Cart"
        verbose_name_plural = "Carts"

    def total_items(self):
        """Calculate total items in the cart."""
        return sum(item.quantity for item in self.cart_items.all())

    def total_price(self):
        """Calculate total price of items in the cart."""
        return sum(item.total_price for item in self.cart_items.all())

    def clear_cart(self):
        """Remove all items from the cart."""
        self.cart_items.all().delete()

    def __str__(self):
        return f"Cart of {self.user.username}"
class CartItem(models.Model):
    cart = models.ForeignKey('Cart', on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Cart Item"
        verbose_name_plural = "Cart Items"

    @property
    def total_price(self):
        """Calculate total price for this cart item."""
        return self.product.price * self.quantity

    def clean(self):
        """Ensure that quantity is a positive integer before saving."""
        if self.quantity <= 0:
            raise ValidationError('Quantity must be a positive integer.')

    def update_quantity(self, new_quantity):
        """Update the quantity of the cart item."""
        if new_quantity <= 0:
            self.delete()  # Remove item if quantity is set to zero or less
        else:
            self.quantity = new_quantity
            self.full_clean()  # Call clean method to validate before saving
            self.save()

    def __str__(self):
        return f"{self.product.name} (x{self.quantity})"

    def save(self, *args, **kwargs):
        """Override save to ensure data integrity."""
        self.full_clean()  # Validate before saving
        super().save(*args, **kwargs)


class LoyaltyPoints(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    points = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Loyalty Points"
        verbose_name_plural = "Loyalty Points"

    def add_points(self, amount):
        """Add points to the user's loyalty points."""
        if amount > 0:
            self.points += amount
            self.save()
            return True
        return False

    def redeem_points(self, amount):
        """Redeem points if the user has enough."""
        if 0 < amount <= self.points:
            self.points -= amount
            self.save()
            return True
        return False

    def __str__(self):
        return f'{self.user.username} - {self.points} points'

class DiscountCode(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name="Discount Code")
    discount_amount = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Discount Amount")
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Discount Percentage")
    start_date = models.DateField(verbose_name="Start Date")
    end_date = models.DateField(verbose_name="End Date")
    active = models.BooleanField(default=True, verbose_name="Is Active")

    class Meta:
        verbose_name = "Discount Code"
        verbose_name_plural = "Discount Codes"

    def __str__(self):
        return self.code

    def is_active(self):
        """Check if the discount code is currently active."""
        return self.active and self.start_date <= timezone.now().date() <= self.end_date

    def get_discount(self):
        """Calculate discount based on the discount amount or percentage."""
        if self.discount_amount is not None:
            return self.discount_amount
        elif self.discount_percentage is not None:
            return self.discount_percentage / 100  # Convert percentage to decimal
        return 0

    def apply_discount(self, price):
        """Apply the discount to a given price."""
        if self.is_active():
            if self.discount_amount is not None:
                return max(price - self.discount_amount, 0)  # Prevent negative price
            elif self.discount_percentage is not None:
                return price * (1 - self.get_discount())
        return price  # Return original price if not active
    
class OrderItem(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='order_items', verbose_name="Order")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Product")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Quantity")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Price at Purchase")

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"
        ordering = ['-id']  # Optional: Order items by ID descending

    def __str__(self):
        return f"{self.product.name} - Quantity: {self.quantity}"

    def total_price(self):
        """Calculate total price for this order item."""
        return self.price * self.quantity

    def save(self, *args, **kwargs):
        """Override save method to ensure price is always the product's price."""
        if not self.price:
            self.price = self.product.price
        super().save(*args, **kwargs)

class Order(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('mpesa', 'M-Pesa'),
        ('mtn', 'MTN Mobile Money'),
        ('airtel', 'Airtel Money'),
        ('cod', 'Pay on Delivery'),
        ('bank_transfer', 'Bank Transfer'),
        # Add more payment methods as necessary
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total Price")
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ], verbose_name="Order Status")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    payment_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cod', 'Cash on Delivery'),  # Include COD as a payment status
    ], default='pending', verbose_name="Payment Status")
    shipping_address = models.TextField(verbose_name="Shipping Address")
    tracking_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="Tracking Number")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, verbose_name="Payment Method")
    is_payment_required = models.BooleanField(default=True, verbose_name="Is Payment Required?")

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ['-created_at']  # Optional: Order by creation date descending

    def __str__(self):
        return f"Order #{self.id} by {self.user.username} - Total: {self.total_price}"

    def calculate_total_price(self):
        """Calculate total price of the order based on order items."""
        return sum(item.total_price() for item in self.order_items.all())

    def is_payment_pending(self):
        """Check if payment is required and pending."""
        return self.is_payment_required and self.payment_status == 'pending'
    
class UserPreference(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    preferred_categories = models.ManyToManyField(Category, blank=True, related_name='preferred_by', verbose_name="Preferred Categories")
    recommended_products = models.ManyToManyField(Product, blank=True, related_name='recommended_to', verbose_name="Recommended Products")

    class Meta:
        verbose_name = "User Preference"
        verbose_name_plural = "User Preferences"

    def __str__(self):
        return f'{self.user.username} Preferences'

    def get_recommended_products(self):
        """Retrieve recommended products based on user preferences."""
        return self.recommended_products.all()

    def get_preferred_categories(self):
        """Retrieve preferred categories of the user."""
        return self.preferred_categories.all()
    
class Music(models.Model):
    title = models.CharField(max_length=255, verbose_name="Title")
    artist = models.CharField(max_length=255, default='Unknown Artist', verbose_name="Artist")
    album = models.CharField(max_length=255, default='Unknown Album', verbose_name="Album")
    audio_file = models.FileField(upload_to='audio/', verbose_name="Audio File")
    video_file = models.FileField(upload_to='videos/', blank=True, null=True, verbose_name="Video File")
    cover_image = models.ImageField(upload_to='covers/', blank=True, null=True, verbose_name="Cover Image")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        verbose_name = "Music"
        verbose_name_plural = "Music Collection"
        ordering = ['title']  # Order by title by default

    def __str__(self):
        return f"{self.title} by {self.artist}"

    def is_audio_file_available(self):
        """Check if the audio file is available."""
        return self.audio_file is not None

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True, verbose_name="Profile Picture")
    phone_number = models.CharField(max_length=15, blank=True, null=True, verbose_name="Phone Number")
    address = models.TextField(blank=True, null=True, verbose_name="Address")
    email_notifications = models.BooleanField(default=True, verbose_name="Email Notifications")
    sms_notifications = models.BooleanField(default=False, verbose_name="SMS Notifications")
    push_notifications = models.BooleanField(default=True, verbose_name="Push Notifications")
    two_factor_auth = models.BooleanField(default=False, verbose_name="Two-Factor Authentication")
    newsletter = models.BooleanField(default=False, verbose_name="Newsletter Subscription")
    privacy_settings = models.CharField(
        max_length=10,
        choices=[
            ('public', 'Public'),
            ('friends', 'Friends Only'),
            ('private', 'Private')
        ],
        default='public',
        verbose_name="Privacy Settings"
    )
    bio = models.TextField(blank=True, null=True, verbose_name="Biography")  # Added bio field

    def __str__(self):
        return f"{self.user.username}'s Profile"
    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def has_profile_picture(self):
        """Check if the user has a profile picture."""
        return self.profile_picture is not None
#
class SMSMessage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message_content = models.TextField(verbose_name="Message Content")
    phone_number = models.CharField(max_length=15, verbose_name="Phone Number")  # Adjust length as needed for international numbers
    sent_at = models.DateTimeField(auto_now_add=True, verbose_name="Sent At")
    delivered = models.BooleanField(default=False, verbose_name="Delivered")  # To track if the SMS was delivered

    class Meta:
        verbose_name = "SMS Message"
        verbose_name_plural = "SMS Messages"
        ordering = ['-sent_at']  # Order messages by sent time, newest first

    def __str__(self):
        return f"Message to {self.phone_number} at {self.sent_at}: {self.message_content[:20]}..."

    def is_delivered(self):
        """Check if the SMS message was delivered."""
        return self.delivered
class ViewedProduct(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='viewed_by', verbose_name="Product")
    viewed_at = models.DateTimeField(auto_now_add=True, verbose_name="Viewed At")

    class Meta:
        verbose_name = "Viewed Product"
        verbose_name_plural = "Viewed Products"
        ordering = ['-viewed_at']  # Order by the most recently viewed products first
        unique_together = ('user', 'product')  # Ensure a user can only have one record per product

    def __str__(self):
        return f"{self.user.username} viewed {self.product.name} on {self.viewed_at.strftime('%Y-%m-%d %H:%M:%S')}"


class Review(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name="User"
    )
    rating = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        validators=[MinValueValidator(1.0), MaxValueValidator(5.0)],
        verbose_name="Rating"
    )  # e.g., 1.0 to 5.0 rating
    comment = models.TextField(blank=True, null=True, verbose_name="Comment")  # Make comment optional
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")

    class Meta:
        verbose_name = "Review"
        verbose_name_plural = "Reviews"
        ordering = ['-created_at']  # Order reviews by newest first

    def __str__(self):
        return f'Review by {self.user.username} - Rating: {self.rating}'
class Feedback(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    feedback_text = models.TextField(verbose_name="Feedback")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")

    class Meta:
        verbose_name = "Feedback"
        verbose_name_plural = "Feedbacks"
        ordering = ['-created_at']  # Order feedback by newest first

    def __str__(self):
        return f'Feedback from {self.user.username} at {self.created_at.strftime("%Y-%m-%d %H:%M")}'
import uuid
class User(AbstractUser):
    # Bio field for the user's personal information
    bio = models.TextField(blank=True, null=True, verbose_name="User Bio")

    # Phone number field with a regex validator
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',  # Adjust regex for your preferred format
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=16,  # Max length for international format
        blank=True,
        null=True,
        verbose_name="Phone Number"
    )

    # Email verification flag
    is_verified = models.BooleanField(default=False, verbose_name="Is Verified")

    # Verification token for email verification
    verification_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, null=True, blank=True)

    # Optional additional fields
    location = models.CharField(max_length=255, blank=True, null=True, verbose_name="Location")

    def generate_verification_token(self):
        # Generate a new UUID and assign it to the verification token
        self.verification_token = uuid.uuid4()
        self.save()

    def verify_token(self, token):
        # Compare the provided token with the stored verification token
        return token == str(self.verification_token)

    def generate_verification_token(self):
        """Generate a new verification token and save the user instance."""
        self.verification_token = uuid.uuid4()
        self.save()

    # Optional method to reset verification status
    def verify_email(self):
        """Set user as verified and clear the verification token."""
        self.is_verified = True
        self.verification_token = None
        self.save()

    # Profile picture field
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        blank=True,
        null=True,
        verbose_name="Profile Picture"
    )

    # Settings for notifications
    email_notifications = models.BooleanField(default=True, verbose_name="Email Notifications")
    sms_notifications = models.BooleanField(default=False, verbose_name="SMS Notifications")
    push_notifications = models.BooleanField(default=True, verbose_name="Push Notifications")

    # Privacy settings
    privacy_settings = models.CharField(
        max_length=10,
        choices=[
            ('public', 'Public'),
            ('friends', 'Friends Only'),
            ('private', 'Private')
        ],
        default='public',
        verbose_name="Privacy Settings"
    )

    def __str__(self):
        return f"{self.username} ({self.email})"  # Improved string representation

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']  # Order notifications by most recent first
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self):
        return f"{self.user.username}: {self.message[:20]}..."  # Show the first 20 characters of the message
class UserRegistrationStatistic(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    registration_date = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"Registration statistic for {self.user.username} on {self.registration_date.strftime('%Y-%m-%d %H:%M:%S')}"
class ReturnRequest(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='return_requests')
    reason = models.TextField()
    additional_comments = models.TextField(blank=True, null=True)  # Add this line
    request_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('completed', 'Completed'),
        ],
        default='pending'
    )

    def __str__(self):
        return f"Return request for order {self.order.id} by {self.user.username} - Status: {self.status}"


class PageView(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='views')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username if self.user else 'Anonymous'} viewed {self.product.name} on {self.timestamp}"
    
class Offer(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    def __str__(self):
        return self.title
from django.conf import settings
from django.db import models
from django.utils import timezone

class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    added_date = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'product')  # Prevents duplicates for the same user and product
        verbose_name = 'Wishlist Item'
        verbose_name_plural = 'Wishlist Items'

    def __str__(self):
        return f"{self.user.username}'s Wishlist - {self.product.name}"

    def save(self, *args, **kwargs):
        # Optional: Custom save logic can go here
        super().save(*args, **kwargs)

class LoyaltyPointHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    points = models.IntegerField()
    action = models.CharField(max_length=50)  # e.g., 'earned', 'redeemed'
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.points} points {self.action} by {self.user.username} on {self.created_at}"
class GiftCard(models.Model):
    code = models.CharField(max_length=50, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    expiration_date = models.DateTimeField(null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='gift_cards', null=True, blank=True)

    def __str__(self):
        return f"Gift Card {self.code} - ${self.amount} ({'Active' if self.is_active else 'Inactive'})"
class BlogPost(models.Model):
    """Model representing a blog post."""

    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='blog_posts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=True)  # New field to indicate publication status
    slug = models.SlugField(max_length=200, unique=True, blank=True)  # Slug for SEO-friendly URLs

    def save(self, *args, **kwargs):
        """Automatically generate a slug from the title if not provided."""
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        """Return the title of the blog post."""
        return self.title


class NewsletterSubscription(models.Model):
    """Model representing a subscription to the newsletter."""

    email = models.EmailField(unique=True)
    subscribed_on = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def clean(self):
        """Custom validation to ensure the email domain is acceptable."""
        valid_domains = ['example.com']  # Add acceptable domains here
        if not any(self.email.endswith(domain) for domain in valid_domains):
            raise ValidationError(f"Email domain must be one of {valid_domains}")

    def __str__(self):
        """Return the email of the subscriber."""
        return self.email


class Comment(models.Model):
    """Model representing a comment on a blog post."""

    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='comments')  # Changed to refer to BlogPost
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=False)  # New field to manage comment approval

    def __str__(self):
        """Return a summary of the comment content."""
        return f"{self.user.username} on '{self.post.title}': {self.content[:20]}..."

    class Meta:
        ordering = ['-created_at']  # Newest comments first

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator


User = get_user_model()  # Get the custom user model

class Purchase(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases')
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='purchases')  # Assuming you have a Product model
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])  # Ensuring quantity is at least 1
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    purchase_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Purchase"
        verbose_name_plural = "Purchases"
        ordering = ['-purchase_date']  # Orders by most recent purchase first

    def __str__(self):
        return f"Purchase of {self.quantity} x {self.product.name} by {self.user.username} on {self.purchase_date.strftime('%Y-%m-%d %H:%M:%S')}"
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
# in shop/models.py
from .models import Profile

def save_user_profile(user):
    # Ensure the user has an associated profile
    profile, created = Profile.objects.get_or_create(user=user)
    # Now you can safely access `user.profile` without errors
    profile.save()
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        return f'{self.user.username} Profile'

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a UserProfile when a new User is created."""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save the UserProfile when the User is saved."""
    instance.userprofile.save()
class ProductListView(ListView):
    model = Product
    template_name = 'shop/product_list.html'  # Make sure you have this template
    context_object_name = 'products'  # Name of the variable to be used in the template
class FAQ(models.Model):
    CATEGORY_CHOICES = [
        ('payments', 'Payments'),
        ('shipping', 'Shipping'),
        ('returns', 'Returns'),
        ('customer-support', 'Customer Support'),
    ]

    question = models.CharField(max_length=255)
    answer = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    upvotes = models.IntegerField(default=0)
    downvotes = models.IntegerField(default=0)

    def __str__(self):
        return self.question