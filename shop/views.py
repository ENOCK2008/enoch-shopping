from datetime import datetime
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import FileSystemStorage
from django.core.mail import send_mail
from django.db.models import Avg
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic.edit import FormView
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth import authenticate, login
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.forms import AuthenticationForm
from .forms import ReturnRequestForm  # Adjust the import based on your file structure
from django.views.decorators.http import require_POST
from django.views.generic import UpdateView, ListView, TemplateView
from .cart import Cart 
from django.utils import timezone
from datetime import timedelta
from .cart import get_cart_items  # Import a function to retrieve cart items
from .utils import calculate_total, calculate_delivery_date  # Custom utility functions
from .forms import (
    AccountSettingsForm, ProfileForm, CustomUserCreationForm,
    UserUpdateForm, ProfileUpdateForm, MusicForm, UserPreferenceForm,
    ReviewForm, FeedbackForm, DiscountCodeForm, LoyaltyPointsForm,
    ProfileImageForm
)
from .models import (
    Product, Cart, CartItem, Review, Order, Category,
    UserPreference, Music, LoyaltyPoints, DiscountCode,
    Feedback, Notification, Profile, Offer, Wishlist, PageView, SMSMessage
)
from .payment_integration import (
    initiate_mpesa_payment, initiate_mtn_payment, initiate_airtel_payment
)
from .mtn_service import get_api_user_info

import paypalrestsdk
import stripe
import requests


logger = logging.getLogger(__name__)

# PayPal setup
import paypalrestsdk
paypalrestsdk.configure({
    "mode": "sandbox",  # Change to "live" in production
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_CLIENT_SECRET
})

# Stripe setup
import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class SubmitReturnRequestView(FormView):
    template_name = 'shop/return_request_form.html'
    form_class = ReturnRequestForm
    success_url = reverse_lazy('some_view_name')  # Replace with your target URL name

    def form_valid(self, form):
        """Process the form data when valid."""
        return_request = form.save(commit=False)
        return_request.user = self.request.user  # Associate with the logged-in user if necessary
        return_request.save()
        messages.success(self.request, 'Your return request has been submitted successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        """Handle invalid form submissions."""
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)

@login_required
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    PageView.objects.create(user=request.user, product=product)
    return render(request, 'shop/product_detail.html', context={'product': product})


@login_required
def mark_as_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect('notifications_list')  # Update URL name as needed

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'shop/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context

class SearchView(View):
    def get(self, request):
        query = request.GET.get('q')
        products = Product.objects.filter(name__icontains=query)  # Modify as needed
        return render(request, 'shop/search_results.html', {'products': products})

def send_verification_email(request):
    user = request.user
    if not user.is_verified:
        # Generate verification token and send email
        token = user.generate_verification_token()
        verification_url = request.build_absolute_uri(reverse('account_verification')) + f'?token={token}'

        # Send the email
        send_mail(
            'Verify Your Account',
            f'Click the link to verify your account: {verification_url}',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )

        messages.success(request, 'Verification email sent! Please check your inbox.')
    else:
        messages.info(request, 'Your account is already verified.')

    return redirect('shop:account_settings')
from django.views.decorators.http import require_GET
@require_GET
def account_verification(request):
    token = request.GET.get('token')
    user = request.user

    if token and user.verify_token(token):
        user.is_verified = True
        user.save()
        messages.success(request, 'Your account has been successfully verified.')
    else:
        messages.error(request, 'Invalid or expired verification link.')

    return render(request, 'shop/account_verification.html')
class AccountVerificationView(View):
    def get(self, request, *args, **kwargs):
        # Logic to check account verification status
        context = {
            'user': request.user,  # Pass the user to the template context
            'messages': messages.get_messages(request)  # Handle messages
        }
        return render(request, 'shop/account_verification.html', context)

class SendVerificationEmailView(View):
    def get(self, request, *args, **kwargs):
        # Handle GET request if necessary (e.g., for rendering a form)
        return JsonResponse({"message": "GET request not allowed for this endpoint."}, status=405)

    def post(self, request, *args, **kwargs):
        # Handle the sending of verification email here
        # Your logic for sending the verification email
        return JsonResponse({"message": "Verification email sent successfully."})
class ResetVerificationStatusView(View):
    def post(self, request, *args, **kwargs):
        # Logic to reset verification status
        # Example: reset_user_verification_status(request.user)
        return JsonResponse({'message': 'Verification status reset successfully.'})
    

def create_order(request):
    if request.method == "POST":
        # Retrieve cart items from the session or however you store them
        cart_items = get_cart_items(request)  # Implement this function to retrieve cart items

        if not cart_items:
            messages.error(request, "Your cart is empty.")
            return redirect('shop:cart')  # Redirect to cart page if cart is empty

        # Process order details from the request
        order = Order.objects.create(
            user=request.user,
            status='Pending',  # Set initial status to pending
            total_amount=calculate_total(cart_items),  # Calculate total from cart items
            estimated_delivery_date=calculate_delivery_date(),  # Get estimated delivery date
        )

        # Create order items based on cart items
        for item in cart_items:
            OrderItem.objects.create(order=order, product=item['product'], quantity=item['quantity'])

        # Optionally, clear the cart after order creation
        clear_cart(request)  # Call the clear_cart function to empty the user's cart

        # Redirect to order confirmation page
        messages.success(request, "Your order has been placed successfully!")
        return redirect('shop:order_confirmation', order_id=order.id)

    # If the request method is not POST, redirect to cart or another appropriate page
    messages.warning(request, "Invalid request method. Please try again.")
    return redirect('shop:cart_view')  # Redirect to cart page

class EditProfileView(LoginRequiredMixin, View):
    template_name = 'shop/edit_profile.html'

    def get_context_data(self, **kwargs):
        user_form = UserUpdateForm(instance=self.request.user)
        profile_form = ProfileUpdateForm(instance=self.request.user.profile)
        return {
            'user_form': user_form,
            'profile_form': profile_form,
        }

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile was successfully updated!')
            return redirect('shop:profile')  # Ensure this matches your URL pattern name
        else:
            messages.error(request, 'Please correct the error below.')
            messages.error(request, user_form.errors.as_text())
            messages.error(request, profile_form.errors.as_text())
            return self.get(request)  # Return the same page with errors

