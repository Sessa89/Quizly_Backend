from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse


class RegisterTest(APITestCase):
    def setUp(self):
        self.url = reverse('api-register')
        self.payload = {
            "username": "Testuser",
            "email": "user@example.com",
            "password": "VerySafePass123"
        }

    def test_register_success_returns_201_and_expected_payload(self):
        resp = self.client.post(self.url, self.payload, format='json')

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data.get("detail"), "User created successfully!")
        self.assertTrue(User.objects.filter(username="Testuser").exists())

    def test_register_duplicate_username(self):
        User.objects.create_user(
            username="Testuser2", email="user@example.com", password="pass12345")
        url = reverse('api-register')
        payload = {"username": "Testuser2",
                   "email": "testuser@example.com", "password": "pass12345"}
        resp = self.client.post(url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", resp.data)

    def test_register_duplicate_email(self):
        User.objects.create_user(
            username="u1", email="dup@x.com", password="pass12345")
        url = reverse('api-register')
        payload = {"username": "u2",
                   "email": "dup@x.com", "password": "pass12345"}
        resp = self.client.post(url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", resp.data)

    def test_register_weak_password(self):
        url = reverse('api-register')
        payload = {"username": "weak",
                   "email": "weak@x.com", "password": "123"}
        resp = self.client.post(url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", resp.data)

    def test_register_too_short_5_chars(self):
        resp = self.client.post(self.url, {
            "username": "shorty",
            "email": "shorty@example.com",
            "password": "aB12!"
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", resp.data)
