# shop/admin.py
from django.contrib import admin
from .models import (
    Category,
    Product,
    UserPreference,
    Music,
    Profile,
    Order,
    Cart,
    CartItem,  # Import CartItem to use with CartItemInline
    Review,
    DiscountCode,
    LoyaltyPoints,
    Notification,
    User  # Import User model
)

# Inline Cart Items for CartAdmin
class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0  # Number of empty forms to display

# Cart Admin with Cart Items inline
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'updated_at')
    search_fields = ('user__username',)
    list_filter = ('created_at',)
    inlines = [CartItemInline]  # Display CartItems inline

# Register the custom User model
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'last_login', 'is_active')
    search_fields = ('username', 'email')
    list_filter = ('is_active', 'is_staff')

# Register Discount Code Admin
@admin.register(DiscountCode)
class DiscountCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_amount', 'start_date', 'end_date', 'active')
    search_fields = ('code',)
    list_filter = ('active', 'start_date', 'end_date')

# Loyalty Points Admin
@admin.register(LoyaltyPoints)
class LoyaltyPointsAdmin(admin.ModelAdmin):
    list_display = ('user', 'points')
    search_fields = ('user__username',)
    list_filter = ('points',)

# Notification Admin
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'timestamp', 'is_read')
    list_filter = ('timestamp', 'is_read')
    search_fields = ('message', 'user__username')

# Register models without custom admin classes
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(UserPreference)
admin.site.register(Music)
admin.site.register(Profile)
admin.site.register(Order)
admin.site.register(Review)

# Register the custom User and Cart models with their specific admin configurations
admin.site.register(User, UserAdmin)
admin.site.register(Cart, CartAdmin)
