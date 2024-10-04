from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views import View
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.core.cache import cache
from django.core.mail import send_mail
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import UserCreationForm
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import ProfileForm  # Ensure this imports your ProfileForm
from django.views.generic import UpdateView
from django.db.models import Avg
from django.views.generic import ListView
from .models import Order 
from .models import SMSMessage
from .forms import (
    CustomUserCreationForm, UserUpdateForm, ProfileUpdateForm, 
    MusicForm, UserPreferenceForm, ReviewForm, FeedbackForm, 
    DiscountCodeForm, LoyaltyPointsForm, ProfileImageForm
)
from .models import (
    Product, Cart, CartItem, Review, Order, Category, UserPreference, 
    Music, LoyaltyPoints, DiscountCode, Feedback, Notification, Profile
)
from .payment_integration import (
    initiate_mpesa_payment, initiate_mtn_payment, initiate_airtel_payment
)
from .mtn_service import get_api_user_info
import paypalrestsdk
import stripe
import requests
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Feedback  # Adjust the import based on your app structure
from .forms import FeedbackForm  # Assuming you're using a form for feedback
from django.views.generic import TemplateView
from .models import Product, PageView

@login_required
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # Log the page view
    PageView.objects.create(user=request.user, product=product)

    return render(request, 'shop/product_detail.html', {'product': product})
@login_required
def mark_as_read(request, notification_id):
    notification = Notification.objects.get(id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect('some_view')  # Redirect to a relevant view
def some_event_triggered(user):
    create_notification(user, "You have a new message!")
class ProfileView(TemplateView):
    template_name = 'shop/profile.html'  # Adjust path as necessary
def some_action(request):
    # Implement your action logic here
    return JsonResponse({'message': 'Action performed successfully!'})
def create_notification(user, message):
    Notification.objects.create(user=user, message=message)
@login_required
def feedback_view(request):
    if request.method == 'POST':
        feedback_content = request.POST.get('feedback')
        if feedback_content:
            Feedback.objects.create(content=feedback_content)  # Save the feedback
            return redirect('shop:thank_you')  # Redirect to the thank you page
    return render(request, 'shop/feedback.html')  # Render the feedback form
def thank_you_view(request):
    return render(request, 'shop/thank_you.html')  # Render the thank you template

# PayPal setup
paypalrestsdk.configure({
    "mode": "sandbox",  # Change to "live" in production
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_CLIENT_SECRET
})

# Stripe setup
stripe.api_key = settings.STRIPE_SECRET_KEY

# Views

# Home View
def home(request):
    user_preference = (
        UserPreference.objects.filter(user=request.user).first()
        if request.user.is_authenticated else None
    )
    products = (
        user_preference.recommended_products.all()
        if user_preference and user_preference.recommended_products.exists() 
        else Product.objects.all()
    )
    return render(request, 'shop/home.html', {'products': products})

# About View
def about(request):
    return render(request, 'shop/about.html')

# Shop View
def shop(request):
    products = Product.objects.all()
    return render(request, 'shop/shop.html', {'products': products})

# Contact View
def contact(request):
    return render(request, 'shop/contact.html')

# Categories View
def categories(request):
    categories = Category.objects.all()
    return render(request, 'shop/categories.html', {'categories': categories, 'current_year': 2024})

# Product Detail View
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'shop/product_detail.html', {'product': product})

# Product List View
def product_list(request):
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    
    products = cache.get('products')
    if not products:
        products = Product.objects.all()
        cache.set('products', products, timeout=60 * 15)
    
    if query:
        products = products.filter(name__icontains=query)
    if category:
        products = products.filter(category__name=category)

    categories = Category.objects.all()
    return render(request, 'shop/product_list.html', {'products': products, 'categories': categories})

#from django.shortcuts import redirect

from django.contrib.auth.models import AnonymousUser

class CartView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'  # URL to redirect to if the user is not logged in

    def get(self, request):
        if isinstance(request.user, AnonymousUser):
            return redirect(self.login_url)
        
        # Fetch or create a cart for the authenticated user
        cart, _ = Cart.objects.get_or_create(user=request.user)
        
        # Retrieve cart items associated with this cart
        cart_items = CartItem.objects.filter(cart=cart)
        
        # Calculate total cost of items in the cart
        cart_total = sum(item.product.price * item.quantity for item in cart_items)
        
        # Render the cart page with the necessary context
        return render(request, 'shop/cart.html', {
            'cart': cart,
            'cart_items': cart_items,
            'cart_total': cart_total
        })

# Add to Cart
@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product, defaults={'quantity': 1})
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    return redirect('shop:cart_view')

