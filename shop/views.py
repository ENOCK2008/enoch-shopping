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
from django.views.generic import ListView
from .models import Offer, Wishlist, Feedback  # Make sure these models exist
from django.contrib import messages
from .forms import FeedbackForm  # Ensure you have a FeedbackForm defined in forms.py


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
    login_url = '/accounts/login/'

    def get(self, request):
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart)
        cart_total = sum(item.product.price * item.quantity for item in cart_items)
        
        return render(request, 'shop/cart_view.html', {
            'cart': cart,
            'cart_items': cart_items,
            'cart_total': cart_total,
        })

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if product.stock <= 0:
        messages.warning(request, "Sorry, this product is out of stock.")
        return redirect('shop:product_detail', product_id=product.id)

    cart, created = Cart.objects.get_or_create(user=request.user)

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 1}
    )
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()

    messages.success(request, f"{product.name} has been added to your cart.")
    
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
@login_required
def cart_view(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart)
    cart_total = sum(item.product.price * item.quantity for item in cart_items)
    return render(request, 'shop/cart_view.html', {'cart_items': cart_items, 'cart_total': cart_total})

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

def checkout_view(request):
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
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from .forms import CustomUserCreationForm

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Automatically log in the user after registration
            messages.success(request, "Registration successful! Welcome!")
            return redirect('shop:home')  # Redirect to home or another page
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserCreationForm()

    context = {
        'form': form,
        'registered': request.method == 'POST' and form.is_valid()
    }
    return render(request, 'shop/register.html', context)

def music_view(request, music_id):
    music_item = get_object_or_404(Music, id=music_id)
    return render(request, 'shop/music_view.html', {'music': music_item})


def music_list(request):
    music_files = Music.objects.all()  # Fetch all music files
    no_music = not music_files.exists()  # Check if there are no music files

    if request.method == 'POST':
        form = MusicForm(request.POST, request.FILES)  # Handle form submission
        if form.is_valid():
            form.save()  # Save the new music file
            return redirect('shop:music_list')  # Redirect after successful upload
    else:
        form = MusicForm()  # Create an empty form for GET requests

    context = {
        'music_files': music_files,
        'no_music': no_music,  # Pass the no_music flag to the template
        'form': form,  # Pass the form to the template
    }
    return render(request, 'shop/music_list.html', context)
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

def chat_room(request, room_name):
    # Fetch SMS messages for the specific room
    messages = SMSMessage.objects.filter(phone_number=room_name)  # Update this logic as needed
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
from .models import Profile
@login_required
def update_account_settings(request):
    user_profile = Profile.objects.get(user=request.user)

    if request.method == 'POST':
        # Update user basic information
        request.user.username = request.POST['username']
        request.user.email = request.POST['email']
        request.user.first_name = request.POST['first_name']
        request.user.last_name = request.POST['last_name']

        # Update password if provided
        if request.POST['password']:
            request.user.set_password(request.POST['password'])

        # Update profile picture if provided
        if request.FILES.get('profile_picture'):
            user_profile.profile_picture = request.FILES['profile_picture']

        # Update additional settings
        user_profile.two_factor_auth = 'two_factor_auth' in request.POST
        user_profile.newsletter = 'newsletter' in request.POST
        user_profile.privacy_settings = request.POST['privacy_settings']
        
        # Save changes
        request.user.save()
        user_profile.save()

        messages.success(request, 'Your account settings have been updated successfully.')
        return redirect('shop:account_settings')

    return render(request, 'shop/account_settings.html', {'user': request.user, 'profile': user_profile})
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
# shop/views.py

from django.db.models import Q

def search_view(request):
    query = request.GET.get('q', '').strip()  # Get the query and strip whitespace
    products = Product.objects.none()  # Initialize products as an empty queryset

    if query:  # Only search if there's a non-empty query
        # Filter products based on the search query
        products = Product.objects.filter(Q(name__icontains=query) | Q(description__icontains=query))

    product_count = products.count()  # Using count() on queryset

    return render(request, 'shop/search_results.html', {
        'products': products,
        'product_count': product_count,
        'query': query,
    })


