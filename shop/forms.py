from django import forms
from django.contrib.auth.models import User
from .models import Product, Review, Profile, Music, UserPreference
# shop/forms.py
# shop/forms.py
from django import forms
from .models import DiscountCode
from django import forms
from .models import Feedback

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['message']

class DiscountCodeForm(forms.ModelForm):
    class Meta:
        model = DiscountCode
        fields = ['code', 'discount_amount', 'start_date', 'end_date', 'active']

from django import forms
from django.contrib.auth.forms import UserCreationForm
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'price', 'description', 'stock', 'category', 'image']  # Adjusted fields

class UserPreferenceForm(forms.ModelForm):
    class Meta:
        model = UserPreference
        fields = ['preferred_categories', 'recommended_products']

class MusicForm(forms.ModelForm):
    class Meta:
        model = Music
        fields = ['title', 'audio_file', 'cover_image']

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone_number', 'address', 'profile_picture']

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
from django import forms
from .models import LoyaltyPoints

class LoyaltyPointsForm(forms.ModelForm):
    class Meta:
        model = LoyaltyPoints
        fields = ['points', 'user']  # Adjust fields based on your model