# Update Cart Item
@login_required
def update_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    if request.method == 'POST':
        new_quantity = int(request.POST.get('quantity', 1))
        cart_item.quantity = new_quantity
        cart_item.save()
    return redirect('shop:cart_view')

def send_order_confirmation_email(user, order):
    subject = "Order Confirmation"
    message = f"Thank you for your order #{order.id}!"
    send_mail(subject, message, 'from@example.com', [user.email])

# Remove from Cart
@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart_item.delete()
    return redirect('shop:cart_view')
def create_order_notification(user, order):
    message = f"Your order #{order.id} has been placed successfully!"
    Notification.objects.create(user=user, message=message)
# Checkout View

def checkout(request):
    if request.method == 'POST':
        BASE_URL = settings.MOBILE_MONEY_CONFIG['API_BASE_URL']
        API_USER_ID = 'c72025f5-5cd1-4630-99e4-8ba4722fad56'
        SUBSCRIPTION_KEY = settings.MOBILE_MONEY_CONFIG['MTN_API_KEY']

        # Get selected currency and amount from the form (for now assuming UGX is the default)
        amount = request.POST.get('amount', 100)  # Defaulting to 100
        currency = request.POST.get('currency', 'UGX')  # Default to Uganda Shilling (UGX)

        url = f"{BASE_URL}{API_USER_ID}/mtn/initiate"
        headers = {
            'Ocp-Apim-Subscription-Key': SUBSCRIPTION_KEY,
            'Content-Type': 'application/json',
        }
        payload = {
            'amount': amount,
            'currency': currency,
            'description': 'Payment for order',
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return JsonResponse({'success': True, 'data': response.json()})
        except requests.exceptions.RequestException as e:
            return JsonResponse({'error': str(e)}, status=400)

    # Add the supported currencies to pass to the template
    supported_currencies = ['UGX', 'USD', 'KES', 'TZS']  # Uganda Shilling, US Dollar, Kenyan Shilling, Tanzanian Shilling

    return render(request, 'shop/checkout.html', {'supported_currencies': supported_currencies})
def mtn_view(request):
    # Your logic here
    return render(request, 'mtn.html')
# Profile View
@login_required
def profile(request):
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile was successfully updated!')
            return redirect('shop:profile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)
    
    reviews = Review.objects.filter(user=request.user)
    orders = Order.objects.filter(user=request.user)
    
    return render(request, 'shop/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'reviews': reviews,
        'orders': orders
    })
@login_required  # Ensure only logged-in users can access this view
def update_profile_picture(request):
    if request.method == 'POST':
        form = ProfileImageForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            return redirect('profile')  # Redirect to the profile page after saving
    else:
        form = ProfileImageForm(instance=request.user.profile)
    return render(request, 'shop/update_profile_picture.html', {'form': form})

class ProductDetailView(View):
    def get(self, request, *args, **kwargs):
        # Get the product ID (primary key) from the URL kwargs
        product_id = kwargs.get('pk')  # Use 'pk' if your URL pattern uses 'pk'

        # Retrieve the product, or return a 404 if not found
        product = get_object_or_404(Product, pk=product_id)
        
        # Calculate average rating if reviews are present
        average_rating = product.reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        
        # Fetch related products (e.g., based on category), excluding the current product
        related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
        
        # Initialize the review form
        review_form = ReviewForm()

        # Prepare the context data to be passed to the template
        context = {
            'product': product,
            'average_rating': average_rating,
            'related_products': related_products,
            'reviews': product.reviews.all(),  # Fetch all reviews for the product
            'form': review_form,  # Pass the review form to the template
        }
        
        # Render the product detail template with the context
        return render(request, 'shop/product_detail.html', context)
    def post(self, request, *args, **kwargs):
        # Get the product ID from the URL kwargs
        product_id = kwargs.get('id')
        product = get_object_or_404(Product, id=product_id)
        
        # Handle review submission form
        review_form = ReviewForm(request.POST)
        if review_form.is_valid():
            review = review_form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            return redirect('product_detail', id=product_id)  # Redirect after submission

        # If the form is not valid, recalculate average rating and render the page again
        average_rating = product.reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]

        context = {
            'product': product,
            'average_rating': average_rating,
            'related_products': related_products,
            'reviews': product.reviews.all(),
            'form': review_form,  # Pass the review form with validation errors
        }

        return render(request, 'shop/product_detail.html', context)
def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            return redirect('login')  # Redirect to the login page or wherever you want
    else:
        form = UserCreationForm()
    return render(request, 'shop/signup.html', {'form': form})
