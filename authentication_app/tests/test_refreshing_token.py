from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

class TokenRefreshTests(APITestCase):
    def setUp(self):
        self.url = reverse('api-token-refresh')
        self.user = User.objects.create_user(username='alice', email='alice@example.com', password='Abc123')

    def test_refresh_success_sets_new_access_cookie(self):
        refresh = RefreshToken.for_user(self.user)
        self.client.cookies['refresh_token'] = str(refresh)

        resp = self.client.post(self.url, {}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['detail'], 'Token refreshed')
        self.assertIn('access', resp.data)
        self.assertIn('access_token', resp.cookies)
        self.assertEqual(resp.data['access'], resp.cookies['access_token'].value)

    def test_refresh_missing_cookie_returns_401(self):
        resp = self.client.post(self.url, {}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_invalid_cookie_returns_401(self):
        self.client.cookies['refresh_token'] = 'not-a-valid-token'
        resp = self.client.post(self.url, {}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
