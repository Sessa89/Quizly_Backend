'''API tests for deleting a quiz.

Covers:
- 401 when unauthenticated.
- 403 when the requester is not the owner.
- 404 when the quiz id does not exist.
- 204 and cascade delete of related questions on successful deletion.

Notes:
- Uses the detail endpoint: DELETE /api/quizzes/<id>/.
- Questions are expected to be removed via FK(on_delete=CASCADE).
'''

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from quiz_app.models import Quiz, Question

class QuizDeleteTests(APITestCase):
    '''Tests for DELETE /api/quizzes/<id>/.'''

    def setUp(self):
        '''Create two users and one quiz with a single question.'''

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
        '''Unauthenticated requests must return 401.'''

        resp = self.client.delete(self.url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_forbidden_for_non_owner(self):
        '''A different authenticated user must receive 403.'''

        self.client.force_authenticate(self.other)
        resp = self.client.delete(self.url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_404_if_not_found(self):
        '''Deleting a non-existent quiz returns 404.'''

        self.client.force_authenticate(self.owner)
        resp = self.client.delete(reverse('api-quiz-detail', kwargs={'id': 999}))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_success_204_and_cascade(self):
        '''Owner can delete; response is 204 and related questions are removed.'''
        
        self.client.force_authenticate(self.owner)
        resp = self.client.delete(self.url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Quiz.objects.filter(id=self.quiz.id).exists())
        self.assertEqual(Question.objects.filter(quiz_id=self.quiz.id).count(), 0)