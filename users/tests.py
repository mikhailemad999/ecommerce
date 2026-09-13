from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

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
            'password': '',
            'confirmPassword': ''
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated Name')
