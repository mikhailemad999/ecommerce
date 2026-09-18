from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from products.models import Product
from orders.models import Order, OrderItem, ShippingAddress, ShippingCarrier, ShippingMethod, ShipmentTracking, TrackingCheckpoint

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
        self.carrier = ShippingCarrier.objects.create(
            name='TestExpress',
            code='TESTEXP',
            tracking_url_template='https://test.com/track/{}'
        )
        self.shipping_method = ShippingMethod.objects.create(
            name='Test Standard Air',
            code='TEST_STD',
            carrier=self.carrier,
            base_price=10.00,
            estimated_days_min=2,
            estimated_days_max=4,
            free_shipping_threshold=100.00
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

    def test_create_order_with_shipping_and_tracking(self):
        self.client.login(username='shopper@example.com', password='password123')
        payload = {
            'orderItems': [{'product': self.product.id, 'qty': 2, 'price': 150.00}],
            'shippingMethodId': self.shipping_method.id,
            'shippingAddress': {
                'address': '123 Luxury Lane',
                'city': 'San Francisco',
                'postalCode': '94105',
                'country': 'United States',
                'phone': '+1 555-432-1098'
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
        
        order = Order.objects.filter(user=self.user).first()
        self.assertIsNotNone(order.tracking_code)
        self.assertTrue(hasattr(order, 'tracking'))
        self.assertEqual(order.tracking.current_status, 'ORDER_PLACED')
        self.assertEqual(order.tracking.checkpoints.count(), 1)
        self.assertEqual(order.shipping_method, self.shipping_method)

        # Verify stock was reduced
        self.product.refresh_from_db()
        self.assertEqual(self.product.countInStock, 8)

    def test_test_card_payment_updates_tracking(self):
        self.client.login(username='shopper@example.com', password='password123')
        order = Order.objects.create(
            user=self.user,
            paymentMethod='Credit Card',
            totalPrice=150.0,
            taxPrice=22.5,
            shippingPrice=0,
            isPaid=False
        )
        tracking = ShipmentTracking.objects.create(
            order=order,
            tracking_number='LX-TEST-99881-US',
            current_status='ORDER_PLACED'
        )

        response = self.client.get(reverse('order-test-pay', kwargs={'pk': order.id}), follow=True)
        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertTrue(order.isPaid)
        self.assertEqual(order.status, 'PAID')

        tracking.refresh_from_db()
        self.assertEqual(tracking.current_status, 'PROCESSING')
        self.assertTrue(tracking.checkpoints.filter(status='PROCESSING').exists())

    def test_public_tracking_portal_lookup(self):
        order = Order.objects.create(
            user=self.user,
            totalPrice=200.0,
            isPaid=True
        )
        tracking = ShipmentTracking.objects.create(
            order=order,
            tracking_number='LX-LIVE-TRACK-001',
            current_status='IN_TRANSIT',
            carrier_name='FedEx Express Worldwide'
        )
        TrackingCheckpoint.objects.create(
            tracking=tracking,
            status='IN_TRANSIT',
            title='In Flight to Oakland Sort Hub',
            location='Oakland CA'
        )

        # Search by tracking number
        response = self.client.get(reverse('order-tracking'), {'tracking_number': 'LX-LIVE-TRACK-001'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'LX-LIVE-TRACK-001')
        self.assertContains(response, 'FedEx Express Worldwide')
        self.assertContains(response, 'In Flight to Oakland Sort Hub')

        # Search with invalid number
        response_invalid = self.client.get(reverse('order-tracking'), {'tracking_number': 'NONEXISTENT'})
        self.assertEqual(response_invalid.status_code, 200)
        self.assertContains(response_invalid, 'No Shipment Found')

    def test_health_check_endpoint(self):
        response = self.client.get(reverse('health-check'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['database'], 'connected')