from .models import UserProfile  #
class ProfileView(LoginRequiredMixin, View):
    """
    View to display the user's profile. 
    Only accessible to authenticated users.
    """
    
    def get(self, request):
        # Get the user profile data
        user_profile = UserProfile.objects.get(user=request.user)
        
        context = {
            'user_profile': user_profile,  # Pass the user profile to the template
        }
        
        return render(request, 'shop/profile.html', context)
@login_required
def update_security_questions(request):
    if request.method == 'POST':
        security_question_1 = request.POST.get('security_question_1')
        security_answer_1 = request.POST.get('security_answer_1')
        security_question_2 = request.POST.get('security_question_2')
        security_answer_2 = request.POST.get('security_answer_2')

        # Assuming you have a Profile model related to the User model
        profile = request.user.profile
        profile.security_question_1 = security_question_1
        profile.security_answer_1 = security_answer_1
        profile.security_question_2 = security_question_2
        profile.security_answer_2 = security_answer_2
        profile.save()

        messages.success(request, 'Your security questions have been updated successfully.')
        return redirect('shop:home')  # Redirect to an appropriate page

    return render(request, 'update_security_questions.html')  # Render the template again if not a POST
from django.shortcuts import render, get_object_or_404
from .models import Product  # Ensure you import your Product model

def ar_view(request, product_id):
    # Use product_id to retrieve the product
    product = get_object_or_404(Product, id=product_id)
    
    # Render the product_detail.html template with the product context
    return render(request, 'shop/ar_view.html', {'product': product})
    return render(request, 'login.html', {'form': form})

User = get_user_model()

@login_required
def deactivate_account(request):
    if request.method == 'POST':
        user = request.user
        
        # Add logic to deactivate the account
        user.is_active = False  # Deactivate the account
        user.save()  # Save the changes
        
        messages.success(request, 'Your account has been deactivated successfully.')
        return redirect('shop:home')  # Redirect to the home page or another page

    return render(request, 'deactivate_account.html')  # Render the deactivation page
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, 'Login successful!')
                return redirect('home')  # Redirect to the home page or desired page
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()

    return render(request, 'login.html', {'form': form})
@login_required
def reset_verification(request):
    user = request.user
    user.is_verified = False
    # Optionally set an expiry date for re-verification
    user.verification_expiry = timezone.now() + timedelta(days=1)
    # Generate or reset a verification token if required
    user.verification_token = user.generate_verification_token()  # Assuming a method for token generation
    user.save()
    messages.info(request, "Verification status has been reset. Please verify again.")
    return redirect('shop:account_verification')
@login_required
def send_verification_email(request):
    user = request.user
    if not user.is_verified:
        # Generate a verification link or token
        verification_link = f"{settings.SITE_URL}/verify/{user.pk}/{user.verification_token}/"
        
        # Send email with verification link
        send_mail(
            "Account Verification",
            f"Hi {user.username}, please verify your account using the link: {verification_link}",
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        messages.success(request, "Verification email sent!")
    else:
        messages.info(request, "Your account is already verified.")
    return redirect('shop:account_verification')


def account_settings_view(request: HttpRequest) -> HttpResponse:
    """View for handling account settings updates."""
    if request.method == 'POST':
        form = AccountSettingsForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account settings updated successfully.')
            return redirect('shop:some_view_name')  # Replace with your desired view
    else:
        form = AccountSettingsForm(instance=request.user)

    return render(request, 'shop/account_settings.html', {'form': form})
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
# Discount Code Views
@login_required
def discount_code_list(request):
    # Retrieve all discount codes, assuming only admin can view them
    discount_codes = DiscountCode.objects.all()

    # Optionally, you can check if the user is staff/admin
    if not request.user.is_staff:
        # Optionally, redirect or raise an error if the user is not authorized
        return render(request, 'shop/access_denied.html', status=403)

    return render(request, 'shop/discount_code_list.html', {'discount_codes': discount_codes})
class NotificationListView(View):
    def get(self, request):
        # Fetch notifications for the authenticated user
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')

        # Optionally, you can implement pagination for better performance with many notifications
        # from django.core.paginator import Paginator
        # paginator = Paginator(notifications, 10)  # Show 10 notifications per page
        # page_number = request.GET.get('page')
        # notifications = paginator.get_page(page_number)

        # Render the notifications template with the notifications context
        return render(request, 'shop/notifications.html', {'notifications': notifications})
    def post(self, request, notification_id):
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({'status': 'success'})

def order_history(request):
    # Fetch the user's orders
    orders = Order.objects.filter(user=request.user).order_by('-date_created')  # Adjust the field name as needed

    # Optional: Implement pagination for improved performance with many orders
    # paginator = Paginator(orders, 10)  # Show 10 orders per page
    # page_number = request.GET.get('page')
    # orders = paginator.get_page(page_number)

    # Render the order history template with the orders context
    return render(request, 'shop/order_history.html', {'orders': orders})


def music_view(request, music_id):
    # Fetch the music item or return a 404 error if not found
    music_item = get_object_or_404(Music, id=music_id)
    
    # Optional: Add any additional context data if needed (e.g., related music, genre)
    # related_music = Music.objects.filter(genre=music_item.genre).exclude(id=music_item.id)[:5]  # Example of related music

    # Render the music view template with the music item context
    return render(request, 'shop/music_view.html', {
        'music': music_item,
        # 'related_music': related_music,  # Uncomment to include related music
    })

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
    if request.user.is_authenticated:
        recommended_products = Product.objects.filter(
            is_recommended=True,
            category__in=request.user.preferences.preferred_categories.all()
        ).distinct()
    else:
        recommended_products = Product.objects.filter(is_recommended=True)

    # Debugging output
    print("Recommended Products Query:", recommended_products.query)  # This prints the SQL query
    print("Recommended Products Count:", recommended_products.count())  # This prints the number of products

    context = {
        'recommended_products': recommended_products,
    }
    return render(request, 'shop/recommended_products.html', context)

class EditProfileView(LoginRequiredMixin, UpdateView):
    model = Profile
    form_class = ProfileForm
    template_name = 'shop/edit_profile.html'
    success_url = reverse_lazy('profile')  # Redirect to profile page after successful edit

    def get_object(self, queryset=None):
        """Retrieve the user's profile."""
        return self.request.user.profile  # Get the logged-in user's profile

    def form_valid(self, form):
        """Additional processing after form validation."""
        # Optional: Add any additional processing here, such as logging or sending notifications
        return super().form_valid(form)
@login_required  # This decorator ensures the user is authenticated
def order_history(request):
    """Display the order history for the authenticated user."""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'shop/order_history.html', {'orders': orders})


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

