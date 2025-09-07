from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from quiz_app.models import Quiz, Question

class QuizDeleteTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='u1', password='Abc123', email='u1@x.com')
        self.other = User.objects.create_user(username='u2', password='Abc123', email='u2@x.com')
        self.quiz = Quiz.objects.create(
            owner=self.owner,
            title='Del Me',
            description='desc',
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
        resp = self.client.delete(self.url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_forbidden_for_non_owner(self):
        self.client.force_authenticate(self.other)
        resp = self.client.delete(self.url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_404_if_not_found(self):
        self.client.force_authenticate(self.owner)
        resp = self.client.delete(reverse('api-quiz-detail', kwargs={'id': 999}))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_success_204_and_cascade(self):
        self.client.force_authenticate(self.owner)
        resp = self.client.delete(self.url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Quiz.objects.filter(id=self.quiz.id).exists())
        self.assertEqual(Question.objects.filter(quiz_id=self.quiz.id).count(), 0)