def filter_view(request):
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    
    products = Product.objects.all()

    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    return render(request, 'shop/product_list.html', {'products': products})
from .models import Category, Product

def category_view(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category)
    return render(request, 'shop/categories.html', {'category': category, 'products': products})
# views.py

def most_viewed_view(request):
    # Logic to retrieve most viewed products
    most_viewed_products = []  # Replace with actual logic to get products
    context = {
        'most_viewed_products': most_viewed_products,
    }
    return render(request, 'shop/most_viewed.html', context)


from .models import Offer

def offer_list_view(request):
    # Fetch active offers from the Offer model
    offers = Offer.objects.filter(active=True)  # Assuming 'active' is a Boolean field

    # Convert each offer into a dictionary format
    offers_data = [
        {
            "title": offer.title,
            "description": offer.description,  # Including description for more context
            "discount": offer.discount_percentage,
            "start_date": offer.start_date,    # Optionally include start and end dates
            "end_date": offer.end_date,
        }
        for offer in offers
    ]

    context = {
        'offers': offers_data,
    }
    return render(request, 'shop/offer_list.html', context)
from django.shortcuts import render

def privacy_policy_view(request):
    return render(request, 'shop/privacy_policy.html')

def dashboard_view(request):
    recommended_products = Product.objects.filter(on_sale=True)
    all_products = Product.objects.all()  # Modify this as per your needs

    context = {
        'recommended_products': recommended_products,
        'all_products': all_products,
        'user': request.user,
        # other context variables as needed
    }
    return render(request, 'shop/dashboard.html', context)
from .models import LoyaltyPointHistory  # Import your model for points history

def loyalty_points(request):
    # Assuming you have a user model with a loyalty_points field
    user = request.user
    loyalty_points = user.loyalty_points  # Fetch user's loyalty points

    # Fetch points history for the user
    points_history = LoyaltyPointHistory.objects.filter(user=user).order_by('-date')

    context = {
        'loyalty_points': loyalty_points,
        'points_history': points_history,
    }
    return render(request, 'shop/loyalty_points.html', context)

def discount_codes_view(request):
    discount_codes = DiscountCode.objects.filter(active=True)  # Optionally filter active codes
    return render(request, 'shop/discount_code_list.html', {'discount_codes': discount_codes})
class DiscountCodeListView(ListView):
    model = DiscountCode
    template_name = 'shop/discount_code_list.html'
    context_object_name = 'discount_codes'

    def get_queryset(self):
        return DiscountCode.objects.filter(active=True)
    from django.shortcuts import render

def faq_view(request):
    return render(request, 'shop/faq.html')
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import LoyaltyPoints  # Adjust the import according to your project structure
from django.contrib.auth.decorators import login_required

@login_required  # Ensure the user is logged in to access this view
def redeem_points_view(request):
    # Fetch the user's loyalty points
    user_points = LoyaltyPoints.objects.get(user=request.user)

    if request.method == 'POST':
        # Handle the redemption request
        points_to_redeem = request.POST.get('points')

        try:
            points_to_redeem = int(points_to_redeem)
            if points_to_redeem <= 0:
                messages.error(request, "Please enter a valid number of points to redeem.")
            elif points_to_redeem > user_points.points:
                messages.error(request, "You do not have enough points to redeem this amount.")
            else:
                # Deduct points from the user's account
                user_points.points -= points_to_redeem
                user_points.save()
                
                # You can also add logic here for what the user receives in return
                messages.success(request, f"You have successfully redeemed {points_to_redeem} points!")
                return redirect('shop:loyalty_points_list')  # Redirect to loyalty points list or another page
        except ValueError:
            messages.error(request, "Invalid input. Please enter a number.")

    return render(request, 'shop/redeem_points.html', {'user_points': user_points})
