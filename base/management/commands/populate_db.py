from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from products.models import Product
import random

class Command(BaseCommand):
    help = 'Populates the database with sample data'

    def handle(self, *args, **kwargs):
        # Create admin user if not exists
        if not User.objects.filter(username='admin@example.com').exists():
            User.objects.create_superuser(
                'admin@example.com',
                'admin@example.com',
                'admin123',
                first_name='Admin'
            )
            self.stdout.write(self.style.SUCCESS('Admin user created'))
        
        # Create sample products
        if Product.objects.count() == 0:
            admin = User.objects.get(username='admin@example.com')
            
            products = [
                {
                    'name': 'Airpods Wireless Bluetooth Headphones',
                    'description': 'Bluetooth technology lets you connect it with compatible devices wirelessly. High-quality AAC audio offers immersive listening experience.',
                    'brand': 'Apple',
                    'category': 'Electronics',
                    'price': 89.99,
                    'countInStock': 10,
                    'rating': 4.5,
                    'numReviews': 12,
                },
                {
                    'name': 'iPhone 11 Pro 256GB Memory',
                    'description': 'Introducing the iPhone 11 Pro. A transformative triple-camera system that adds tons of capability without complexity.',
                    'brand': 'Apple',
                    'category': 'Electronics',
                    'price': 599.99,
                    'countInStock': 7,
                    'rating': 4.0,
                    'numReviews': 8,
                },
                {
                    'name': 'Cannon EOS 80D DSLR Camera',
                    'description': 'Characterized by versatile imaging specs, the Canon EOS 80D further clarifies itself using a pair of robust focusing systems.',
                    'brand': 'Cannon',
                    'category': 'Electronics',
                    'price': 929.99,
                    'countInStock': 5,
                    'rating': 3.0,
                    'numReviews': 12,
                },
                {
                    'name': 'Sony Playstation 5',
                    'description': 'The ultimate home entertainment center starts with PlayStation. Whether you are into gaming, HD movies, television, music.',
                    'brand': 'Sony',
                    'category': 'Electronics',
                    'price': 399.99,
                    'countInStock': 11,
                    'rating': 5.0,
                    'numReviews': 12,
                },
                {
                    'name': 'Logitech G-Series Gaming Mouse',
                    'description': 'Get a better handle on your games with this Logitech LIGHTSYNC gaming mouse. The six programmable buttons allow customization.',
                    'brand': 'Logitech',
                    'category': 'Electronics',
                    'price': 49.99,
                    'countInStock': 7,
                    'rating': 3.5,
                    'numReviews': 10,
                },
                {
                    'name': 'Amazon Echo Dot 3rd Generation',
                    'description': 'Meet Echo Dot - Our most popular smart speaker with a fabric design. It is our most compact smart speaker that fits perfectly into small spaces.',
                    'brand': 'Amazon',
                    'category': 'Electronics',
                    'price': 29.99,
                    'countInStock': 0,
                    'rating': 4.0,
                    'numReviews': 12,
                },
            ]
            
            for product_data in products:
                Product.objects.create(
                    user=admin,
                    **product_data
                )
            
            self.stdout.write(self.style.SUCCESS(f'Created {len(products)} sample products'))
