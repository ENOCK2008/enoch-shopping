from django import forms
from django.contrib.auth import get_user_model
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
    ReturnRequest,
    Comment,  # Make sure to import Comment here
)

User = get_user_model()

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
        fields = ['feedback_text']
        widgets = {
            'feedback_text': forms.Textarea(attrs={'placeholder': 'Leave your feedback here...', 'rows': 3}),
        }

# Discount Code Form
class DiscountCodeForm(forms.ModelForm):
    class Meta:
        model = DiscountCode
        fields = ['code', 'discount_amount', 'start_date', 'end_date', 'active']

# Custom User Creation Form
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
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
        fields = ['phone_number', 'address', 'profile_picture']
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
        fields = ['points', 'user']

# Checkout Form
class CheckoutForm(forms.Form):
    name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Full Name'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'Email Address'}))
    address = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Shipping Address', 'rows': 3}))
    payment_method = forms.ChoiceField(
        choices=[
            ('mpesa', 'M-Pesa'),
            ('mtn', 'MTN Mobile Money'),
            ('airtel', 'Airtel Money'),
            ('cod', 'Pay on Delivery'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    payment_info = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'placeholder': 'Payment Information'}),
    )

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        payment_info = cleaned_data.get('payment_info')

        if payment_method != 'cod' and not payment_info:
            self.add_error('payment_info', 'Payment information is required for this payment method.')

# Return Request Form
class ReturnRequestForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'placeholder': 'Enter your username'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'Enter your email'}))
    password = forms.CharField(required=False, widget=forms.PasswordInput(attrs={'placeholder': 'Enter your password'}))
    bio = forms.CharField(required=False, widget=forms.Textarea(attrs={'placeholder': 'Tell us about yourself...', 'rows': 2}))
    phone_number = forms.CharField(max_length=16, required=False, widget=forms.TextInput(attrs={'placeholder': 'Enter your phone number'}))

    class Meta:
        model = ReturnRequest
        fields = ['order', 'reason', 'additional_comments', 'username', 'email', 'password', 'bio', 'phone_number']
        widgets = {
            'order': forms.TextInput(attrs={'placeholder': 'Enter your order ID'}),
            'reason': forms.Textarea(attrs={'placeholder': 'Reason for return...', 'rows': 3}),
            'additional_comments': forms.Textarea(attrs={'placeholder': 'Any additional comments...', 'rows': 3}),
        }

# Account Settings Form
class AccountSettingsForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password']
        widgets = {
            'password': forms.PasswordInput(attrs={'placeholder': 'Enter your new password'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data['password']:
            user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user

# Shipping Address Form
class ShippingAddressForm(forms.Form):
    name = forms.CharField(max_length=100)
    address = forms.CharField(max_length=255)
    city = forms.CharField(max_length=100)
    region = forms.CharField(max_length=100)
    # Add more fields as needed

# Comment Form
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']  # Updated to match the Comment model
        widgets = {
            'content': forms.Textarea(attrs={'placeholder': 'Write your comment here...', 'rows': 4}),
        }