def chat_bot_view(request):
    return render(request, 'shop/chat_bot.html')  # Make sure you have this template
def account_home(request):
    return render(request, 'shop/account_home.html')  # Adjust the template name as necessary
def payment_success(request):
    return render(request, 'shop/payment_success.html')  # Adjust the template name as necessary
def payment_failure(request):
    return render(request, 'shop/payment_failure.html')  # Adjust the template name as necessary
def ar_view(request, pk):
    product = get_object_or_404(Product, pk=pk)  # Retrieve the product based on the primary key
    return render(request, 'shop/ar_view.html', {'product': product})  # Adjust the template name as necessary
# Add Review
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.product = product
            review.save()
            return redirect('shop:product_detail', pk=product_id)
    else:
        form = ReviewForm()
    return render(request, 'shop/add_review.html', {'form': form, 'product': product})

# Other views (e.g. for feedback, notifications, AR, discount codes, loyalty points) would be added here in the same way.
# Feedback View
@login_required
def feedback_view(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Thank you for your feedback!')
            return redirect('shop:feedback_thank_you')
    else:
        form = FeedbackForm()
    return render(request, 'shop/feedback_form.html', {'form': form})

@login_required
def feedback_thank_you(request):
    return render(request, 'shop/feedback_thank_you.html')


# Notification View
@login_required
def notification_list(request):
    notifications = Notification.objects.filter(user=request.user)
    return render(request, 'shop/notification_list.html', {'notifications': notifications})


# AR (Augmented Reality) View for products
def ar_product_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'shop/ar_view.html', {'product': product})


# Discount Code Views
@login_required
def discount_code_list(request):
    discount_codes = DiscountCode.objects.all()  # Assuming admin views all discount codes
    return render(request, 'shop/discount_code_list.html', {'discount_codes': discount_codes})

@login_required
def apply_discount_code(request, code):
    discount_code = get_object_or_404(DiscountCode, code=code)
    # Apply discount code logic here
    return redirect('shop:cart_view')


# Loyalty Points Views
@login_required
def loyalty_points_list(request):
    loyalty_points = LoyaltyPoints.objects.filter(user=request.user)
    return render(request, 'shop/loyalty_points_list.html', {'loyalty_points': loyalty_points})

@login_required
def update_loyalty_points(request):
    if request.method == 'POST':
        form = LoyaltyPointsForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Loyalty points updated successfully!')
            return redirect('shop:loyalty_points_list')
    else:
        form = LoyaltyPointsForm()
    return render(request, 'shop/update_loyalty_points.html', {'form': form})

# Thank You View for Discount Codes
@login_required
def discount_thank_you(request):
    return render(request, 'shop/discount_thank_you.html')
def upload_music(request):
    if request.method == 'POST' and request.FILES['music_file']:
        music_file = request.FILES['music_file']
        fs = FileSystemStorage()
        filename = fs.save(music_file.name, music_file)
        uploaded_file_url = fs.url(filename)
        # You can also save the file path to the database if needed

        return render(request, 'shop/upload_success.html', {
            'uploaded_file_url': uploaded_file_url
        })
    return render(request, 'shop/upload_music.html')
def music_list(request):
    # Fetch all uploaded music files from the database
    music_files = Music.objects.all()  # Adjust according to your model
    return render(request, 'shop/music_list.html', {'music_files': music_files})
def chat_room(request, room_name):
    return render(request, 'shop/chat_room.html', {'room_name': room_name})
class NotificationListView(View):
    def get(self, request):
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
        return render(request, 'shop/notifications.html', {'notifications': notifications})

    def post(self, request, notification_id):
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({'status': 'success'})

def order_history(request):
    # Fetch the user's orders
    orders = Order.objects.filter(user=request.user).order_by('-date_created')  # Adjust the field name as needed
    return render(request, 'shop/order_history.html', {'orders': orders})
def create_discount_code(request):
    if request.method == 'POST':
        # Logic to create a discount code
        code = request.POST.get('code')
        discount = request.POST.get('discount')
        # Save the discount code (you may need to adjust the fields according to your model)
        DiscountCode.objects.create(code=code, discount=discount)
        return redirect('some_redirect_view')  # Redirect to an appropriate view after creation
    
    return render(request, 'shop/create_discount_code.html')  # Render a template for creating discount codes
def delete_discount_code(request, code_id):
    # Get the discount code by ID
    discount_code = get_object_or_404(DiscountCode, id=code_id)
    
    # Delete the discount code
    if request.method == 'POST':
        discount_code.delete()
        return redirect('some_redirect_view')  # Redirect to a view after deletion

    return render(request, 'shop/confirm_delete_discount_code.html', {'discount_code': discount_code})
