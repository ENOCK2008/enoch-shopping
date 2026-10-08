from django.core.management.base import BaseCommand
from decimal import Decimal
from shop.models import Product, Category

class Command(BaseCommand):
    help = 'Create sample products for testing'

    def handle(self, *args, **options):
        # Create or get a default category
        category, created = Category.objects.get_or_create(
            name='General',
            defaults={'slug': 'general'}
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created category: {category.name}'))

        # Define sample products
        sample_products = [
            {
                'name': 'Wireless Headphones',
                'description': 'High-quality wireless headphones with noise cancellation',
                'price': Decimal('99.99'),
                'stock': 15,
            },
            {
                'name': 'USB-C Cable',
                'description': 'Durable USB-C charging and data cable',
                'price': Decimal('19.99'),
                'stock': 50,
            },
            {
                'name': 'Phone Case',
                'description': 'Protective phone case with excellent grip',
                'price': Decimal('24.99'),
                'stock': 30,
            },
            {
                'name': 'Portable Charger',
                'description': '20000mAh portable power bank',
                'price': Decimal('49.99'),
                'stock': 20,
            },
            {
                'name': 'Screen Protector',
                'description': 'Tempered glass screen protector',
                'price': Decimal('9.99'),
                'stock': 100,
            },
            {
                'name': 'Keyboard',
                'description': 'Mechanical gaming keyboard RGB lights',
                'price': Decimal('149.99'),
                'stock': 10,
            },
            {
                'name': 'Mouse',
                'description': 'Ergonomic wireless mouse',
                'price': Decimal('59.99'),
                'stock': 25,
            },
            {
                'name': 'Webcam',
                'description': '1080p HD webcam for video calls',
                'price': Decimal('79.99'),
                'stock': 12,
            },
        ]

        # Create products
        created_count = 0
        existing_count = 0

        for product_data in sample_products:
            product, created = Product.objects.get_or_create(
                name=product_data['name'],
                defaults={
                    'description': product_data['description'],
                    'price': product_data['price'],
                    'stock': product_data['stock'],
                    'category': category,
                }
            )

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created product: {product.name} (ID: {product.id})'))
            else:
                existing_count += 1
                self.stdout.write(f'Product already exists: {product.name} (ID: {product.id})')

        self.stdout.write(self.style.SUCCESS(f'\n✓ Created {created_count} new products'))
        self.stdout.write(f'✓ {existing_count} products already existed')
        self.stdout.write(self.style.SUCCESS('Sample products are ready!'))
