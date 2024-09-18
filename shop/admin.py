# shop/admin.py

from django.contrib import admin
from .models import Category, Product, UserPreference, Music, Profile, Order, Cart, Review
# shop/admin.py
from django.contrib import admin
from .models import DiscountCode, LoyaltyPoints

@admin.register(DiscountCode)
class DiscountCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_amount', 'start_date', 'end_date', 'active')
    search_fields = ('code',)

@admin.register(LoyaltyPoints)
class LoyaltyPointsAdmin(admin.ModelAdmin):
    list_display = ('user', 'points')
    search_fields = ('user__username',)

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(UserPreference)
admin.site.register(Music)
admin.site.register(Profile)
admin.site.register(Order)
admin.site.register(Cart)
admin.site.register(Review)  # Add this line
