from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views import View
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView
from django.core.cache import cache

from .forms import (
    CustomUserCreationForm, UserUpdateForm, ProfileUpdateForm, MusicForm, 
    UserPreferenceForm, ReviewForm, FeedbackForm
)
from .models import (
    Product, Cart, CartItem, Review, Order, Category, UserPreference, Music, 
    LoyaltyPoints, DiscountCode, Feedback, Notification
)
from .payment_integration import (
    initiate_mpesa_payment, initiate_mtn_payment, initiate_airtel_payment
)
from django.shortcuts import render
from .models import Product  # Import the Product model from models.py

def recommended_products_view(request):
    recommended_products = Product.objects.filter(is_recommended=True)
    return render(request, 'shop/recommended.html', {'products': recommended_products})

import paypalrestsdk
import stripe
from django.shortcuts import render
from .models import Profile

def profile_view(request):
    if request.user.is_authenticated:
        profile = Profile.objects.get(user=request.user)
    else:
        profile = None
    return render(request, 'profile.html', {'profile': profile})

# PayPal setup
paypalrestsdk.configure({
    "mode": "sandbox",  # Change to "live" in production
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_CLIENT_SECRET
})

# Stripe setup
stripe.api_key = settings.STRIPE_SECRET_KEY

# Custom Login View
class CustomLoginView(LoginView):
    template_name = 'shop/login.html'
    success_url = reverse_lazy('shop:home')

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

# Cart View
class CartView(View):
    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart)
        cart_total = sum(item.product.price * item.quantity for item in cart_items)
        return render(request, 'shop/cart.html', {'cart': cart, 'cart_items': cart_items, 'cart_total': cart_total})

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

# Remove from Cart
@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart_item.delete()
    return redirect('shop:cart_view')

# Checkout View
@login_required
def checkout(request):
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        amount = request.POST.get('amount')
        order_id = 'order123'  # Example order ID
        payment_method = request.POST.get('payment_method')

        payment_methods = {
            'mpesa': initiate_mpesa_payment,
            'mtn': initiate_mtn_payment,
            'airtel': initiate_airtel_payment,
            'paypal': initiate_paypal_payment
        }

        if payment_method in payment_methods:
            response = payment_methods[payment_method](phone_number, amount, order_id)
            if response.get('status') == 'success':
                return redirect('shop:payment_success')
            else:
                return redirect('shop:payment_failure')

        return redirect('shop:payment_failure')

    return render(request, 'shop/checkout.html')

# Payment Success View
def payment_success(request):
    return render(request, 'shop/payment_success.html')

# Payment Failure View
def payment_failure(request):
    return render(request, 'shop/payment_failure.html')

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

# Upload Music
def upload_music(request):
    if request.method == 'POST':
        form = MusicForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('shop:music_list')
    else:
        form = MusicForm()
    return render(request, 'shop/upload_music.html', {'form': form})

# Music List
def music_list(request):
    musics = Music.objects.all()
    return render(request, 'shop/music_list.html', {'musics': musics})

# Other Views (Feedback, Notifications, etc.)
# Implement feedback_view, loyalty_points_view, notification_view, etc.

# AR View
def ar_view(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'shop/ar_view.html', {'product': product})
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('shop:home')  # Redirect to home or any other page after registration
    else:
        form = UserCreationForm()
    
    return render(request, 'shop/register.html', {'form': form})
from django.shortcuts import render

def chat_bot_view(request):
    return render(request, 'shop/chat_bot.html')  # Assuming you have a 'chat_bot.html' template
from django.shortcuts import render

def account_home(request):
    return render(request, 'shop/account_home.html')  # Assuming you have an 'account_home.html' template
from django.shortcuts import render

def chat_room(request, room_name):
    context = {
        'room_name': room_name
    }
    return render(request, 'shop/chat_room.html', context)
from django.shortcuts import render

