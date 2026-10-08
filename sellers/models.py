from django.conf import settings
from django.db import models

class SellerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="seller_profile")
    store_name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    verified = models.BooleanField(default=False)
    phone = models.CharField(max_length=30, blank=True)
    country = models.CharField(max_length=80, default="Uganda")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.store_name
