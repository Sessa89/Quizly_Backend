'''API tests for the token refresh endpoint.

Covers:
- Successful refresh reads the 'refresh_token' cookie, returns 200,
  sets a new 'access_token' cookie, and echoes the access token in the body.
- Missing refresh cookie -> 401.
- Invalid refresh cookie -> 401.

Notes:
- Tests simulate the presence/absence of the refresh cookie by writing directly
  into the DRF test client's cookie jar.
'''

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

class TokenRefreshTests(APITestCase):
    '''Tests for POST /api/token/refresh/.'''

    def setUp(self):
        '''Create a user and store the endpoint URL.'''

        self.url = reverse('api-token-refresh')
        self.user = User.objects.create_user(username='alice', email='alice@example.com', password='Abc123')

    def test_refresh_success_sets_new_access_cookie(self):
        '''Valid refresh cookie should yield 200 and set a fresh access cookie.'''

        refresh = RefreshToken.for_user(self.user)
        self.client.cookies['refresh_token'] = str(refresh)

        resp = self.client.post(self.url, {}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['detail'], 'Token refreshed')
        self.assertIn('access', resp.data)
        self.assertIn('access_token', resp.cookies)
        self.assertEqual(resp.data['access'], resp.cookies['access_token'].value)

    def test_refresh_missing_cookie_returns_401(self):
        '''No refresh cookie -> 401 Unauthorized.'''

        resp = self.client.post(self.url, {}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_invalid_cookie_returns_401(self):
        '''Malformed/invalid refresh cookie -> 401 Unauthorized.'''
        
        self.client.cookies['refresh_token'] = 'not-a-valid-token'
        resp = self.client.post(self.url, {}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)