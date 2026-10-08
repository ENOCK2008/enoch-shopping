from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from sellers.models import SellerProfile
from catalog.models import Category, Product

class Command(BaseCommand):
    help = "Create demo Enock sellers, categories and products."

    def handle(self, *args, **kwargs):
        User = get_user_model()
        sellers = [
            ("demo@enock.test", "Enock Tech Store", "Electronics and gadgets", "Uganda", True),
            ("fashion@enock.test", "Global Fashion Hub", "Fashion for everyday life", "Kenya", True),
            ("home@enock.test", "Home & Living Market", "Useful products for modern homes", "Rwanda", False),
        ]
        profiles = []
        for email, store, desc, country, verified in sellers:
            user, created = User.objects.get_or_create(email=email, defaults={"username": email.split("@")[0], "role": User.Role.SELLER})
            if created:
                user.set_password("ChangeMe123!")
                user.save()
            profile, _ = SellerProfile.objects.get_or_create(user=user, defaults={
                "store_name": store, "slug": slugify(store), "description": desc, "country": country, "verified": verified
            })
            profiles.append(profile)

        cats = {}
        for name in ["Electronics", "Fashion", "Home & Living", "Beauty", "Sports", "Books"]:
            cats[name], _ = Category.objects.get_or_create(name=name, slug=slugify(name))

        products = [
            (profiles[0], cats["Electronics"], "Smartphone Pro 5G", "650000", "UGX", 20),
            (profiles[0], cats["Electronics"], "Wireless Earbuds", "95000", "UGX", 50),
            (profiles[0], cats["Electronics"], "Laptop 14-inch", "1850000", "UGX", 12),
            (profiles[1], cats["Fashion"], "Classic Running Shoes", "180000", "KES", 30),
            (profiles[1], cats["Fashion"], "Premium Cotton Hoodie", "45000", "KES", 40),
            (profiles[1], cats["Fashion"], "Everyday Backpack", "32000", "KES", 25),
            (profiles[2], cats["Home & Living"], "LED Desk Lamp", "28", "USD", 40),
            (profiles[2], cats["Home & Living"], "Kitchen Organizer Set", "35", "USD", 25),
            (profiles[2], cats["Home & Living"], "Reusable Water Bottle", "18", "USD", 60),
        ]
        for seller, category, name, price, currency, stock in products:
            Product.objects.get_or_create(
                sku=slugify(name)[:90],
                defaults={
                    "seller": seller, "category": category, "name": name,
                    "slug": slugify(name), "description": f"{name} available from {seller.store_name}.",
                    "price": price, "currency": currency, "stock_quantity": stock, "active": True
                }
            )
        self.stdout.write(self.style.SUCCESS("Demo marketplace data created. Demo seller password: ChangeMe123!"))
