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
)

# Profile Form
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone_number', 'address', 'profile_picture']  # Editable fields

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

# Product Form
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'stock', 'category', 
                  'image', 'video_url', 'panoramic_image', 'rating', 
                  'is_recommended']

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

# Profile Update Form
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone_number', 'address', 'profile_picture']  # Editable fields for profile update

# Review Form
class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']

# Loyalty Points Form
class LoyaltyPointsForm(forms.ModelForm):
    class Meta:
        model = LoyaltyPoints
        fields = ['points', 'user']  # Fields for loyalty points management