def feedback_view(request):
    if request.method == 'POST':
        # Handle feedback form submission
        feedback = request.POST.get('feedback')
        # Process feedback, save to database, etc.
        # For now, just render a thank you page
        return render(request, 'shop/feedback_thank_you.html')
    else:
        # Render feedback form
        return render(request, 'shop/feedback_form.html')
from django.shortcuts import render

def music_view(request):
    # Implement the functionality for this view
    return render(request, 'shop/music_view.html')
from django.shortcuts import render

def loyalty_point_view(request):
    # Implement the functionality for this view
    return render(request, 'shop/loyalty_point.html')
from django.shortcuts import render

def notification_view(request):
    # Implement the functionality for this view
    return render(request, 'shop/notification.html')
from django.shortcuts import render

def setup_view(request):
    # Implement the functionality for this view
    return render(request, 'shop/setup.html')
from django.shortcuts import render

def discount_code_list(request):
    # Fetch discount codes and pass them to the template
    # This is a placeholder, adjust according to your model and logic
    discount_codes = []  # Replace with actual query
    return render(request, 'shop/discount_code_list.html', {'discount_codes': discount_codes})
@login_required
def delete_discount_code(request, code_id):
    try:
        discount_code = DiscountCode.objects.get(id=code_id)
        discount_code.delete()
    except DiscountCode.DoesNotExist:
        # Handle the case where the discount code does not exist
        pass
    return redirect('shop:discount_code_list')
@login_required
def create_discount_code(request):
    if request.method == 'POST':
        form = DiscountCodeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('shop:discount_code_list')
    else:
        form = DiscountCodeForm()
    return render(request, 'shop/create_discount_code.html', {'form': form})
from django.shortcuts import render, get_object_or_404, redirect
from .models import DiscountCode
from .forms import DiscountCodeForm

def update_discount_code(request, code_id):
    code = get_object_or_404(DiscountCode, id=code_id)
    if request.method == 'POST':
        form = DiscountCodeForm(request.POST, instance=code)
        if form.is_valid():
            form.save()
            return redirect('some_view_name')  # replace with your redirect view
    else:
        form = DiscountCodeForm(instance=code)

    return render(request, 'shop/update_discount_code.html', {'form': form})
from django.shortcuts import render, redirect
from .models import LoyaltyPoints
from .forms import LoyaltyPointsForm

def update_loyalty_points(request):
    if request.method == 'POST':
        form = LoyaltyPointsForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('some_view_name')  # Update with your desired redirect
    else:
        form = LoyaltyPointsForm()

    return render(request, 'shop/update_loyalty_points.html', {'form': form})
from django.http import HttpResponse

def test_view(request):
    return HttpResponse("This is a test view.")
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  # Redirect to the login page after successful registration
    else:
        form = UserCreationForm()
    
    return render(request, 'shop/register.html', {'form': form})
from django.shortcuts import render, redirect
from .models import DiscountCode
from .forms import DiscountCodeForm

def create_discount_code(request):
    if request.method == 'POST':
        form = DiscountCodeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('discount_code_list')  # Adjust this to the appropriate view
    else:
        form = DiscountCodeForm()
    
    return render(request, 'shop/create_discount_code.html', {'form': form})
# shop/views.py

from django.shortcuts import render, redirect
from .forms import DiscountCodeForm
from .models import DiscountCode

def create_discount_code(request):
    if request.method == 'POST':
        form = DiscountCodeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('shop:discount_code_list')
    else:
        form = DiscountCodeForm()
    return render(request, 'shop/create_discount_code.html', {'form': form})
# In views.py
def loyalty_points_list(request):
    loyalty_points = LoyaltyPoints.objects.filter(user=request.user)
    return render(request, 'shop/loyalty_points_list.html', {'loyalty_points': loyalty_points})
def notification_view(request):
    return render(request, 'shop/notification.html')
from django.shortcuts import render

def order_history(request):
    # Example logic for order history
    orders = []  # Replace with actual logic to get order history
    return render(request, 'shop/order_history.html', {'orders': orders})
from django.shortcuts import render, redirect

