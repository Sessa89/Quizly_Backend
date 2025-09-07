'''API tests for the login endpoint.

Covers:
- Successful login returns 200, includes a short user payload, and sets
  HttpOnly cookies 'access_token' and 'refresh_token'.
- Invalid credentials return 401 with the expected error message.

Preconditions:
- SimpleJWT is configured.
- Cookie issuing is handled by LoginView via set_jwt_cookies(...).
'''

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

class LoginTests(APITestCase):
    '''Tests for POST /api/login/.'''

    def setUp(self):
        '''Create a test user and store the endpoint URL.'''

        self.url = reverse('api-login')
        self.user = User.objects.create_user(
            username='demo', email='demo@example.com', password='Abc123'
        )

    def test_login_success_sets_cookies_and_returns_user(self):
        '''Successful login yields 200, returns user data, and sets JWT cookies.'''

        resp = self.client.post(self.url, {'username': 'demo', 'password': 'Abc123'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['detail'], 'Login successfully!')
        self.assertEqual(resp.data['user']['username'], 'demo')
        
        self.assertIn('access_token', resp.cookies)
        self.assertIn('refresh_token', resp.cookies)

    def test_login_invalid_credentials(self):
        '''Invalid credentials must return 401 with the canonical error message.'''

        resp = self.client.post(self.url, {'username': 'demo', 'password': 'wrong'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(resp.data['detail'], 'Invalid credentials.')