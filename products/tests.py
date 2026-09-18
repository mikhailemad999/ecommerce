from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from products.models import Category, Product, ProductSpecification, ProductImage, Review

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
        self.category = Category.objects.create(
            name='Audio & Sound',
            slug='audio-sound',
            icon='fa-headphones'
        )
        self.product1 = Product.objects.create(
            user=self.admin,
            name='Pro Studio Headphones',
            brand='AudioLux',
            category='Audio & Sound',
            category_ref=self.category,
            price=299.99,
            discount_price=249.99,
            countInStock=10,
            rating=4.8,
            numReviews=15,
            is_featured=True,
            description='Crisp audiophile sound.'
        )
        ProductSpecification.objects.create(
            product=self.product1,
            name='Battery Life',
            value='35 Hours'
        )

        self.product2 = Product.objects.create(
            user=self.admin,
            name='Budget Earbuds',
            brand='SoundBasic',
            category='Audio & Sound',
            category_ref=self.category,
            price=29.99,
            discount_price=None,
            countInStock=0, # Out of stock
            rating=3.5,
            numReviews=4,
            description='Everyday listening.'
        )

    def test_products_list_view(self):
        response = self.client.get(reverse('products'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pro Studio Headphones')

    def test_products_search(self):
        response = self.client.get(reverse('products'), {'keyword': 'Studio'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pro Studio Headphones')
        self.assertNotContains(response, 'Budget Earbuds')

    def test_brand_filter(self):
        response = self.client.get(reverse('products'), {'brand': 'AudioLux'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pro Studio Headphones')
        self.assertNotContains(response, 'Budget Earbuds')

    def test_price_range_filter(self):
        # Filter for price >= 100
        response = self.client.get(reverse('products'), {'min_price': '100'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pro Studio Headphones')
        self.assertNotContains(response, 'Budget Earbuds')

    def test_in_stock_filter(self):
        # product2 has countInStock=0
        response = self.client.get(reverse('products'), {'in_stock': 'true'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pro Studio Headphones')
        self.assertNotContains(response, 'Budget Earbuds')

    def test_on_sale_filter(self):
        # product1 has discount_price=249.99, product2 has no discount
        response = self.client.get(reverse('products'), {'on_sale': 'true'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pro Studio Headphones')
        self.assertNotContains(response, 'Budget Earbuds')

    def test_product_detail_and_specifications(self):
        response = self.client.get(reverse('product', kwargs={'pk': self.product1.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pro Studio Headphones')
        self.assertContains(response, 'Battery Life')
        self.assertContains(response, '35 Hours')

    def test_save_cart_to_session(self):
        payload = {
            'cartItems': [{'product': str(self.product1.id), 'name': self.product1.name, 'price': 249.99, 'qty': 1}],
            'itemsPrice': 249.99,
            'shippingPrice': 0,
            'taxPrice': 37.50,
            'totalPrice': 287.49
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
            reverse('create-review', kwargs={'pk': self.product1.id}),
            data={'rating': 5, 'comment': 'Exceptional sound stage and pristine noise cancellation!'},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Review.objects.filter(product=self.product1).count(), 1)