def create_discount_code(request):
    # Example logic for creating a discount code
    if request.method == 'POST':
        # Process the form and create the discount code
        pass
    return render(request, 'shop/create_discount_code.html')
from django.shortcuts import render

def create_discount_code(request):
    # Logic to handle creating discount code
    return render(request, 'shop/create_discount_code.html')
from django.shortcuts import render

def create_discount_code(request):
    # Logic for creating a discount code
    return render(request, 'shop/create_discount_code.html')
# shop/views.py
from django.shortcuts import render

def music_view(request):
    # Your view logic here
    return render(request, 'shop/music_view.html')
# shop/views.py
from django.shortcuts import render

def account_home(request):
    # Your view logic here
    return render(request, 'shop/account_home.html')
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import ProfileImageForm

@login_required
def update_profile_picture(request):
    if request.method == 'POST':
        form = ProfileImageForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile picture was successfully updated!')
            return redirect('shop:profile')
    else:
        form = ProfileImageForm(instance=request.user.profile)

    return render(request, 'shop/profile.html', {'form': form})

# shop/views.py
from django.shortcuts import render, get_object_or_404, redirect
from .models import DiscountCode
from .forms import DiscountCodeForm

def update_discount_code(request, code_id):
    discount_code = get_object_or_404(DiscountCode, id=code_id)
    if request.method == 'POST':
        form = DiscountCodeForm(request.POST, instance=discount_code)
        if form.is_valid():
            form.save()
            return redirect('shop:discount_code_list')
    else:
        form = DiscountCodeForm(instance=discount_code)
    return render(request, 'shop/update_discount_code.html', {'form': form})
# shop/paypal_utils.py

from paypalrestsdk import Payment
import paypalrestsdk

# Configure PayPal SDK with your credentials
paypalrestsdk.configure({
    "mode": "sandbox",  # or "live" for production
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET"
})

def initiate_paypal_payment(amount, return_url, cancel_url):
    payment = Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"
        },
        "redirect_urls": {
            "return_url": return_url,
            "cancel_url": cancel_url
        },
        "transactions": [{
            "amount": {
                "total": amount,
                "currency": "USD"
            },
            "description": "Payment description"
        }]
    })

    if payment.create():
        return payment
    else:
        return None
from django.shortcuts import render
from .models import Product  # Assuming you have a Product model

def recommended_products_view(request):
    # Logic to get recommended products (you can customize this)
    recommended_products = Product.objects.filter(is_recommended=True)  # Example filter

    # Render the recommended products in a template
    return render(request, 'shop/recommended_products.html', {'recommended_products': recommended_products})

import yaml
from django.conf import settings  # Import the settings where you defined the YAML path

def load_yaml_data():
    yaml_file_path = settings.YAML_FILE_PATH

    # Open and load the YAML file
    try:
        with open(yaml_file_path, 'r') as file:
            data = yaml.safe_load(file)
            return data  # Now you can use the loaded YAML data
    except FileNotFoundError:
        print(f"YAML file not found at: {yaml_file_path}")
        return None
    except yaml.YAMLError as exc:
        print(f"Error while parsing YAML: {exc}")
        return None
from django.shortcuts import render, get_object_or_404
from .models import Profile  # or wherever your Profile model is located

def profile_view(request):
    user_profile = get_object_or_404(Profile, user=request.user)
    return render(request, 'shop/profile.html', {'profile': user_profile})
from django.shortcuts import render, redirect
from django.views import View
from .models import Profile
from .forms import ProfileForm  # Make sure to create a ProfileForm

class EditProfileView(View):
    def get(self, request):
        profile = Profile.objects.get(user=request.user)
        form = ProfileForm(instance=profile)
        return render(request, 'shop/edit_profile.html', {'form': form})

    def post(self, request):
        profile = Profile.objects.get(user=request.user)
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('shop:profile')  # Redirect to profile page after saving
        return render(request, 'shop/edit_profile.html', {'form': form})

def home(request):
    return render(request, 'shop/home.html')  # Adjust the template name as needed
