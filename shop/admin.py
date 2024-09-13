# shop/admin.py

from django.contrib import admin
from .models import Category, Product, UserPreference, Music, Profile, Order, Cart, Review

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(UserPreference)
admin.site.register(Music)
admin.site.register(Profile)
admin.site.register(Order)
admin.site.register(Cart)
admin.site.register(Review)  # Add this line
