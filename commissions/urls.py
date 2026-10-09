from django.urls import path

from . import views

app_name = "commissions"

urlpatterns = [
    path("", views.my_commissions, name="my_commissions"),
]
