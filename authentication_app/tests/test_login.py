from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

class LoginTests(APITestCase):
    def setUp(self):
        self.url = reverse('api-login')
        self.user = User.objects.create_user(
            username='demo', email='demo@example.com', password='Abc123'
        )

    def test_login_success_sets_cookies_and_returns_user(self):
        resp = self.client.post(self.url, {'username': 'demo', 'password': 'Abc123'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['detail'], 'Login successfully!')
        self.assertEqual(resp.data['user']['username'], 'demo')
        
        self.assertIn('access_token', resp.cookies)
        self.assertIn('refresh_token', resp.cookies)

    def test_login_invalid_credentials(self):
        resp = self.client.post(self.url, {'username': 'demo', 'password': 'wrong'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(resp.data['detail'], 'Invalid credentials.')
