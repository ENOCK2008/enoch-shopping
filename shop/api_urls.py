# shop/api_urls.py
from django.urls import path
from .views import FAQViewSet  # Adjust the import based on your actual view

urlpatterns = [
    path('faqs/', FAQViewSet.as_view({'get': 'list'}), name='faq-list'),
    path('faqs/<int:pk>/', FAQViewSet.as_view({'get': 'retrieve'}), name='faq-detail'),
    # Add other API endpoints as needed
]
