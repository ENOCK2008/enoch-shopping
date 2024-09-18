# auth_two_factor/views.py
from django.shortcuts import render

def setup_view(request):
    # Handle 2FA setup logic here
    return render(request, 'auth_two_factor/setup.html')

def verify_view(request):
    # Handle 2FA verification logic here
    return render(request, 'auth_two_factor/verify.html')
# in two_factor/views.py

from django.views.generic import View
from django.shortcuts import render

class SetupView(View):
    def get(self, request):
        # Render the setup template or handle setup logic here
        return render(request, 'two_factor/setup.html')
from django.views.generic import View
from django.shortcuts import render

class VerifyView(View):
    def get(self, request):
        # Handle verification logic
        return render(request, 'two_factor/verify.html')