from django.http import Http404

def loyalty_terms_view(request):
    try:
        # You could pass any context data if needed
        context = {
            'terms': "Here are the terms and conditions of our loyalty program..."
        }
        return render(request, 'shop/loyalty_terms.html', context)
    except Exception as e:
        # Log the exception or handle it as needed
        raise Http404("Page not found.")
from django.shortcuts import render
from .models import LoyaltyPoints  # Ensure this imports your LoyaltyPoints model

def redeem_points_view(request):
    try:
        # Assuming you want to get loyalty points for the current user
        loyalty_points = LoyaltyPoints.objects.get(user=request.user)  # Adjust as necessary
    except LoyaltyPoints.DoesNotExist:
        # Handle the case where there are no loyalty points for the user
        loyalty_points = None  # Set loyalty_points to None if not found

    # Render the template with loyalty points data
    context = {
        'loyalty_points': loyalty_points
    }
    return render(request, 'shop/redeem_points.html', context)
from django.contrib import messages

def add_payment_method(request):
    if request.method == 'POST':
        # Logic for adding the payment method
        card_number = request.POST.get('card_number')
        expiry_date = request.POST.get('expiry_date')
        # Process the payment method (e.g., save to the database)
        
        messages.success(request, "Payment method added successfully.")
        return redirect('shop:account_settings')  # Redirect to the account settings or another page

    return render(request, 'shop/account_settings.html')  # Render the template if GET request
from django.contrib import messages

def add_shipping_address(request):
    if request.method == 'POST':
        # Logic for adding the shipping address
        address = request.POST.get('address')
        city = request.POST.get('city')
        # Process and save the address (e.g., save to the database)
        
        messages.success(request, "Shipping address added successfully.")
        return redirect('shop:account_settings')  # Redirect to the account settings or another page

    return render(request, 'shop/account_settings.html')  # Render the template if GET request
from django.contrib.auth.models import User

def send_verification_email(request):
    if request.method == 'POST':
        # Logic to send a verification email
        user = request.user
        if user.is_authenticated and not user.is_verified:
            # Assuming you have a method to send verification email
            user.send_verification_email()  # Implement this method in your User model
            messages.success(request, "Verification email sent successfully.")
        else:
            messages.error(request, "You cannot resend a verification email.")

    return render(request, 'shop/account_settings.html')  # Render the template if GET request
def generate_referral_link(request):
    if request.method == 'POST':
        # Logic to generate referral link
        user = request.user
        if user.is_authenticated:
            referral_link = f"http://yourdomain.com/referral?ref={user.id}"  # Example link generation
            messages.success(request, f"Your referral link: {referral_link}")
        else:
            messages.error(request, "You must be logged in to generate a referral link.")

    return render(request, 'shop/account_settings.html')  # Render the template
def update_security_questions(request):
    if request.method == 'POST':
        # Logic to update security questions and answers
        security_question_1 = request.POST.get('security_question_1')
        security_answer_1 = request.POST.get('security_answer_1')
        
        # Save the security question and answer to the user's profile
        user = request.user
        user.profile.security_question_1 = security_question_1
        user.profile.security_answer_1 = security_answer_1
        user.profile.save()

        messages.success(request, "Your security questions have been updated.")

    return render(request, 'shop/account_settings.html')  # Render the template
def deactivate_account(request):
    if request.method == 'POST':
        # Logic to deactivate the user's account
        user = request.user
        user.is_active = False  # Or whatever logic you use for deactivation
        user.save()

        messages.success(request, "Your account has been deactivated.")
        return redirect('shop:home')  # Redirect to a safe page after deactivation

    return render(request, 'shop/account_settings.html')  
def update_theme_preferences(request):
    if request.method == 'POST':
        theme = request.POST.get('theme')
        request.user.profile.theme = theme  # Assuming you have a Profile model linked to the User
        request.user.profile.save()

        messages.success(request, "Theme preferences updated successfully.")
        return redirect('shop:account_settings')  # Redirect back to the account settings

    return render(request, 'shop/account_settings.html')  # Render the template for the form