def account_home(request):
    # Logic to retrieve and display account information
    return render(request, 'shop/account_home.html')  # En
from .models import Profile
@login_required
def update_account_settings(request):
    user_profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        # Update user basic information
        request.user.username = request.POST.get('username', request.user.username)
        request.user.email = request.POST.get('email', request.user.email)
        request.user.first_name = request.POST.get('first_name', request.user.first_name)
        request.user.last_name = request.POST.get('last_name', request.user.last_name)
        request.user.bio = request.POST.get('bio', request.user.bio)
        request.user.phone_number = request.POST.get('phone_number', request.user.phone_number)

        # Update password if provided
        password = request.POST.get('password', '').strip()
        if password:
            request.user.set_password(password)

        # Update profile picture if provided
        if request.FILES.get('profile_picture'):
            user_profile.profile_picture = request.FILES['profile_picture']

        # Update additional settings
        user_profile.two_factor_auth = 'two_factor_auth' in request.POST
        user_profile.newsletter = 'newsletter' in request.POST
        user_profile.privacy_settings = request.POST.get('privacy_settings', user_profile.privacy_settings)

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

    return render(request, 'shop/redeem_loyalty_points.html', {'user_points': user_points})

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
class FeedbackThankYouView(TemplateView):
    template_name = 'shop/feedback_thank_you.html'  # Create this template for thank you message
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

import uuid

def create_order(request):
    if request.method == 'POST':
        # Assuming you're gathering other order details from the request
        address = request.POST.get('address')  # Example for address field
        payment_method = request.POST.get('payment_method')  # Example for payment method field
        # Add any other necessary fields

        # Create the order instance
        order = Order.objects.create(
            user=request.user,
            address=address,
            payment_method=payment_method,
            # Include other fields here as necessary
        )

        order.tracking_number = str(uuid.uuid4())  # Generate a tracking number
        order.save()

        # Redirect or render a response after order creation
        return redirect('some_view_name')  # Adjust to your needs
class OrderHistoryView(ListView):
    model = Order
    template_name = 'shop/order_history.html'
    context_object_name = 'orders'  # This will be the context variable in the template

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-order_date')  # Filter orders for the logged-in user

def order_history(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'shop/order_history.html', {'orders': orders})
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
from django.shortcuts import render, get_object_or_404, redirect
from .models import BlogPost, Comment
from .forms import CommentForm  # Create this form later

def blog_list(request):
    posts = BlogPost.objects.all()
    return render(request, 'shop/blog_list.html', {'posts': posts})

def blog_detail(request, post_id):
    post = get_object_or_404(BlogPost, id=post_id)
    related_posts = BlogPost.objects.exclude(id=post_id)[:5]  # Get related posts (customize as needed)
    
    if request.method == 'POST':
        comment = Comment()
        comment.post = post
        comment.user = request.user
        comment.text = request.POST.get('comment')
        comment.save()
        return redirect('shop:blog_detail', post_id=post.id)

    return render(request, 'shop/blog_detail.html', {'post': post, 'related_posts': related_posts})

def blog_view(request):
    """View function for displaying the blog with pagination and comments."""
    all_posts = BlogPost.objects.filter(is_published=True)  # Only get published posts
    paginator = Paginator(all_posts, 5)  # Show 5 posts per page

    page_number = request.GET.get('page')
    paginated_posts = paginator.get_page(page_number)

    # Get comments for the paginated posts
    comments = {post.id: post.comments.filter(is_approved=True) for post in paginated_posts}

    context = {
        'posts': paginated_posts,
        'comments': comments,
    }

    return render(request, 'shop/blog.html', context)
from .models import BlogPost, Comment, NewsletterSubscription 
from django.core.paginator import Paginator

def subscribe(request):
    """View function for handling newsletter subscriptions."""
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            # Validate email format here if needed
            try:
                subscription, created = NewsletterSubscription.objects.get_or_create(email=email)
                if created:
                    messages.success(request, 'Thank you for subscribing!')
                else:
                    messages.info(request, 'You are already subscribed.')
            except Exception as e:
                messages.error(request, f'An error occurred: {str(e)}')
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

login_required
def add_to_wishlist(request, product_id):
    """Add a product to the user's wishlist."""
    product = get_object_or_404(Product, id=product_id)
    
    # Check if the product is already in the wishlist
    if Wishlist.objects.filter(user=request.user, product=product).exists():
        messages.info(request, f"{product.name} is already in your wishlist.")
    else:
        # Create a new wishlist entry
        wishlist_item = Wishlist(user=request.user, product=product, added_date=timezone.now())
        wishlist_item.save()
        messages.success(request, f"{product.name} has been added to your wishlist.")

    return redirect('shop:wishlist_view')  # Adjust this to your wishlist view
from .models import Wishlist, Product

def remove_from_wishlist(request, item_id):
    """Remove an item from the user's wishlist."""
    # Check if the user is authenticated
    if not request.user.is_authenticated:
        messages.error(request, "You must be logged in to remove items from your wishlist.")
        return redirect('shop:login')  # Redirect to login page

    # Get the user's wishlist
    wishlist = get_object_or_404(Wishlist, user=request.user)

    # Get the product to remove
    product = get_object_or_404(Product, id=item_id)

    # Remove the product from the wishlist
    if product in wishlist.products.all():  # Check if the product is in the wishlist
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

class ProductDetailView(View):
    """View for displaying product details."""
    
    def get(self, request, product_id):  # Accept product_id instead of id
        product = get_object_or_404(Product, id=product_id)  # Use product_id here
        context = {
            'product': product,
        }
        return render(request, 'shop/product_detail.html', context)


# PayPal setup
import paypalrestsdk
paypalrestsdk.configure({
    "mode": "sandbox",  # Change to "live" in production
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_CLIENT_SECRET
})

# Stripe setup
import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


def submit_return_request(request):
    if request.method == 'POST':
        form = ReturnRequestForm(request.POST)
        if form.is_valid():
            return_request = form.save(commit=False)
            return_request.save()
            messages.success(request, 'Your return request has been submitted successfully.')
            return redirect('some_view_name')  # Redirect after a successful submission
    else:
        form = ReturnRequestForm()
    return render(request, 'shop/return_request_form.html', {'form': form})


