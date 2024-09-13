from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views import View
from django.http import JsonResponse
from .forms import CustomUserCreationForm, UserUpdateForm, ProfileUpdateForm, MusicForm, UserPreferenceForm, ReviewForm
from .models import Product, Cart, CartItem, Review, Order, Category, UserPreference, Music
from .payment_integration import initiate_mpesa_payment, initiate_mtn_payment, initiate_airtel_payment

# Chat bot view
def chat_bot_view(request):
    if request.method == 'POST':
        user_message = request.POST.get('message', '')

        # Bot auto-response logic
        if "hello" in user_message.lower():
            response = "Hello! How can I help you today?"
        elif "bye" in user_message.lower():
            response = "Goodbye! Have a nice day!"
        else:
            response = "I don't understand that."

        return JsonResponse({'response': response})
    return JsonResponse({'error': 'Invalid request'})

# Set Stripe API key
import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

# Custom logout view
@login_required
def custom_logout(request):
    logout(request)
    return redirect('shop:home')

# Register view
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Log in the user immediately after registration
            return redirect('shop:home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'shop/register.html', {'form': form})

# Update cart item
@login_required
def update_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    if request.method == 'POST':
        new_quantity = int(request.POST.get('quantity', 1))
        cart_item.quantity = new_quantity
        cart_item.save()
    return redirect('shop:cart_view')

# Remove item from cart
@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart_item.delete()
    return redirect('shop:cart_view')

# Cart view
class CartView(View):
    def get(self, request):
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart)
        cart_total = sum(item.product.price * item.quantity for item in cart_items)
        return render(request, 'shop/cart.html', {
            'cart': cart,
            'cart_items': cart_items,
            'cart_total': cart_total
        })

# Add to cart
@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 1}
    )
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    return redirect('shop:cart_view')

# About view
def about(request):
    return render(request, 'shop/about.html')

# Shop view
def shop(request):
    products = Product.objects.all()
    return render(request, 'shop/shop.html', {'products': products})

# Contact view
def contact(request):
    return render(request, 'shop/contact.html')

# Home view
def home(request):
    user_preference = UserPreference.objects.filter(user=request.user).first() if request.user.is_authenticated else None
    if user_preference and user_preference.recommended_products.exists():
        products = user_preference.recommended_products.all()
    else:
        products = Product.objects.all()
    return render(request, 'shop/home.html', {'products': products})

# Payment success view
def payment_success(request):
    return render(request, 'shop/payment_success.html')

# Payment failure view
def payment_failure(request):
    return render(request, 'shop/payment_failure.html')

# Checkout view
@login_required
def checkout(request):
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        amount = request.POST.get('amount')
        order_id = 'order123'  # Generate or use a real order ID

        payment_method = request.POST.get('payment_method')
        if payment_method == 'mpesa':
            response = initiate_mpesa_payment(phone_number, amount, order_id)
        elif payment_method == 'mtn':
            response = initiate_mtn_payment(phone_number, amount, order_id)
        elif payment_method == 'airtel':
            response = initiate_airtel_payment(phone_number, amount, order_id)
        else:
            response = {'status': 'error', 'message': 'Invalid payment method'}

        if response.get('status') == 'success':
            return redirect('shop:payment_success')
        else:
            return redirect('shop:payment_failure')

    return render(request, 'shop/checkout.html')

# AR View
def ar_view(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'shop/ar_view.html', {'product': product})

# Update preferences
@login_required
def update_preferences(request):
    user_preference, created = UserPreference.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserPreferenceForm(request.POST, instance=user_preference)
        if form.is_valid():
            form.save()
            return redirect('shop:home')
    else:
        form = UserPreferenceForm(instance=user_preference)

    return render(request, 'shop/update_preferences.html', {'form': form})

# Upload music
def upload_music(request):
    if request.method == 'POST':
        form = MusicForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('shop:music_list')
    else:
        form = MusicForm()
    return render(request, 'shop/upload_music.html', {'form': form})

# Music list
def music_list(request):
    musics = Music.objects.all()
    return render(request, 'shop/music_list.html', {'musics': musics})

# Chat room
def chat_room(request, room_name):
    return render(request, 'shop/chat_room.html', {'room_name': room_name})

# Product list
def product_list(request):
    query = request.GET.get('q')
    category = request.GET.get('category')

    products = Product.objects.all()
    categories = Category.objects.all()

    if query:
        products = products.filter(name__icontains=query)
    if category:
        products = products.filter(category__name=category)

    return render(request, 'shop/product_list.html', {'products': products, 'categories': categories})

# Profile view
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

    return render(request, 'shop/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })

# Add review
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

# Product detail
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'shop/product_detail.html', {'product': product})

# Order history
def order_history(request):
    if not request.user.is_authenticated:
        return redirect('shop:login')  # Redirect to login if user is not authenticated

    # Fetch orders for the authenticated user
    orders = Order.objects.filter(user=request.user)
    return render(request, 'shop/order_history.html', {'orders': orders})

def chat_room(request, room_name):
    return render(request, 'shop/chat_room.html', {
        'room_name': room_name
    })
