from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from quiz_app.models import Quiz, Question

class QuizPatchTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='u1', password='Abc123', email='u1@x.com')
        self.other = User.objects.create_user(username='u2', password='Abc123', email='u2@x.com')
        self.quiz = Quiz.objects.create(
            owner=self.owner,
            title='Old Title',
            description='Old Desc',
            video_url='https://www.youtube.com/watch?v=AAAAAAAAAAA',
        )
        Question.objects.create(
            quiz=self.quiz,
            question_title='Q1',
            question_options=['A','B','C','D'],
            answer='A',
        )
        self.url = reverse('api-quiz-detail', kwargs={'id': self.quiz.id})

    def test_requires_auth(self):
        resp = self.client.patch(self.url, {'title': 'X'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_forbidden_for_non_owner(self):
        self.client.force_authenticate(self.other)
        resp = self.client.patch(self.url, {'title': 'X'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_404_if_not_found(self):
        self.client.force_authenticate(self.owner)
        resp = self.client.patch(reverse('api-quiz-detail', kwargs={'id': 999}),
                                 {'title': 'X'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_title_only(self):
        self.client.force_authenticate(self.owner)
        resp = self.client.patch(self.url, {'title': 'Partially Updated'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['title'], 'Partially Updated')
        self.assertEqual(len(resp.data['questions']), 1)  # Fragen bleiben

    def test_patch_video_url_normalizes(self):
        self.client.force_authenticate(self.owner)
        resp = self.client.patch(self.url, {'video_url': 'https://youtu.be/BBBBBBBBBBB'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['video_url'], 'https://www.youtube.com/watch?v=BBBBBBBBBBB')

    def test_patch_empty_body_returns_400(self):
        self.client.force_authenticate(self.owner)
        resp = self.client.patch(self.url, {}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_invalid_url_returns_400(self):
        self.client.force_authenticate(self.owner)
        resp = self.client.patch(self.url, {'video_url': 'not-a-url'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)