from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from products.models import Product, Review

class ProductTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='password123',
            first_name='Tester'
        )
        self.admin = User.objects.create_superuser(
            username='admin@example.com',
            email='admin@example.com',
            password='password123'
        )
        self.product = Product.objects.create(
            user=self.admin,
            name='Test Headphones',
            brand='TestBrand',
            category='Audio',
            price=99.99,
            countInStock=10,
            rating=4.5,
            numReviews=2,
            description='Crisp test audio'
        )

    def test_products_list_view(self):
        response = self.client.get(reverse('products'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Headphones')

    def test_products_search(self):
        response = self.client.get(reverse('products'), {'keyword': 'Headphones'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Headphones')
        
        response2 = self.client.get(reverse('products'), {'keyword': 'NonExistent'})
        self.assertEqual(response2.status_code, 200)
        self.assertNotContains(response2, 'Test Headphones')

    def test_products_category_filter(self):
        response = self.client.get(reverse('products'), {'category': 'Audio'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Headphones')

    def test_product_detail_view(self):
        response = self.client.get(reverse('product', kwargs={'pk': self.product.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Headphones')
        self.assertContains(response, '$99.99')

    def test_save_cart_to_session(self):
        payload = {
            'cartItems': [{'product': str(self.product.id), 'name': self.product.name, 'price': 99.99, 'qty': 2}],
            'itemsPrice': 199.98,
            'shippingPrice': 0,
            'taxPrice': 30.0,
            'totalPrice': 229.98
        }
        response = self.client.post(
            reverse('save-cart'),
            data=payload,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        session = self.client.session
        self.assertEqual(len(session.get('cart_items', [])), 1)

    def test_create_review(self):
        self.client.login(username='testuser@example.com', password='password123')
        response = self.client.post(
            reverse('create-review', kwargs={'pk': self.product.id}),
            data={'rating': 5, 'comment': 'Amazing product!'},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Review.objects.filter(product=self.product).count(), 1)
