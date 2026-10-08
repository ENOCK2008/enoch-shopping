from django.urls import path
from . import views

app_name = 'auth_two_factor'

urlpatterns = [
    path('setup/', views.setup_view, name='setup'),
    path('verify/', views.verify_view, name='verify'),
]
