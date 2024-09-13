# auth_two_factor/views.py
from django.shortcuts import render

def setup_view(request):
    # Handle 2FA setup logic here
    return render(request, 'auth_two_factor/setup.html')

def verify_view(request):
    # Handle 2FA verification logic here
    return render(request, 'auth_two_factor/verify.html')
