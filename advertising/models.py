from django.db import models
from django.conf import settings
from decimal import Decimal


class AdCampaign(models.Model):
    """Represents an advertising campaign"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('ended', 'Ended'),
    ]
    
    name = models.CharField(max_length=255, verbose_name="Campaign Name")
    description = models.TextField(blank=True, verbose_name="Campaign Description")
    advertiser = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ad_campaigns", verbose_name="Advertiser")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name="Status")
    budget = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Budget (UGX)")
    spent = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Amount Spent")
    start_date = models.DateTimeField(verbose_name="Start Date")
    end_date = models.DateTimeField(verbose_name="End Date")
    target_country = models.CharField(max_length=100, default="Uganda", verbose_name="Target Country")
    impressions = models.PositiveIntegerField(default=0, verbose_name="Total Impressions")
    clicks = models.PositiveIntegerField(default=0, verbose_name="Total Clicks")
    conversions = models.PositiveIntegerField(default=0, verbose_name="Total Conversions")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Ad Campaign"
        verbose_name_plural = "Ad Campaigns"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.status}"

    @property
    def ctr(self):
        """Click-through rate"""
        return round((self.clicks / self.impressions * 100), 2) if self.impressions > 0 else 0

    @property
    def conversion_rate(self):
        """Conversion rate"""
        return round((self.conversions / self.clicks * 100), 2) if self.clicks > 0 else 0

    @property
    def roi(self):
        """Return on investment"""
        if self.spent == 0:
            return 0
        revenue = self.conversions * 50000  # Approximate average order value
        return round(((revenue - float(self.spent)) / float(self.spent)) * 100, 2)


class VideoAd(models.Model):
    """Video advertisement model"""
    PLACEMENT_CHOICES = [
        ('homepage', 'Homepage'),
        ('product_page', 'Product Page'),
        ('checkout', 'Checkout Page'),
        ('cart', 'Cart Page'),
        ('search', 'Search Results'),
        ('music_page', 'Music Page'),
        ('chat', 'Chat Page'),
    ]

    campaign = models.ForeignKey(AdCampaign, on_delete=models.CASCADE, related_name="video_ads", verbose_name="Campaign")
    title = models.CharField(max_length=255, verbose_name="Ad Title")
    description = models.TextField(verbose_name="Ad Description")
    video_file = models.FileField(upload_to='ads/videos/', verbose_name="Video File")
    thumbnail = models.ImageField(upload_to='ads/thumbnails/', verbose_name="Thumbnail")
    duration_seconds = models.PositiveIntegerField(verbose_name="Duration (seconds)")
    placement = models.CharField(max_length=50, choices=PLACEMENT_CHOICES, verbose_name="Placement")
    call_to_action_url = models.URLField(blank=True, verbose_name="Call-to-Action URL")
    call_to_action_text = models.CharField(max_length=100, blank=True, verbose_name="CTA Text")
    priority = models.PositiveIntegerField(default=1, verbose_name="Priority (1=highest)")
    views = models.PositiveIntegerField(default=0, verbose_name="View Count")
    clicks = models.PositiveIntegerField(default=0, verbose_name="Click Count")
    active = models.BooleanField(default=True, verbose_name="Active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Video Advertisement"
        verbose_name_plural = "Video Advertisements"
        ordering = ['-priority', '-created_at']

    def __str__(self):
        return f"{self.title} ({self.placement})"

    @property
    def view_through_rate(self):
        """Percentage of views that completed the video"""
        return round((self.clicks / self.views * 100), 2) if self.views > 0 else 0


class Banner(models.Model):
    """Banner advertisement model"""
    SIZE_CHOICES = [
        ('728x90', 'Leaderboard'),
        ('300x250', 'Medium Rectangle'),
        ('160x600', 'Wide Skyscraper'),
        ('300x600', 'Half Page'),
        ('970x90', 'Large Leaderboard'),
        ('custom', 'Custom Size'),
    ]

    PLACEMENT_CHOICES = [
        ('header', 'Header'),
        ('sidebar', 'Sidebar'),
        ('footer', 'Footer'),
        ('between_products', 'Between Products'),
        ('modal', 'Modal Pop-up'),
    ]

    campaign = models.ForeignKey(AdCampaign, on_delete=models.CASCADE, related_name="banners", verbose_name="Campaign")
    title = models.CharField(max_length=255, verbose_name="Banner Title")
    image = models.ImageField(upload_to='ads/banners/', verbose_name="Banner Image")
    link_url = models.URLField(verbose_name="Link URL")
    size = models.CharField(max_length=20, choices=SIZE_CHOICES, default='300x250', verbose_name="Size")
    custom_width = models.PositiveIntegerField(null=True, blank=True, verbose_name="Custom Width (px)")
    custom_height = models.PositiveIntegerField(null=True, blank=True, verbose_name="Custom Height (px)")
    placement = models.CharField(max_length=50, choices=PLACEMENT_CHOICES, verbose_name="Placement")
    priority = models.PositiveIntegerField(default=1, verbose_name="Priority")
    impressions = models.PositiveIntegerField(default=0, verbose_name="Impressions")
    clicks = models.PositiveIntegerField(default=0, verbose_name="Clicks")
    active = models.BooleanField(default=True, verbose_name="Active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Banner Advertisement"
        verbose_name_plural = "Banner Advertisements"
        ordering = ['-priority', '-created_at']

    def __str__(self):
        return f"{self.title} ({self.size})"

    @property
    def ctr(self):
        """Click-through rate"""
        return round((self.clicks / self.impressions * 100), 2) if self.impressions > 0 else 0


class ProductPromotion(models.Model):
    """Product-specific promotion/ad"""
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage Off'),
        ('fixed', 'Fixed Amount Off'),
        ('free_shipping', 'Free Shipping'),
        ('bundle', 'Bundle Deal'),
    ]

    campaign = models.ForeignKey(AdCampaign, on_delete=models.CASCADE, related_name="product_promotions", verbose_name="Campaign")
    product = models.ForeignKey('shop.Product', on_delete=models.CASCADE, related_name="promotions", verbose_name="Product")
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, verbose_name="Discount Type")
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Discount Value")
    promotion_text = models.CharField(max_length=200, verbose_name="Promotion Text")
    badge_text = models.CharField(max_length=50, verbose_name="Badge Text (e.g., 'SALE')")
    priority = models.PositiveIntegerField(default=1, verbose_name="Priority")
    impressions = models.PositiveIntegerField(default=0, verbose_name="Times Shown")
    conversions = models.PositiveIntegerField(default=0, verbose_name="Conversions")
    active = models.BooleanField(default=True, verbose_name="Active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Product Promotion"
        verbose_name_plural = "Product Promotions"
        ordering = ['-priority', '-created_at']

    def __str__(self):
        return f"{self.product.name} - {self.get_discount_type_display()}"

    @property
    def conversion_rate(self):
        """Conversion rate"""
        return round((self.conversions / self.impressions * 100), 2) if self.impressions > 0 else 0


class AdMetrics(models.Model):
    """Track detailed metrics for ads"""
    METRIC_TYPES = [
        ('impression', 'Impression'),
        ('click', 'Click'),
        ('conversion', 'Conversion'),
        ('view', 'Video View'),
        ('engagement', 'Engagement'),
    ]

    campaign = models.ForeignKey(AdCampaign, on_delete=models.CASCADE, related_name="metrics")
    video_ad = models.ForeignKey(VideoAd, on_delete=models.SET_NULL, null=True, blank=True, related_name="metrics")
    banner = models.ForeignKey(Banner, on_delete=models.SET_NULL, null=True, blank=True, related_name="metrics")
    metric_type = models.CharField(max_length=20, choices=METRIC_TYPES)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    session_id = models.CharField(max_length=100, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    country = models.CharField(max_length=100, default="Uganda")
    device_type = models.CharField(max_length=50, blank=True)  # mobile, desktop, tablet
    custom_data = models.JSONField(default=dict, blank=True)  # For additional tracking data

    class Meta:
        verbose_name = "Ad Metric"
        verbose_name_plural = "Ad Metrics"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['campaign', 'timestamp']),
            models.Index(fields=['metric_type', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.get_metric_type_display()} - {self.campaign.name}"


class Sponsorship(models.Model):
    """Sponsorships for music and video content"""
    CONTENT_TYPES = [
        ('music', 'Music Track'),
        ('video', 'Video Content'),
        ('artist', 'Artist Profile'),
        ('channel', 'Channel'),
    ]

    sponsor = models.ForeignKey('shop.User', on_delete=models.CASCADE, related_name="sponsorships", verbose_name="Sponsor")
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES, verbose_name="Sponsored Content Type")
    content_id = models.PositiveIntegerField(verbose_name="Content ID")
    title = models.CharField(max_length=255, verbose_name="Sponsorship Title")
    description = models.TextField(verbose_name="Sponsorship Description")
    logo = models.ImageField(upload_to='sponsorships/', verbose_name="Sponsor Logo")
    link_url = models.URLField(verbose_name="Link URL")
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Sponsorship Amount (UGX)")
    start_date = models.DateTimeField(verbose_name="Start Date")
    end_date = models.DateTimeField(verbose_name="End Date")
    impressions = models.PositiveIntegerField(default=0, verbose_name="Impressions")
    clicks = models.PositiveIntegerField(default=0, verbose_name="Clicks")
    active = models.BooleanField(default=True, verbose_name="Active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Sponsorship"
        verbose_name_plural = "Sponsorships"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.sponsor.username} - {self.title}"

    @property
    def ctr(self):
        """Click-through rate"""
        return round((self.clicks / self.impressions * 100), 2) if self.impressions > 0 else 0


class AdRequest(models.Model):
    """Track ad content requests for personalization"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    advertiser = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ad_requests")
    title = models.CharField(max_length=255)
    description = models.TextField()
    budget = models.DecimalField(max_digits=12, decimal_places=2)
    duration_days = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Ad Request"
        verbose_name_plural = "Ad Requests"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.advertiser.username} - {self.title}"