@login_required
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    PageView.objects.create(user=request.user, product=product)
    return render(request, 'shop/product_detail.html', context={'product': product})


@login_required
def mark_as_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect('notifications_list')  # Update URL name as needed


def some_event_triggered(user):
    if user.is_authenticated:
        create_notification(user, "You have a new message!")


@require_POST
def some_action(request):
    """Handle a specific action and return a JSON response."""
    try:
        # Placeholder for action logic
        return JsonResponse({'message': 'Action performed successfully!'}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def create_notification(user, message):
    try:
        notification = Notification.objects.create(user=user, message=message)
        logger.info(f"Notification created for user {user.username}: {message}")
        return notification
    except ObjectDoesNotExist:
        logger.error(f"User {user} does not exist while creating notification.")
    except Exception as e:
        logger.error(f"Error creating notification for user {user.username}: {str(e)}")


@login_required
def feedback_view(request):
    if request.method == 'POST':
        feedback_content = request.POST.get('feedback')
        if feedback_content:
            Feedback.objects.create(user=request.user, feedback_text=feedback_content)
            messages.success(request, "Thank you for your feedback!")
            return redirect('shop:feedback_thank_you')
        else:
            messages.error(request, "Feedback cannot be empty.")
    return render(request, 'shop/feedback_form.html')


def thank_you_view(request):
    return render(request, 'shop/feedback_thank_you.html')


def home(request):
    user_preference = UserPreference.objects.filter(user=request.user).first() if request.user.is_authenticated else None
    products = user_preference.recommended_products.all() if user_preference and user_preference.recommended_products.exists() else Product.objects.all()
    return render(request, 'shop/home.html', {'products': products})


def about(request):
    return render(request, 'shop/about.html')


def shop(request):
    product_list = Product.objects.all()
    paginator = Paginator(product_list, 12)  # Show 12 products per page
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)
    return render(request, 'shop/shop.html', {'products': products})


def contact(request):
    return render(request, 'shop/contact.html')


def add_to_cart(request, product_id):
    """Add a product to the user's cart."""
    product = get_object_or_404(Product, id=product_id)

    if product.stock <= 0:
        messages.warning(request, "Sorry, this product is out of stock.")
        return redirect('shop:product_detail', product_id=product.id)

    # Retrieve the cart from the session
    cart = request.session.get('cart', {})

    # Update cart
    if product_id in cart:
        cart[product_id]['quantity'] += 1
    else:
        cart[product_id] = {
            'name': product.name,
            'price': str(product.price),
            'quantity': 1,
        }

    request.session['cart'] = cart  # Save the updated cart to the session

    messages.success(request, f"{product.name} has been added to your cart.")
    return redirect('shop:cart_view')

def cart_view(request):
    """View to display the shopping cart."""
    # Retrieve the cart from the session
    cart = request.session.get('cart', {})
    items = []  # List to hold items with detailed information

    # Loop through the cart to prepare item details
    for product_id, item in cart.items():
        items.append({
            'id': product_id,
            'name': item['name'],
            'price': float(item['price']),  # Ensure price is a float
            'quantity': item['quantity'],
            'total_price': float(item['price']) * item['quantity'],  # Calculate total price for this item
        })

    # Calculate total items and total price
    total_items = sum(item['quantity'] for item in items)
    total_price = sum(item['total_price'] for item in items)

    # Fetch recommended products based on user preferences or history
    recommended_products = get_recommended_products(request.user)

    # Prepare context for rendering
    context = {
        'cart': {
            'items': items,            # Access this in the template as cart.items
            'total_items': total_items,
            'total_price': total_price,
        },
        'recommended_products': recommended_products,  # Populate with recommended products
    }

    return render(request, 'shop/cart_view.html', context)

def get_recommended_products(user):
    """Function to get recommended products based on the user's preferences or history."""
    if user.is_authenticated:
        # Fetch the IDs of products that the user has purchased
        purchased_product_ids = user.purchased_products.values_list('id', flat=True)  # Adjust according to your User model
        
        # Query for products that the user has not purchased yet
        recommended = Product.objects.exclude(id__in=purchased_product_ids).order_by('?')[:4]  # Randomly select 4 products
        
        return recommended
    else:
        # Return an empty queryset if the user is not authenticated
        return Product.objects.none()
# Update Cart Item
@login_required
def update_cart_item(request, item_id):
    """Update the quantity of an item in the shopping cart."""
    cart_item = get_object_or_404(CartItem, id=item_id)

    if request.method == 'POST':
        quantity_input = request.POST.get('quantity', '1')  # Default to '1' as string

        try:
            new_quantity = int(quantity_input)
            if new_quantity < 1:
                messages.error(request, "Quantity must be at least 1.")
            else:
                cart_item.quantity = new_quantity
                cart_item.save()
                messages.success(request, f"Quantity for {cart_item.product.name} has been updated to {new_quantity}.")
        except ValueError:
            messages.error(request, "Invalid quantity. Please enter a valid number.")

    return redirect('shop:cart_view')

def get_recommended_products(cart):
    """Get recommended products based on the last product added to the cart."""
    recommended_products = []

    # Check if the cart is not empty
    if cart:
        # Get the product ID of the last added item in the cart
        last_product_id = next(iter(cart))  # Adjust this if you want a specific "last added" logic

        # Safely retrieve the last product
        try:
            last_product = Product.objects.get(id=last_product_id)  # Use get instead of get_object_or_404 for flexibility
        except Product.DoesNotExist:
            return recommended_products  # Return empty if the last product does not exist

        # Fetch products in the same category, excluding the last added product and filtering by stock
        recommended_products = (
            Product.objects
            .filter(category=last_product.category)
            .exclude(id=last_product.id)
            .filter(stock__gt=0)  # Filter for products with stock greater than 0
            [:4]  # Limit to 4 recommendations
        )

    return recommended_products
