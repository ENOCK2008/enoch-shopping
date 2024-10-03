# shop/admin.py
from django.contrib import admin
from .models import Category, Product, UserPreference, Music, Profile, Order, Cart, Review, DiscountCode, LoyaltyPoints, Notification  # Make sure to import Notification

@admin.register(DiscountCode)
class DiscountCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_amount', 'start_date', 'end_date', 'active')
    search_fields = ('code',)

@admin.register(LoyaltyPoints)
class LoyaltyPointsAdmin(admin.ModelAdmin):
    list_display = ('user', 'points')
    search_fields = ('user__username',)

@admin.register(Notification)  # Register Notification model here
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'created_at')  # Adjust based on your Notification model fields
    list_filter = ('created_at',)
    search_fields = ('message',)

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(UserPreference)
admin.site.register(Music)
admin.site.register(Profile)
admin.site.register(Order)
admin.site.register(Cart)
admin.site.register(Review)
