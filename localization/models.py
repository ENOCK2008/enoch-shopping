from django.db import models

class Country(models.Model):
    code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=100)
    currency = models.CharField(max_length=10, default="USD")
    language = models.CharField(max_length=20, default="en")
    active = models.BooleanField(default=True)
    tax_rate = models.DecimalField(max_digits=6, decimal_places=3, default=0)

class CurrencyRate(models.Model):
    base = models.CharField(max_length=10)
    quote = models.CharField(max_length=10)
    rate = models.DecimalField(max_digits=20, decimal_places=8)
    updated_at = models.DateTimeField(auto_now=True)
