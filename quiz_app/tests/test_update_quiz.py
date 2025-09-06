from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from quiz_app.models import Quiz, Question

class QuizUpdateTests(APITestCase):
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

    def test_put_requires_auth(self):
        resp = self.client.put(self.url, {}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_put_forbidden_if_not_owner(self):
        self.client.force_authenticate(self.other)
        payload = {
            'title': 'New Title',
            'description': 'New Desc',
            'video_url': 'https://www.youtube.com/watch?v=BBBBBBBBBBB',
        }
        resp = self.client.put(self.url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_put_404_if_not_found(self):
        self.client.force_authenticate(self.owner)
        bad_url = reverse('api-quiz-detail', kwargs={'id': 999})
        payload = {
            'title': 'New Title',
            'description': 'New Desc',
            'video_url': 'https://www.youtube.com/watch?v=BBBBBBBBBBB',
        }
        resp = self.client.put(bad_url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_put_success_updates_fields_and_keeps_questions(self):
        self.client.force_authenticate(self.owner)
        payload = {
            'title': 'Updated Quiz Title',
            'description': 'Updated Quiz Description',
            'video_url': 'https://youtu.be/BBBBBBBBBBB',
        }
        resp = self.client.put(self.url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['title'], payload['title'])
        self.assertEqual(resp.data['description'], payload['description'])
        self.assertEqual(resp.data['video_url'], 'https://www.youtube.com/watch?v=BBBBBBBBBBB')
        
        self.assertEqual(len(resp.data['questions']), 1)
        self.assertEqual(resp.data['questions'][0]['question_title'], 'Q1')

    def test_put_invalid_payload_returns_400(self):
        self.client.force_authenticate(self.owner)
        
        bad = {'title': 'X', 'description': 'Y'}
        resp = self.client.put(self.url, bad, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("video_url", resp.data)

        bad2 = {'title': 'X', 'description': 'Y', 'video_url': 'not-a-url'}
        resp = self.client.put(self.url, bad2, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