def cart_view(request):
    """View to display the shopping cart."""
    # Retrieve the cart from the session
    cart = request.session.get('cart', {})
    items = []  # List to hold items with detailed information

    # Loop through the cart to prepare item details
    for product_id, item in cart.items():
        try:
            product = Product.objects.get(id=product_id)  # Fetch product details
            items.append({
                'id': product.id,
                'name': product.name,
                'price': product.price,
                'quantity': item['quantity'],
                'total_price': product.price * item['quantity'],  # Calculate total price for this item
            })
        except Product.DoesNotExist:
            messages.warning(request, f"Product with ID {product_id} not found. It has been removed from your cart.")

    # Calculate total items and total price
    total_items = sum(item['quantity'] for item in items)
    total_price = sum(item['total_price'] for item in items)

    # Get recommended products based on the cart
    recommended_products = get_recommended_products(cart)

    # Prepare context for rendering
    context = {
        'cart': {
            'items': items,
            'total_items': total_items,
            'total_price': total_price,
        },
        'recommended_products': recommended_products,
    }

    return render(request, 'shop/cart_view.html', context)

import logging




logger = logging.getLogger(__name__)

def remove_from_cart(request, item_id):
    """Remove an item from the user's cart."""
    logger.debug(f"Attempting to remove CartItem with ID: {item_id}")

    try:
        cart_item = get_object_or_404(CartItem, id=item_id)
        logger.debug(f"Found CartItem: {cart_item}")

        if cart_item.cart.user == request.user:
            cart_item.delete()
            message = f"{cart_item.product.name} has been removed from your cart."
            messages.success(request, message)
            logger.info(f"Removed item: {cart_item.product.name} from cart of {request.user.username}.")

            # Check if request is an AJAX request
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success', 'message': message})

        else:
            error_message = "You do not have permission to remove this item."
            messages.error(request, error_message)
            logger.warning(f"User {request.user.username} tried to remove item from another user's cart.")

            # Respond with JSON for AJAX requests
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': error_message})

    except Exception as e:
        error_message = "An unexpected error occurred while trying to remove the item."
        messages.error(request, error_message)
        logger.error(f"Error removing item {item_id}: {e}")

        # Respond with JSON for AJAX requests
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': error_message})

    # Redirect for non-AJAX requests
    return redirect('shop:cart_view')