def update_discount_code(request, code_id):
    # Get the discount code by ID
    discount_code = get_object_or_404(DiscountCode, id=code_id)

    if request.method == 'POST':
        form = DiscountCodeForm(request.POST, instance=discount_code)
        if form.is_valid():
            form.save()  # Save the updated discount code
            return redirect('some_redirect_view')  # Redirect to a view after updating
    else:
        form = DiscountCodeForm(instance=discount_code)  # Pre-fill the form with current data

    return render(request, 'shop/update_discount_code.html', {'form': form, 'discount_code': discount_code})
def test_view(request):
    return render(request, 'shop/test.html', {})
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful! Welcome!")
            return redirect('home')  # Make sure 'home' is a valid URL name
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserCreationForm()

    return render(request, 'shop/signup.html', {'form': form})  
def music_view(request, music_id):
    music_item = get_object_or_404(Music, id=music_id)
    return render(request, 'shop/music_view.html', {'music': music_item})
def music_list(request):
    music_files = Music.objects.all()  # Fetch all music files
    no_music = not music_files.exists()  # Check if there are no music files
    context = {
        'music_files': music_files,
        'no_music': no_music,  # Pass the no_music flag to the template
    }
    return render(request, 'shop/music_list.html', context)
from .forms import MusicForm

def create_music(request):
    if request.method == 'POST':
        form = MusicForm(request.POST, request.FILES)  # Ensure to include request.FILES
        if form.is_valid():
            form.save()
            return redirect('music_list')  # Adjust this according to your URLs
    else:
        form = MusicForm()
    return render(request, 'music_view.html', {'form': form})
def recommended_products_view(request):
    # Retrieve recommended products, this is just an example
    recommended_products = Product.objects.filter(is_recommended=True)  # Adjust your filtering criteria
    context = {
        'recommended_products': recommended_products
    }
    return render(request, 'shop/recommended_products.html', context)
class EditProfileView(LoginRequiredMixin, UpdateView):
    model = Profile
    form_class = ProfileForm
    template_name = 'shop/edit_profile.html'
    success_url = reverse_lazy('profile')  # Redirect to profile page after successful edit

    def get_object(self, queryset=None):
        return self.request.user.profile  # Get the logged-in user's profile
@login_required
def order_history(request):
    # Ensure request.user is an authenticated user
    if request.user.is_authenticated:
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
        return render(request, 'shop/order_history.html', {'orders': orders})
    else:
        return redirect('login')  # Redirect to the login page if not authenticated

def notification_view(request):
    if request.user.is_authenticated:
        user_notifications = request.user.notifications.all()
        context = {
            'notifications': user_notifications,
        }
        return render(request, 'shop/notification.html', context)
    else:
        # Redirect to login or show a message for anonymous users
        return redirect('shop:login')  # or render a message template

# shop/views.py

from django.db.models import Count

def most_viewed_products(request):
    most_viewed = Product.objects.annotate(view_count=Count('pageview')).order_by('-view_count')[:10]
    return render(request, 'shop/most_viewed.html', {'most_viewed': most_viewed})
from .models import UserRegistrationStatistic

def user_registration_stats(request):
    registrations = UserRegistrationStatistic.objects.all().order_by('-registered_at')
    return render(request, 'shop/registration_stats.html', {'registrations': registrations})

@login_required
def submit_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()

            # Return success response
            return JsonResponse({
                'success': True,
                'username': review.user.username,
                'comment': review.comment,
                'rating': review.rating,
            })
        
        # Return error response if form is not valid
        return JsonResponse({'success': False, 'error': 'Invalid review data.'})

    # If it's a GET request, you might want to return an error
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})
class NotificationView(View):
    def get(self, request):
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
        context = {
            'notifications': notifications,
        }
        return render(request, 'shop/notifications.html', context)

    def post(self, request, notification_id):
        # Mark notification as read
        notification = get_object_or_404(Notification, id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return redirect('shop:notifications')
from .models import ViewedProduct
from django.http import HttpResponse
class ViewedProductsView(View):
    def get(self, request):
        viewed_products = ViewedProduct.objects.filter(user=request.user)
        no_products_viewed = viewed_products.count() == 0
        
        context = {
            'viewed_products': viewed_products,
            'no_products_viewed': no_products_viewed,
        }
        
        return render(request, 'shop/viewed_products.html', context)
class ProductDetailView(View):
    def get(self, request, id):
        # Retrieve the product using the primary key (id)
        product = get_object_or_404(Product, id=id)
        # Render the product detail template with the product context
        return render(request, 'shop/product_detail.html', {'product': product})

    def post(self, request, id):
        # Handle the POST request (e.g., adding to cart or submitting a review)
        product = get_object_or_404(Product, id=id)
        
        # Here you can add your logic for handling the POST request
        # For example, you might want to add the product to the user's cart
        # Assuming you have a form submission to add the product to cart:
        
        # Add your logic to handle the POST data
        # e.g., request.POST.get('quantity') or similar
        
        return HttpResponse("Product updated")  # Customize this response as needed
class HomeView(View):
    def get(self, request, *args, **kwargs):
        # Render the home page
        return render(request, 'shop/home.html') 
import json

async def receive(self, text_data):
    text_data_json = json.loads(text_data)

    # Check if the received data indicates typing status
    if 'typing' in text_data_json:
        is_typing = text_data_json['typing']
        # Broadcast typing status to the group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_message',  # This should correspond to a method in your consumer to handle typing status
                'is_typing': is_typing,
            }
        )

