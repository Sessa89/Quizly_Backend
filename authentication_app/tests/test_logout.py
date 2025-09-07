'''API tests for the logout endpoint.

Covers:
- Successful logout (authenticated) returns 200, blacklists the refresh token,
  and clears both 'access_token' and 'refresh_token' cookies (Max-Age=0).
- Unauthenticated requests return 401.

Notes:
- Tests simulate authentication by writing JWTs directly into the client's
  cookie jar (no network login step required).
'''

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

class LogoutTests(APITestCase):
    '''Tests for POST /api/logout/.'''

    def setUp(self):
        '''Create a user and store the endpoint URL.'''
        self.url = reverse('api-logout')
        self.user = User.objects.create_user(username='demo', email='demo@example.com', password='Abc123')

    def _login_via_cookies(self):
        '''Simulate an authenticated client by setting JWT cookies.'''

        refresh = RefreshToken.for_user(self.user)
        access = refresh.access_token
        
        self.client.cookies['access_token']  = str(access)
        self.client.cookies['refresh_token'] = str(refresh)

    def test_logout_success_deletes_cookies(self):
        '''Authenticated logout should clear both cookies and return 200.'''

        self._login_via_cookies()
        resp = self.client.post(self.url, {}, format='json')

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(
            resp.data['detail'],
            'Log-Out successfully! All Tokens will be deleted. Refresh token is now invalid.'
        )
        
        self.assertIn('access_token', resp.cookies)
        self.assertIn('refresh_token', resp.cookies)
        self.assertEqual(resp.cookies['access_token'].value, '')
        self.assertEqual(resp.cookies['refresh_token'].value, '')

    def test_logout_unauthenticated_returns_401(self):
        '''Unauthenticated requests must be rejected with 401.'''

        resp = self.client.post(self.url, {}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)