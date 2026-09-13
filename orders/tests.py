from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from products.models import Product
from orders.models import Order, OrderItem, ShippingAddress

class OrderTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='shopper@example.com',
            email='shopper@example.com',
            password='password123',
            first_name='Shopper'
        )
        self.admin = User.objects.create_superuser(
            username='admin@example.com',
            email='admin@example.com',
            password='password123'
        )
        self.product = Product.objects.create(
            user=self.admin,
            name='Test Device',
            brand='TechCorp',
            category='Gadgets',
            price=150.00,
            countInStock=10,
            rating=5.0
        )

    def test_checkout_redirects_when_not_logged_in(self):
        response = self.client.get(reverse('checkout'))
        self.assertEqual(response.status_code, 302)

    def test_create_order_api(self):
        self.client.login(username='shopper@example.com', password='password123')
        payload = {
            'orderItems': [{'product': self.product.id, 'qty': 2, 'price': 150.00}],
            'shippingAddress': {
                'address': '123 Main St',
                'city': 'Metropolis',
                'postalCode': '10001',
                'country': 'USA',
                'phone': '1234567890'
            },
            'paymentMethod': 'Credit Card',
            'taxPrice': 45.0,
            'shippingPrice': 0.0,
            'totalPrice': 345.0
        }
        response = self.client.post(
            reverse('orders-add'),
            data=payload,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Order.objects.filter(user=self.user).exists())
        
        # Verify stock decreased
        self.product.refresh_from_db()
        self.assertEqual(self.product.countInStock, 8)

    def test_test_card_payment(self):
        self.client.login(username='shopper@example.com', password='password123')
        order = Order.objects.create(
            user=self.user,
            paymentMethod='Credit Card',
            totalPrice=150.0,
            taxPrice=22.5,
            shippingPrice=0,
            isPaid=False
        )
        response = self.client.get(reverse('order-test-pay', kwargs={'pk': order.id}), follow=True)
        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertTrue(order.isPaid)
        self.assertIsNotNone(order.paidAt)
