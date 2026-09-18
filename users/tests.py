from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from users.models import Profile, CustomerAddress

class UserTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='existing@example.com',
            email='existing@example.com',
            password='password123',
            first_name='Existing User'
        )

    def test_register_user_success(self):
        response = self.client.post(reverse('register'), {
            'name': 'New Customer',
            'email': 'newcustomer@example.com',
            'password': 'secretpassword',
            'confirmPassword': 'secretpassword'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(email='newcustomer@example.com').exists())

    def test_register_password_mismatch(self):
        response = self.client.post(reverse('register'), {
            'name': 'Mismatch',
            'email': 'mismatch@example.com',
            'password': 'secretpassword1',
            'confirmPassword': 'secretpassword2'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email='mismatch@example.com').exists())

    def test_login_success(self):
        response = self.client.post(reverse('login'), {
            'username': 'existing@example.com',
            'password': 'password123'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('_auth_user_id' in self.client.session)

    def test_login_invalid_password(self):
        response = self.client.post(reverse('login'), {
            'username': 'existing@example.com',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_profile_update(self):
        self.client.login(username='existing@example.com', password='password123')
        response = self.client.post(reverse('users-profile'), {
            'name': 'Updated Name',
            'email': 'existing@example.com',
            'phone': '+1 555-123-4567',
            'password': '',
            'confirmPassword': ''
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated Name')
        self.assertEqual(self.user.profile.phone_number, '+1 555-123-4567')

    def test_customer_address_lifecycle(self):
        self.client.login(username='existing@example.com', password='password123')
        
        # Add Address
        response = self.client.post(reverse('user-address-add'), {
            'title': 'Primary Villa',
            'full_name': 'Existing User',
            'phone': '+1 555-987-6543',
            'street_address': '100 Ocean Drive',
            'city': 'Miami',
            'postal_code': '33139',
            'country': 'United States',
            'is_default': 'on'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.user.addresses.count(), 1)
        addr = self.user.addresses.first()
        self.assertTrue(addr.is_default)
        self.assertEqual(addr.city, 'Miami')

        # Add Second Address and set default
        addr2 = CustomerAddress.objects.create(
            user=self.user,
            title='Office HQ',
            full_name='Existing User',
            phone='+1 555-000-1111',
            street_address='500 Tech Blvd',
            city='Austin',
            postal_code='78701',
            country='United States',
            is_default=False
        )
        self.client.post(reverse('user-address-default', args=[addr2.id]), follow=True)
        addr.refresh_from_db()
        addr2.refresh_from_db()
        self.assertFalse(addr.is_default)
        self.assertTrue(addr2.is_default)

        # Delete Address
        self.client.post(reverse('user-address-delete', args=[addr.id]), follow=True)
        self.assertEqual(self.user.addresses.count(), 1)