def checkout_view(request):
    if request.method == 'POST':
        # Retrieve payment configuration
        BASE_URL = settings.MOBILE_MONEY_CONFIG['API_BASE_URL']
        API_USER_ID = 'c72025f5-5cd1-4630-99e4-8ba4722fad56'
        SUBSCRIPTION_KEY = settings.MOBILE_MONEY_CONFIG['MTN_API_KEY']

        # Get selected currency and amount from the form (default values if not provided)
        amount = request.POST.get('amount', 100)  # Defaulting to 100
        currency = request.POST.get('currency', 'UGX')  # Default to Uganda Shilling (UGX)
        payment_method = request.POST.get('payment_method')

        # Ensure the amount is a valid number
        try:
            amount = float(amount)
        except ValueError:
            return JsonResponse({'error': 'Invalid amount'}, status=400)

        # Retrieve shipping address details
        shipping_name = request.POST.get('shipping_name')
        shipping_address = request.POST.get('shipping_address')
        shipping_city = request.POST.get('shipping_city')
        shipping_region = request.POST.get('shipping_region')
        shipping_zip = request.POST.get('shipping_zip')

        # Optionally handle gift options
        is_gift = request.POST.get('is_gift', False) == 'on'
        gift_message = request.POST.get('gift_message', '')
        recipient_email = request.POST.get('recipient_email', '')

        # Initialize order
        order = Order(
            user=request.user,
            total_price=amount,
            status='pending',
            payment_status='pending',
            shipping_name=shipping_name,
            shipping_address=shipping_address,
            shipping_city=shipping_city,
            shipping_region=shipping_region,
            shipping_zip=shipping_zip,
            is_gift=is_gift,
            gift_message=gift_message,
            recipient_email=recipient_email
        )
        order.payment_method = payment_method
        order.is_payment_required = payment_method != 'cod'  # No payment required for COD
        order.save()

        # If payment method is COD, handle accordingly
        if payment_method == 'cod':  # Pay on Delivery
            logger.info(f"Order placed without payment for order #{order.id} with amount {amount} {currency}")
            return JsonResponse({'success': True, 'message': 'Order placed successfully, payment due on delivery.', 'order_id': order.id})

        # Otherwise, proceed with immediate payment (for example, MTN)
        url = f"{BASE_URL}/{API_USER_ID}/mtn/initiate"  # Ensure the URL is correctly formatted
        headers = {
            'Ocp-Apim-Subscription-Key': SUBSCRIPTION_KEY,
            'Content-Type': 'application/json',
        }
        payload = {
            'amount': amount,
            'currency': currency,
            'description': f'Payment for order #{order.id}',
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            payment_data = response.json()

            # Check for expected fields in payment_data
            if 'expected_field' not in payment_data:  # Replace with actual expected field check
                raise ValueError("Unexpected response structure")

            order.payment_status = 'initiated'  # Update payment status if needed
            order.save()

            logger.info(f"Payment initiated for order #{order.id} with amount {amount} {currency}")

            return JsonResponse({'success': True, 'data': payment_data, 'order_id': order.id})

        except requests.exceptions.RequestException as e:
            order.payment_status = 'failed'  # Update the order status to failed
            order.save()
            logger.error(f"Payment failed for order #{order.id}: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)

    # Add the supported currencies to pass to the template
    supported_currencies = ['UGX', 'USD', 'KES', 'TZS']  # Supported currencies

    return render(request, 'shop/checkout.html', {'supported_currencies': supported_currencies})

def mtn_view(request):
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        amount = request.POST.get('amount')
        currency = request.POST.get('currency')

        # Set up API details
        BASE_URL = settings.MOBILE_MONEY_CONFIG['API_BASE_URL']
        API_USER_ID = 'c72025f5-5cd1-4630-99e4-8ba4722fad56'
        SUBSCRIPTION_KEY = settings.MOBILE_MONEY_CONFIG['MTN_API_KEY']

        url = f"{BASE_URL}{API_USER_ID}/mtn/initiate"
        headers = {
            'Ocp-Apim-Subscription-Key': SUBSCRIPTION_KEY,
            'Content-Type': 'application/json',
        }
        payload = {
            'amount': amount,
            'currency': currency,
            'description': 'Payment for order',
            'phone_number': phone_number,
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            messages.success(request, f"Payment of {amount} {currency} initiated successfully!")
            return redirect('shop:payment_success')  # Redirect to a success page
        except requests.exceptions.RequestException as e:
            messages.error(request, f"Error initiating payment: {str(e)}")

    # Render the payment form with any messages
    return render(request, 'mtn.html', {
        'supported_currencies': ['UGX', 'USD', 'KES', 'TZS'],  # Example supported currencies
    })
#@login_required
class ProfileView(LoginRequiredMixin, View):
    """View for displaying the user's profile."""
    template_name = 'shop/profile.html'  # Adjust the path as necessary

    def get_context_data(self, **kwargs):
        """Add any additional context data needed for the profile view."""
        user_form = UserUpdateForm(instance=self.request.user)
        profile_form = ProfileUpdateForm(instance=self.request.user.profile)
        reviews = Review.objects.filter(user=self.request.user)
        orders = Order.objects.filter(user=self.request.user)

        context = {
            'user_form': user_form,
            'profile_form': profile_form,
            'reviews': reviews,
            'orders': orders,
        }
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return render(request, self.template_name, context)

class EditProfileView(LoginRequiredMixin, View):
    """View for editing the user's profile."""
    template_name = 'shop/edit_profile.html'  # Adjust the path as necessary

    def get_context_data(self, **kwargs):
        """Add the forms to the context for the edit profile view."""
        user_form = UserUpdateForm(instance=self.request.user)
        profile_form = ProfileUpdateForm(instance=self.request.user.profile)

        return {
            'user_form': user_form,
            'profile_form': profile_form,
        }

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile was successfully updated!')
            return redirect('shop:profile')
        else:
            messages.error(request, 'Please correct the error below.')
            messages.error(request, user_form.errors.as_text())
            messages.error(request, profile_form.errors.as_text())
            return self.get(request)  # Return the same page with errors
        
@login_required  # Ensure only logged-in users can access this view
def update_profile_picture(request):
    if request.method == 'POST':
        form = ProfileImageForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            return redirect('profile')  # Redirect to the profile page after saving
    else:
        form = ProfileImageForm(instance=request.user.profile)
    return render(request, 'shop/profile.html', {'form': form})

class ProductDetailView(View):
    def get(self, request, *args, **kwargs):
        # Get the product ID (primary key) from the URL kwargs
        product_id = kwargs.get('pk')

        # Retrieve the product, or return a 404 if not found
        product = get_object_or_404(Product, pk=product_id)
        
        # Increment the view count
        product.view_count += 1
        product.save()

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
        product_id = kwargs.get('pk')
        product = get_object_or_404(Product, pk=product_id)
        review_form = ReviewForm(request.POST)

        if review_form.is_valid():
            # Create a new review and associate it with the product
            review = review_form.save(commit=False)
            review.product = product
            review.user = request.user  # Assuming you have user authentication
            review.save()
            return redirect('shop:product_detail', pk=product_id)  # Redirect to the same product detail page

        # If the form is not valid, re-render the page with the existing data
        average_rating = product.reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
        
        context = {
            'product': product,
            'average_rating': average_rating,
            'related_products': related_products,
            'reviews': product.reviews.all(),
            'form': review_form,  # Pass the invalid form with errors to the template
        }
        
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
    return render(request, 'shop/account_setings.html')  # Adjust the template name as necessary
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


# Notification View
@login_required
def notification_list(request):
    # Fetch notifications for the logged-in user
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')

    # Set up pagination
    paginator = Paginator(notifications, 10)  # Show 10 notifications per page
    page_number = request.GET.get('page')  # Get the current page number from the query string
    page_obj = paginator.get_page(page_number)  # Get the specific page of notifications

    return render(request, 'shop/notification.html', {
        'page_obj': page_obj,
        'notifications': notifications,
    })

# AR (Augmented Reality) View for products
def ar_product_view(request, product_id):
    # Fetch the product using the provided product ID
    product = get_object_or_404(Product, id=product_id)
    
    # Check if the product is available for AR view
    if not product.is_available:  # Assuming you have an 'is_available' field
        messages.warning(request, 'This product is currently unavailable for AR view.')
        return render(request, 'shop/ar_view.html', {'product': None})

    # Render the AR view template with the product details
    return render(request, 'shop/ar_view.html', {'product': product})

@login_required
def apply_discount_code(request, code):
    discount_code = get_object_or_404(DiscountCode, code=code)

    # Example: Assume you have a cart associated with the user
    cart = Cart.objects.filter(user=request.user).first()  # Get the user's cart

    if cart:  # Check if the cart exists
        if discount_code.is_active and discount_code.expiration_date > timezone.now():  # Check if the code is valid
            # Apply discount logic (example: apply discount amount to the cart total)
            cart.total -= discount_code.discount_amount
            cart.save()
            messages.success(request, f"Discount code '{code}' applied successfully!")
        else:
            messages.error(request, "This discount code is either inactive or expired.")
    else:
        messages.error(request, "No cart found for your account.")

    return redirect('shop:cart_view')  # Redirect to the cart view
# Loyalty Points Views
@login_required
def loyalty_points_list(request):
    loyalty_points = LoyaltyPoints.objects.filter(user=request.user)
    total_points = sum(point.points for point in loyalty_points)  # Calculate total loyalty points
    return render(request, 'shop/loyalty_points_list.html', {
        'loyalty_points': loyalty_points,
        'total_points': total_points,  # Pass total points to the template
    })
from django.db import transaction
from django.contrib import messages
from .models import LoyaltyPoints, Purchase 
@login_required
def complete_purchase(request):
    # Assume you handle the purchase logic here
    # For example, creating a Purchase object

    with transaction.atomic():  # Ensure all operations are atomic
        # Logic to handle the purchase, e.g., creating a Purchase record
        purchase = Purchase.objects.create(user=request.user, total_amount=100)  # Example

        # Award loyalty points (example: 1 point for every 10 units spent)
        loyalty_points_awarded = purchase.total_amount // 10
        LoyaltyPoints.objects.create(user=request.user, points=loyalty_points_awarded)

        messages.success(request, f"You have earned {loyalty_points_awarded} loyalty points!")

    return redirect('shop:order_confirmation')  # Redirect to an order confirmation page
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

    # Pagination
    paginator = Paginator(music_files, 10)  # Show 10 music files per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'shop/music_list.html', {'page_obj': page_obj})

login_required
def chat_room(request, room_name):
    # Fetch any necessary data related to the chat room here (if applicable)
    return render(request, 'shop/chat_room.html', {'room_name': room_name, 'user': request.user})


class TrackOrderView(LoginRequiredMixin, View):
    """View for tracking orders."""

    def get(self, request):
        order_id = request.GET.get('order_id')  # Get order_id from query parameters
        order = None
        
        if order_id:
            order = get_object_or_404(Order, id=order_id, user=request.user)  # Ensure the order belongs to the user

        return render(request, 'shop/track_order.html', {'order': order})
class ReturnsView(View):
    def get(self, request):
        # Add your logic for handling returns here
        return render(request, 'shop/returns.html')  # Ensure you have this template
    

class GiftCardsView(View):
    """View to handle the display of gift cards."""

    template_name = 'shop/gift_cards.html'  # Template for the gift cards page

    def get(self, request):
        """Handle GET requests for the gift cards page."""
        context = self.get_context_data()
        return render(request, self.template_name, context)

    def get_context_data(self, **kwargs):
        """Prepare context data for rendering."""
        context = {
            'page_title': 'Gift Cards',  # You can pass additional context variables here
            # Add more context variables as needed
        }
        context.update(kwargs)  # Update context with any additional keyword arguments
        return context
class RecommendedProductsView(View):
    """View to display recommended products."""
    template_name = 'shop/recommended_products.html'

    def get(self, request):
        """Handle GET requests for recommended products."""
        context = self.get_context_data()
        return render(request, self.template_name, context)

    def get_context_data(self, **kwargs):
        """Prepare context data for rendering."""
        context = {
            'page_title': 'Recommended Products',
            # You can fetch and add actual recommended products here
        }
        context.update(kwargs)
        return context
class BlogView(View):
    """View to display the blog page."""
    template_name = 'shop/blog.html'  # Specify your blog template

    def get(self, request):
        """Handle GET requests for the blog page."""
        context = self.get_context_data()
        return render(request, self.template_name, context)

    def get_context_data(self, **kwargs):
        """Prepare context data for rendering."""
        context = {
            'page_title': 'Blog',
            # You can fetch and add actual blog posts here
        }
        context.update(kwargs)
        return context
class CartView(View):
    """View to display the shopping cart."""
    template_name = 'shop/cart.html'  # Specify your cart template

    def get(self, request):
        """Handle GET requests for the cart page."""
        context = self.get_context_data()
        return render(request, self.template_name, context)

    def get_context_data(self, **kwargs):
        """Prepare context data for rendering."""
        context = {
            'page_title': 'Shopping Cart',
            # Add any context data needed for the cart
        }
        context.update(kwargs)
        return context
    
class ChatRoomView(View):
    """View to handle the chat room functionality."""
    template_name = 'shop/chat_room.html'  # Specify your chat room template

    def get(self, request, room_name):
        """Handle GET requests for the chat room page."""
        context = {
            'room_name': room_name,  # Pass the room name to the context
            # Add any other context data needed for the chat room
        }
        return render(request, self.template_name, context)
class PrivacyPolicyView(View):
    """View to handle the privacy policy page."""
    template_name = 'shop/privacy_policy.html'  # Specify your privacy policy template

    def get(self, request):
        """Handle GET requests for the privacy policy page."""
        return render(request, self.template_name)
class CheckoutView(View):
    """View to handle the checkout process."""
    template_name = 'shop/checkout.html'  # Specify your checkout template

    def get(self, request):
        """Handle GET requests for the checkout page."""
        return render(request, self.template_name)
class NotificationView(View):
    """View to handle user notifications."""
    template_name = 'shop/notifications.html'  # Specify your notifications template

    def get(self, request):
        """Handle GET requests for the notifications page."""
        # Add any logic to retrieve notifications here
        return render(request, self.template_name)
    
    # views.py


from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

@method_decorator(login_required, name='dispatch')  # Ensure the user is logged in
class UpdateAccountSettingsView(View):
    """View to handle updating user account settings."""
    def get(self, request):
        """Render the account settings form."""
        return render(request, 'shop/account_settings.html')

    def post(self, request):
        """Handle the form submission to update account settings."""
        # Implement your logic for updating user details here
        user = request.user
        user.username = request.POST.get('username', user.username)
        user.email = request.POST.get('email', user.email)
        user.save()  # Save updated user information
        return redirect('shop:account_settings')  # Redirect to the account settings page
    
@method_decorator(login_required, name='dispatch')  # Ensure the user is logged in
class DeleteAccountView(View):
    """View to handle account deletion."""
    def post(self, request):
        """Handle the account deletion."""
        user = request.user
        user.delete()  # Delete the user account
        messages.success(request, "Your account has been deleted successfully.")
        return redirect('shop:home')  # Redirect to home or another page
@method_decorator(login_required, name='dispatch')  # Ensure the user is logged in
class AddPaymentMethodView(View):
    """View to handle adding a payment method."""
    def post(self, request):
        """Handle the payment method addition."""
        card_number = request.POST.get('card_number')
        expiry_date = request.POST.get('expiry_date')

        # Here, add your logic to save the payment method
        # Example: user.profile.payment_methods.create(card_number=card_number, expiry_date=expiry_date)

        messages.success(request, "Payment method added successfully.")
        return redirect('shop:account_settings')  # Redirect to account settings or another page
    
class SubscribeView(View):
    """View to handle newsletter subscriptions."""

    def post(self, request):
        """Handle subscription post request."""
        email = request.POST.get('email')

        # Here you would typically save the email to a database or subscription list
        # For example: NewsletterSubscription.objects.create(email=email)

        messages.success(request, "Thank you for subscribing to our newsletter!")
        return redirect('shop:blog')  # Redirect to the blog page or another page
class AddShippingAddressView(View):
    """View to handle adding shipping addresses."""

    def post(self, request):
        """Handle adding a shipping address."""
        address = request.POST.get('address')
        city = request.POST.get('city')
        
        # Here you would typically save the address to the user's profile
        # Example: request.user.profile.shipping_addresses.create(address=address, city=city)

        messages.success(request, "Shipping address added successfully!")
        return redirect('shop:account_settings')  # Redirect to the account settings page
class ResetVerificationView(View):
    """View to handle resetting the verification status."""

    def post(self, request):
        """Handle resetting the verification status."""
        user = request.user
        
        # Resetting the verification status
        user.is_verified = False  # Example: Setting the user as not verified
        user.save()

        messages.success(request, "Verification status has been reset.")
        return redirect('shop:account_settings')  # Redirect to the account settings page
@method_decorator(login_required, name='dispatch')  # Ensure the user is logged in
class GenerateReferralLinkView(View):
    """View to handle generating referral links."""

    def post(self, request):
        """Handle generating a referral link."""
        user = request.user
        
        # Generate a referral link (example implementation)
        referral_link = f"http://127.0.0.1:8000/referral/{user.id}/"  # Updated referral link
  # Customize as needed

        # You might want to save the referral link to the user's profile or notify them
        # user.profile.referral_link = referral_link
        # user.profile.save()

        messages.success(request, f"Your referral link: {referral_link}")
        return redirect('shop:account_settings')  # Redirect to the account settings page
@method_decorator(login_required, name='dispatch')  # Ensure the user is logged in
class UpdateSecurityQuestionsView(View):
    """View to handle updating security questions."""

    def post(self, request):
        """Handle updating security questions."""
        user = request.user
        question1 = request.POST.get('question1')
        answer1 = request.POST.get('answer1')
        question2 = request.POST.get('question2')
        answer2 = request.POST.get('answer2')

        # Update the user's security questions (example implementation)
        user.profile.security_question_1 = question1
        user.profile.security_answer_1 = answer1
        user.profile.security_question_2 = question2
        user.profile.security_answer_2 = answer2
        user.profile.save()

        messages.success(request, "Your security questions have been updated successfully.")
        return redirect('shop:account_settings')  # Redirect to the account settings page
class SubmitFeedbackView(View):
    """View to handle submitting feedback."""

    def post(self, request):
        """Handle submitting feedback."""
        user = request.user
        feedback_text = request.POST.get('feedback_text')

        # Create and save the feedback instance
        feedback = Feedback(user=user, feedback_text=feedback_text)
        feedback.save()

        messages.success(request, "Your feedback has been submitted successfully.")
        return redirect('shop:account_settings')  # Redirect to the account settings or desired page
class LinkSocialAccountView(View):
    """View to handle linking a social account."""

    @login_required  # Ensure the user is logged in
    def post(self, request):
        """Handle linking a social account."""
        social_account_type = request.POST.get('social_account_type')  # Example: 'twitter', 'facebook', etc.
        account_token = request.POST.get('account_token')  # Token or identifier from social account

        # Logic to link the social account (implementation may vary)
        # Example: Link the account to the user's profile
        user = request.user
        # Your linking logic here, e.g., updating the user's profile with social account info.

        messages.success(request, f"{social_account_type.capitalize()} account linked successfully.")
        return redirect('shop:account_settings')  # Redirect to account settings or desired page
class UpdateAccessibilityView(View):
    """View to handle updating accessibility settings."""

    @login_required  # Ensure the user is logged in
    def post(self, request):
        """Handle the form submission for accessibility settings."""
        accessibility_option = request.POST.get('accessibility_option')  # Example option

        # Logic to update the user's accessibility settings
        user_profile = request.user.profile  # Assuming you have a Profile model linked to User
        user_profile.accessibility_option = accessibility_option  # Update with new value
        user_profile.save()

        messages.success(request, "Accessibility settings updated successfully.")
        return redirect('shop:account_settings')  # Redirect to the account settings or desired page
    
from django.views.generic import DetailView
class ProductDetailView(DetailView):
    model = Product
    template_name = 'shop/product_detail.html'
    context_object_name = 'product'
from .models import Product, Wishlist

def add_to_wishlist(request, product_id):
    if request.method == 'POST' and request.user.is_authenticated:
        product = get_object_or_404(Product, id=product_id)
        Wishlist.objects.create(user=request.user, product=product)  # Ensure product is not None
        return redirect('shop:wishlist')  # Redirect to the wishlist page
    return redirect('shop:product_detail', pk=product_id)  # Redirect to product detail if not authenticated
def ar_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    # Your logic here
    return render(request, 'shop/ar_view.html', {'product': product})


def order_confirmation(request, order_id):
    """Display the order confirmation."""
    order = get_object_or_404(Order, id=order_id, user=request.user)  # Ensure the order belongs to the user
    order_items = order.order_items.all()  # Get related order items
    return render(request, 'shop/order_confirmation.html', {'order': order, 'order_items': order_items})

class SignupView(View):
    def get(self, request):
        form = UserCreationForm()  # Create an instance of the user creation form
        return render(request, 'shop/signup.html', {'form': form})  # Pass the form to the template

    def post(self, request):
        form = UserCreationForm(request.POST)  # Create a form instance with submitted data
        if form.is_valid():
            user = form.save()  # Save the user
            login(request, user)  # Log in the user after signup
            messages.success(request, 'Account created successfully! You are now logged in.')
            return redirect('shop:home')  # Redirect to the home page or any other page
        else:
            messages.error(request, 'Please correct the errors below.')  # Add error message if form is not valid
        
        return render(request, 'shop/signup.html', {'form': form})  # Re-render the form with errors

class ProductListView(ListView):
    model = Product
    template_name = 'shop/product_list.html'  # Adjust the path as needed
    context_object_name = 'products'  # This will be used in the template
from .models import UserPoints 

def redeem_loyalty_points_view(request):
    if request.method == 'POST':
        try:
            points_to_redeem = int(request.POST.get('points', 0))
            if points_to_redeem <= 0:
                messages.error(request, "Please enter a valid number of points to redeem.")
                return redirect('shop:redeem_loyalty_points')
                
            user_points, created = UserPoints.objects.get_or_create(user=request.user)

            if user_points.points >= points_to_redeem:
                user_points.points -= points_to_redeem
                user_points.save()
                messages.success(request, f"You have successfully redeemed {points_to_redeem} points!")
            else:
                messages.error(request, "You do not have enough points to redeem.")
        except ValueError:
            messages.error(request, "Invalid input for points. Please enter a number.")
        
        return redirect('shop:redeem_points')  # Redirect after POST to prevent resubmission

    # Retrieve user's current points
    user_points = UserPoints.objects.filter(user=request.user).first()

    return render(request, 'shop/redeem_points.html', {'user_points': user_points})

def loyalty_terms_view(request):
    return render(request, 'shop/loyalty_terms.html')
class MostViewedProductsView(ListView):
    model = Product
    template_name = 'shop/most_viewed_products.html'  # Ensure this template exists
    context_object_name = 'most_viewed_products'

    def get_queryset(self):
        # Retrieve products ordered by the number of views, descending
        return Product.objects.order_by('-views')[:10]  # Adjust as needed