from .models import Message  # Ensure you import the Message model

def chat_room(request, room_name):
    # Fetch messages for the specific room
    messages = Message.objects.filter(room_name=room_name)
    return render(request, 'shop/chat_room.html', {'room_name': room_name, 'messages': messages})
 #shop/views.py
from django.views.generic import ListView
from .models import Order  # Ensure this points to your Order model

class OrderHistoryView(ListView):
    model = Order
    template_name = 'shop/order_history.html'  # Ensure this template exists
    context_object_name = 'orders'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)  # Adjust as needed

def account_settings_view(request):
    return render(request, 'shop/account_settings.html')
from django.shortcuts import render

def wishlist_view(request):
    # Replace with your actual logic for fetching wishlist items
    wishlist_items = []  # Example: Fetch user's wishlist items here
    return render(request, 'shop/wishlist.html', {'wishlist_items': wishlist_items})
def account_home(request):
    # Logic to retrieve and display account information
    return render(request, 'shop/account_home.html')  # En

@login_required
def update_account_settings(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        profile_picture = request.FILES.get('profile_picture')

        # Update user info
        user = request.user
        user.username = username
        user.email = email
        user.first_name = first_name
        user.last_name = last_name

        if password:  # Only change password if a new one is provided
            user.set_password(password)

        if profile_picture:  # Handle profile picture upload
            user.profile_picture = profile_picture  # Assuming you have a profile_picture field
        user.save()
        messages.success(request, "Account settings updated successfully.")
        return redirect('shop:account_settings')  # Redirect to the settings page or any other page

    return render(request, 'shop/account_settings.html')
@login_required
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        user.delete()
        messages.success(request, "Your account has been deleted successfully.")
        return redirect('shop:home')  # Redirect to a suitable page after deletion

    return render(request, 'shop/delete_account_confirmation.html')  # A confirmation page (optional)
class WishlistView(View):
    def get(self, request):
        # Logic to retrieve and display the wishlist
        return render(request, 'shop/wishlist.html')  # Ens
    class OffersView(View):
     def get(self, request):
        # Logic to retrieve and display offers
        return render(request, 'shop/offers.html')
     from django.shortcuts import render, redirect
from django.views.generic import ListView
from .models import Offer, Wishlist, Feedback  # Make sure these models exist
from django.contrib import messages
from .forms import FeedbackForm  # Ensure you have a FeedbackForm defined in forms.py


class OffersView(ListView):
    model = Offer
    template_name = 'shop/offers.html'  # Template for displaying offers
    context_object_name = 'offers'

    def get_queryset(self):
        # Filter to get only active offers
        return Offer.objects.filter(is_active=True)


def wishlist_view(request):
    """View for displaying and managing the user's wishlist."""
    if request.user.is_authenticated:
        wishlist_items = Wishlist.objects.filter(user=request.user)
        return render(request, 'shop/wishlist.html', {'wishlist_items': wishlist_items})
    else:
        messages.error(request, "You need to be logged in to view your wishlist.")
        return redirect('login')  # Redirect to login if not authenticated


def feedback_view(request):
    """View for submitting feedback."""
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.user = request.user  # Associate feedback with the logged-in user
            feedback.save()
            messages.success(request, "Thank you for your feedback!")
            return redirect('feedback')  # Redirect to feedback page or another page
    else:
        form = FeedbackForm()

    return render(request, 'shop/feedback_form.html', {'form': form})  # Render feedback form


def privacy_policy(request):
    return render(request, 'shop/privacy_policy.html')

def terms_of_service(request):
    return render(request, 'shop/terms_of_service.html')

def contact_us(request):
    return render(request, 'shop/contact_us.html')