from django.http import JsonResponse  # or HttpResponse, depending on your data format

def export_data(request):
    if request.method == 'POST':
        # Logic to export user data
        user_data = {
            'username': request.user.username,
            'email': request.user.email,
            # Add other fields as needed
        }
        # You can either return this as JSON or create a CSV/excel file depending on your requirement
        return JsonResponse(user_data)  # Example of returning JSON data

    # If GET request, render a template or redirect as needed
    return render(request, 'shop/account_settings.html')  # Adjust as necessary
def submit_feedback(request):
    if request.method == 'POST':
        feedback = request.POST.get('feedback')
        # Logic to process the feedback (e.g., save it to the database)
        # For example:
        # FeedbackModel.objects.create(user=request.user, feedback=feedback)

        messages.success(request, 'Thank you for your feedback!')
        return redirect('shop:account_settings')  # Redirect to a relevant page after submission

    # If the request method is GET, render the account settings page or redirect
    return render(request, 'shop/account_settings.html')  # Adjust as necessary
def link_social_account(request):
    if request.method == 'POST':
        # Check if the user wants to link a Facebook account
        if request.POST.get('link_facebook'):
            # Add logic here to link Facebook account
            # For example, use the Facebook API to authenticate and link the account
            messages.success(request, 'Facebook account linked successfully!')

        # Check if the user wants to link a Google account
        elif request.POST.get('link_google'):
            # Add logic here to link Google account
            # For example, use the Google API to authenticate and link the account
            messages.success(request, 'Google account linked successfully!')

        else:
            messages.error(request, 'No valid account type selected to link.')

        return redirect('shop:account_settings')  # Redirect to the account settings page

    # If the request method is GET, render the account settings page
    return render(request, 'shop/account_settings.html')
def update_accessibility(request):
    if request.method == 'POST':
        text_size = request.POST.get('text_size')

        # Save the text size to the user's profile
        request.user.profile.text_size = text_size
        request.user.profile.save()
        
        messages.success(request, 'Accessibility settings updated successfully!')
        return redirect('shop:account_settings')  # Redirect to the account settings page

    # If the request method is GET, render the account settings page
    return render(request, 'shop/account_settings.html')
from .models import Music  # Import your Music model
from django.core.files.storage import FileSystemStorage

def music_list(request):
    # Fetch all music items from the database
    music_list = Music.objects.all()
    no_music = not music_list  # Check if there are no music items
    return render(request, 'shop/music_list.html', {'music_list': music_list, 'no_music': no_music})

