from django.contrib import admin
from .models import (
    AdCampaign, VideoAd, Banner, ProductPromotion,
    AdMetrics, Sponsorship, AdRequest
)


@admin.register(AdCampaign)
class AdCampaignAdmin(admin.ModelAdmin):
    list_display = ['name', 'advertiser', 'status', 'budget', 'spent', 'impressions', 'clicks', 'ctr', 'created_at']
    list_filter = ['status', 'created_at', 'target_country']
    search_fields = ['name', 'advertiser__username']
    readonly_fields = ['impressions', 'clicks', 'conversions', 'spent', 'ctr', 'conversion_rate', 'roi', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'description', 'advertiser', 'status')
        }),
        ('Budget & Duration', {
            'fields': ('budget', 'spent', 'start_date', 'end_date')
        }),
        ('Targeting', {
            'fields': ('target_country',)
        }),
        ('Metrics', {
            'fields': ('impressions', 'clicks', 'conversions', 'ctr', 'conversion_rate', 'roi'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(VideoAd)
class VideoAdAdmin(admin.ModelAdmin):
    list_display = ['title', 'campaign', 'placement', 'priority', 'views', 'clicks', 'active', 'created_at']
    list_filter = ['placement', 'active', 'created_at']
    search_fields = ['title', 'campaign__name']
    readonly_fields = ['views', 'clicks', 'view_through_rate', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Info', {
            'fields': ('campaign', 'title', 'description', 'video_file', 'thumbnail', 'duration_seconds')
        }),
        ('Placement & Priority', {
            'fields': ('placement', 'priority', 'active')
        }),
        ('Call to Action', {
            'fields': ('call_to_action_url', 'call_to_action_text')
        }),
        ('Metrics', {
            'fields': ('views', 'clicks', 'view_through_rate'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ['title', 'campaign', 'placement', 'size', 'priority', 'impressions', 'clicks', 'ctr', 'active']
    list_filter = ['placement', 'size', 'active', 'created_at']
    search_fields = ['title', 'campaign__name']
    readonly_fields = ['impressions', 'clicks', 'ctr', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Info', {
            'fields': ('campaign', 'title', 'image', 'link_url')
        }),
        ('Size & Placement', {
            'fields': ('size', 'custom_width', 'custom_height', 'placement', 'priority', 'active')
        }),
        ('Metrics', {
            'fields': ('impressions', 'clicks', 'ctr'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProductPromotion)
class ProductPromotionAdmin(admin.ModelAdmin):
    list_display = ['product', 'campaign', 'discount_type', 'discount_value', 'impressions', 'conversions', 'conversion_rate', 'active']
    list_filter = ['discount_type', 'active', 'created_at']
    search_fields = ['product__name', 'campaign__name', 'promotion_text']
    readonly_fields = ['impressions', 'conversions', 'conversion_rate', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Info', {
            'fields': ('campaign', 'product')
        }),
        ('Discount', {
            'fields': ('discount_type', 'discount_value')
        }),
        ('Display', {
            'fields': ('promotion_text', 'badge_text', 'priority', 'active')
        }),
        ('Metrics', {
            'fields': ('impressions', 'conversions', 'conversion_rate'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Sponsorship)
class SponsorshipAdmin(admin.ModelAdmin):
    list_display = ['title', 'sponsor', 'content_type', 'amount', 'impressions', 'clicks', 'ctr', 'active']
    list_filter = ['content_type', 'active', 'start_date', 'end_date']
    search_fields = ['title', 'sponsor__username', 'description']
    readonly_fields = ['impressions', 'clicks', 'ctr', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Info', {
            'fields': ('sponsor', 'title', 'description', 'logo', 'link_url')
        }),
        ('Content', {
            'fields': ('content_type', 'content_id')
        }),
        ('Duration & Amount', {
            'fields': ('start_date', 'end_date', 'amount', 'active')
        }),
        ('Metrics', {
            'fields': ('impressions', 'clicks', 'ctr'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AdRequest)
class AdRequestAdmin(admin.ModelAdmin):
    list_display = ['title', 'advertiser', 'budget', 'duration_days', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'advertiser__username', 'description']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Info', {
            'fields': ('advertiser', 'title', 'description')
        }),
        ('Campaign Details', {
            'fields': ('budget', 'duration_days')
        }),
        ('Status', {
            'fields': ('status', 'rejection_reason')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AdMetrics)
class AdMetricsAdmin(admin.ModelAdmin):
    list_display = ['campaign', 'metric_type', 'user', 'timestamp', 'device_type', 'country']
    list_filter = ['metric_type', 'timestamp', 'device_type', 'country']
    search_fields = ['campaign__name', 'user__username', 'session_id', 'ip_address']
    readonly_fields = ['timestamp', 'campaign', 'video_ad', 'banner', 'metric_type', 'user', 'session_id', 'ip_address']
    fieldsets = (
        ('Metric Info', {
            'fields': ('campaign', 'metric_type', 'timestamp')
        }),
        ('Related Objects', {
            'fields': ('video_ad', 'banner')
        }),
        ('User Info', {
            'fields': ('user', 'session_id', 'ip_address')
        }),
        ('Context', {
            'fields': ('country', 'device_type', 'custom_data')
        }),
    )
