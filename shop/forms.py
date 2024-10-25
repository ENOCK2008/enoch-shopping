from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import (
    Product,
    Review,
    Profile,
    Music,
    UserPreference,
    DiscountCode,
    Feedback,
    LoyaltyPoints,
    ReturnRequest,  # Ensure this is imported correctly
)

# Profile Form
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            'phone_number',
            'address',
            'email_notifications',
            'sms_notifications',
            'push_notifications'
        ]
        widgets = {
            'phone_number': forms.TextInput(attrs={'placeholder': 'Enter your phone number'}),
            'address': forms.TextInput(attrs={'placeholder': 'Enter your address'}),
        }

# Profile Image Form
class ProfileImageForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_picture']

# Feedback Form
class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['content']  # Ensure this matches your Feedback model's field name
        widgets = {
            'content': forms.Textarea(attrs={'placeholder': 'Leave your feedback here...', 'rows': 3}),
        }

# Discount Code Form
class DiscountCodeForm(forms.ModelForm):
    class Meta:
        model = DiscountCode
        fields = ['code', 'discount_amount', 'start_date', 'end_date', 'active']  # Adjusted based on your model

# Custom User Creation Form
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']  # Required fields for user creation
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Choose a username'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Your email address'}),
            'password1': forms.PasswordInput(attrs={'placeholder': 'Create a password'}),
            'password2': forms.PasswordInput(attrs={'placeholder': 'Confirm your password'}),
        }

# Product Form
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name',
            'description',
            'price',
            'stock',
            'category', 
            'image', 
            'video_url', 
            'panoramic_image', 
            'rating', 
            'is_recommended'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'placeholder': 'Product description...', 'rows': 4}),
            'price': forms.NumberInput(attrs={'placeholder': 'Product price'}),
        }

# User Preference Form
class UserPreferenceForm(forms.ModelForm):
    class Meta:
        model = UserPreference
        fields = ['preferred_categories', 'recommended_products']

# Music Form
class MusicForm(forms.ModelForm):
    class Meta:
        model = Music
        fields = ['title', 'audio_file', 'video_file', 'cover_image']

# User Update Form
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Update your username'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Update your email'}),
        }

# Profile Update Form
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone_number', 'address', 'profile_picture']  # Editable fields for profile update
        widgets = {
            'phone_number': forms.TextInput(attrs={'placeholder': 'Update your phone number'}),
            'address': forms.TextInput(attrs={'placeholder': 'Update your address'}),
        }

# Review Form
class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'placeholder': 'Write your review here...', 'rows': 4}),
        }

# Loyalty Points Form
class LoyaltyPointsForm(forms.ModelForm):
    class Meta:
        model = LoyaltyPoints
        fields = ['points', 'user']  # Fields for loyalty points management

# Checkout Form
class CheckoutForm(forms.Form):
    name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Full Name'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'Email Address'}))
    address = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Shipping Address', 'rows': 3}))
    payment_info = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Payment Information'}))

# Return Request Form
class ReturnRequestForm(forms.ModelForm):
    class Meta:
        model = ReturnRequest
        fields = ['order_id', 'reason', 'additional_comments']
        widgets = {
            'order_id': forms.TextInput(attrs={'placeholder': 'Enter your order ID'}),
            'reason': forms.Textarea(attrs={'placeholder': 'Reason for return...', 'rows': 3}),
            'additional_comments': forms.Textarea(attrs={'placeholder': 'Any additional comments...', 'rows': 3}),
        }
