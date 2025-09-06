from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch
from quiz_app.models import Quiz, Question

class CreateQuizTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='Testuser', password='Abc123', email='testuser@test.com')
        self.client.force_authenticate(self.user)
        self.url = reverse('api-create-quiz')

    @patch('quiz_app.api.views.create_quiz_from_youtube')
    def test_create_quiz_success(self, mock_create):
        quiz = Quiz.objects.create(owner=self.user, title='Quiz Title',
                                   description='Quiz Desc', video_url='https://www.youtube.com/watch?v=AAAAAAAAAAA')
        Question.objects.create(quiz=quiz, question_title='Q1',
                                question_options=['A','B','C','D'], answer='A')
        mock_create.return_value = quiz

        resp = self.client.post(self.url, {'url': 'https://youtu.be/AAAAAAAAAAA'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['title'], 'Quiz Title')
        self.assertEqual(resp.data['video_url'], 'https://www.youtube.com/watch?v=AAAAAAAAAAA')
        self.assertEqual(len(resp.data['questions']), 1)

    def test_create_quiz_missing_url(self):
        resp = self.client.post(self.url, {}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