def upload_music(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        artist = request.POST.get('artist')
        audio_file = request.FILES.get('audio_file')

        if title and artist and audio_file:
            # Create a new Music object and save it
            music = Music(title=title, artist=artist, audio_file=audio_file)
            music.save()  # Save the music instance to the database
            messages.success(request, 'Music uploaded successfully!')
            return redirect('shop:music_list')  # Redirect to the music list page
        else:
            messages.error(request, 'Please fill in all fields.')

    # If the request method is GET, render the upload form
    return render(request, 'shop/upload_music.html')  # Adjust the template name if needed
from .models import Product, Review  # Assuming you have a Review model

def submit_review(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        comment = request.POST.get('comment')
        rating = request.POST.get('rating')

        # Create a new review (ensure you have a Review model defined)
        Review.objects.create(
            product=product,
            user=request.user,  # Assuming you're associating the review with the user
            comment=comment,
            rating=rating
        )

        messages.success(request, 'Your review has been submitted!')
        return redirect('shop:product_detail', product_id=product.id)

    # Redirect or render appropriate response if method is not POST
    return redirect('shop:product_detail', product_id=product_id)
from django.contrib.auth.decorators import login_required
from .models import Profile

@login_required
def update_social_media(request):
    if request.method == 'POST':
        profile = request.user.profile
        profile.whatsapp = request.POST.get('whatsapp', '')
        profile.facebook = request.POST.get('facebook', '')
        profile.twitter = request.POST.get('twitter', '')
        profile.instagram = request.POST.get('instagram', '')
        profile.linkedin = request.POST.get('linkedin', '')
        profile.save()
        return redirect('shop:account_settings')  # Redirect to account settings or another page
    return render(request, 'shop/account_settings.html')
login_required
def update_two_factor(request):
    if request.method == 'POST':
        profile = request.user.profile
        profile.two_factor_enabled = not profile.two_factor_enabled  # Toggle the setting
        profile.save()
        return redirect('shop:account_settings')  # Redirect back to account settings
    return redirect('shop:account_settings')  # Redirect if not a POST request
def update_subscription(request):
    if request.method == 'POST':
        # Logic to update the subscription
        user_profile = request.user.profile
        user_profile.newsletter_subscription = request.POST.get('newsletter_subscription') == 'on'
        user_profile.save()
        messages.success(request, 'Subscription updated successfully!')
        return redirect('shop:account_settings')  # Adjust redirect as necessary
    return render(request, 'shop/account_settings.html')
def update_privacy(request):
    if request.method == 'POST':
        # Logic to update privacy settings
        user_profile = request.user.profile
        user_profile.visibility = request.POST.get('profile_visibility')
        user_profile.save()
        messages.success(request, 'Privacy settings updated successfully!')
        return redirect('shop:account_settings')  # Redirect to account settings after update
    return render(request, 'shop/account_settings.html')
def update_language(request):
    if request.method == 'POST':
        # Logic to update language preference
        user_profile = request.user.profile
        user_profile.language = request.POST.get('language')
        user_profile.save()
        messages.success(request, 'Language preferences updated successfully!')
        return redirect('shop:account_settings')  # Redirect to account settings after update
    return render(request, 'shop/account_settings.html')
from .forms import CheckoutForm  # Import your form here
from .models import Order  # Assuming you have an Order model

def track_order(request):
    tracking_number = request.POST.get('tracking_number') if request.method == 'POST' else None
    order = None

    if tracking_number:
        try:
            order = Order.objects.get(tracking_number=tracking_number)
        except Order.DoesNotExist:
            messages.error(request, "No order found with that tracking number.")

    return render(request, 'shop/track_order.html', {'order': order})
from .models import ReturnRequest  # Assuming you have a model for handling return requests
from .forms import ReturnRequestForm  # Assuming you have a form for return requests

def returns_view(request):
    if request.method == 'POST':
        form = ReturnRequestForm(request.POST)
        if form.is_valid():
            return_request = form.save(commit=False)
            return_request.user = request.user  # Associate the request with the logged-in user
            return_request.save()
            messages.success(request, 'Your return request has been submitted successfully.')
            return redirect('shop:returns')  # Redirect to the same returns page after submission
    else:
        form = ReturnRequestForm()

    return render(request, 'shop/returns.html', {'form': form})
from .models import GiftCard  # Assuming you have a GiftCard model to manage gift cards

def gift_cards_view(request):
    # Fetch available gift cards from the database
    gift_cards = GiftCard.objects.filter(is_active=True)  # Assuming you have an is_active field

    context = {
        'gift_cards': gift_cards,
        'messages': request.messages if hasattr(request, 'messages') else [],
    }

    # Render the gift cards template with the gift card data
    return render(request, 'shop/gift_cards.html', context)
from .models import BlogPost  # Assuming you have a BlogPost model
from django.core.paginator import Paginator
def blog_view(request):
    all_posts = BlogPost.objects.all()
    paginator = Paginator(all_posts, 5)  # Show 5 posts per page

    page_number = request.GET.get('page')
    paginated_posts = paginator.get_page(page_number)

    comments = {}  # Create a dictionary to store comments for each post

    for post in paginated_posts:
        # Assuming you have a Comment model that relates to BlogPost
        comments[post.id] = post.comments.all()  # Get comments for each post

    context = {
        'posts': paginated_posts,
        'comments': comments,  # Pass the comments dictionary to the template
    }

    return render(request, 'shop/blog.html', context)
from .models import NewsletterSubscription  # Make sure to create this model

def subscribe(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            # Save the email to your database
            NewsletterSubscription.objects.create(email=email)
            messages.success(request, 'Thank you for subscribing!')
        else:
            messages.error(request, 'Please enter a valid email address.')
        return redirect('shop:home')  # Redirect to the home page or any page you prefer
    return render(request, 'shop/home.html')
class CategoryView(View):
    template_name = 'shop/category.html'

    def get(self, request, slug):
        category = get_object_or_404(Category, slug=slug)
        products = Product.objects.filter(category=category)

        context = {
            'category': category,
            'products': products,
        }

        return render(request, self.template_name, context)
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django import forms
from django.urls import reverse_lazy
class ContactForm(forms.Form):
    name = forms.CharField(max_length=100, required=True, label='Your Name')
    email = forms.EmailField(required=True, label='Your Email')
    message = forms.CharField(widget=forms.Textarea, required=True, label='Your Message')

class PrivacyPolicyView(TemplateView):
    template_name = 'shop/privacy_policy.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Privacy Policy'
        return context

class ContactView(FormView):
    template_name = 'shop/contact_us.html'
    form_class = ContactForm
    success_url = reverse_lazy('shop:contact')  # Redirect after successful form submission

    def form_valid(self, form):
        # Here you would handle the form submission, e.g., send an email
        # For example:
        name = form.cleaned_data['name']
        email = form.cleaned_data['email']
        message = form.cleaned_data['message']
        
        # You could implement your email sending logic here
        # send_mail(subject, message, from_email, recipient_list)
        
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Contact Us'
        return context
def calculate_profile_completion(user):
    total_fields = 5  # Adjust based on the number of fields
    completed = 0
    if user.profile.profile_picture:
        completed += 1
    if user.email:
        completed += 1
    if user.profile.bio:
        completed += 1
    # Add more field checks here...

    return int((completed / total_fields) * 100)
from .forms import ProfileForm

def profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            return redirect('shop:profile')  # Ensure this matches the URL pattern name
    else:
        form = ProfileForm(instance=request.user.profile)
    
    profile_completion = calculate_profile_completion(request.user)
    context = {
        'form': form,
        'user': request.user,
        'profile_completion': profile_completion,
    }
    return render(request, 'shop/profile.html', context)
class FilteredProductsView(View):
    def get(self, request):
        price_filter = request.GET.get('price')
        products = Product.objects.all()

        if price_filter == 'low-to-high':
            products = products.order_by('price')
        elif price_filter == 'high-to-low':
            products = products.order_by('-price')

        return render(request, 'shop/categories.html', {'products': products})

from .models import Product, Comment  # Adjust imports as necessary

class AddCommentView(View):
    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        comment_text = request.POST.get('comment')
        # Assuming you have a Comment model with a foreign key to Product and User
        Comment.objects.create(
            user=request.user,
            product=product,
            text=comment_text,
        )
        return redirect('shop:product_detail', product_id=product.id)  # Redirect to the product detail page
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json
import time

# Rate limit configuration
RATE_LIMIT_SECONDS = 10  # Time window in seconds
USER_REQUESTS_KEY = "user_requests"  # Key to track user requests in the session

@csrf_exempt
@login_required
def chat_response(request):
    if request.method == "POST":
        # Rate limiting
        user_requests = request.session.get(USER_REQUESTS_KEY, [])
        current_time = time.time()

        # Remove timestamps older than the rate limit window
        user_requests = [timestamp for timestamp in user_requests if current_time - timestamp < RATE_LIMIT_SECONDS]
        
        if len(user_requests) >= 5:  # Allow up to 5 requests in the time window
            return JsonResponse({"error": "Rate limit exceeded, please try again later."}, status=429)

        # Record the new request timestamp
        user_requests.append(current_time)
        request.session[USER_REQUESTS_KEY] = user_requests

        try:
            data = json.loads(request.body.decode("utf-8"))
            user_message = data.get("message", "")
            user = request.user

            if user_message:
                # Generate a response based on user message
                response_message = generate_ai_response(user_message, user)
                return JsonResponse({"response": response_message}, status=200)
            else:
                return JsonResponse({"error": "No message provided"}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON input"}, status=400)
    else:
        return JsonResponse({"error": "POST request required"}, status=405)

def generate_ai_response(user_message, user=None):
    user_message = user_message.lower()  # Normalize input to lowercase

    if "help" in user_message:
        return "Sure! I can help you with your shopping."

    if "latest deals" in user_message:
        return "Here are our latest deals:http://127.0.0.1:8000/blog/."

    if "view my cart" in user_message:
        # You might want to return a cart summary here
        return "You have 3 items in your cart: http://127.0.0.1:8000/cart/."

    if "recommended products" in user_message:
        return "Here are some recommended products for you: http://127.0.0.1:8000/recommended/."

    if "faqs" in user_message or "frequently asked questions" in user_message:
        return "You can find our FAQs here: http://127.0.0.1:8000/faq/."

    return "I'm here to assist you with your shopping needs!"
from .models import Product, Wishlist  # Import your models appropriately

def add_to_wishlist(request, product_id):
    # Check if the user is authenticated
    if not request.user.is_authenticated:
        messages.error(request, "You must be logged in to add items to your wishlist.")
        return redirect('shop:login')  # Redirect to login page

    # Get the product or return a 404 error if it does not exist
    product = get_object_or_404(Product, id=product_id)

    # Check if the product is already in the user's wishlist
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)

    if product in wishlist.products.all():  # Assuming you have a many-to-many relationship
        messages.info(request, f"{product.name} is already in your wishlist.")
    else:
        wishlist.products.add(product)  # Add product to the wishlist
        messages.success(request, f"{product.name} has been added to your wishlist.")

    return redirect('shop:wishlist')  # Redirect to the wishlist page
from .models import Wishlist, Product

def remove_from_wishlist(request, item_id):
    # Check if the user is authenticated
    if not request.user.is_authenticated:
        messages.error(request, "You must be logged in to remove items from your wishlist.")
        return redirect('shop:login')  # Redirect to login page

    # Get the user's wishlist
    wishlist = get_object_or_404(Wishlist, user=request.user)

    # Get the product to remove
    product = get_object_or_404(Product, id=item_id)

    # Remove the product from the wishlist
    if product in wishlist.products.all():
        wishlist.products.remove(product)
        messages.success(request, f"{product.name} has been removed from your wishlist.")
    else:
        messages.info(request, f"{product.name} was not found in your wishlist.")

    return redirect('shop:wishlist')  # Redirect to the wishlist page
def wishlist(request):
    if request.user.is_authenticated:
        wishlist_items = Wishlist.objects.filter(user=request.user)  # Get user's wishlist items
        return render(request, 'shop/wishlist.html', {'wishlist_items': wishlist_items})
    else:
        messages.error(request, "You need to be logged in to view your wishlist.")
        return redirect('shop:login')  # Redirect to login page

def add_to_wishlist(request, product_id):
    # Your logic for adding to wishlist
    return redirect('shop:wishlist')  # Redirect to the wishlist or another page

def remove_from_wishlist(request, item_id):
    # Logic to remove item from wishlist (as discussed before)
    return redirect('shop:wishlist')  # Redirect to the wishlist or another page
class ProductDetailView(View):
    def get(self, request, product_id):  # Accept product_id instead of id
        # Attempt to retrieve the product by its ID
        product = get_object_or_404(Product, id=product_id)  # Use product_id here
        context = {
            'product': product,
        }
        return render(request, 'shop/product_detail.html', context)