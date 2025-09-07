'''API tests for retrieving a single quiz (detail view).

Covers:
- 401 when unauthenticated.
- 404 when the quiz id does not exist.
- 403 when the requester is not the owner.
- 200 with full payload (including nested questions) for the owner.

Notes:
- Uses the detail endpoint: GET /api/quizzes/<id>/.
'''

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from quiz_app.models import Quiz, Question

class QuizDetailTests(APITestCase):
    '''Tests for GET /api/quizzes/<id>/.'''

    def setUp(self):
        '''Create two users and a quiz owned by the first user.'''

        self.u1 = User.objects.create_user(username='u1', password='Abc123', email='u1@x.com')
        self.u2 = User.objects.create_user(username='u2', password='Abc123', email='u2@x.com')

        self.quiz_u1 = Quiz.objects.create(
            owner=self.u1, title='My Quiz', description='desc',
            video_url='https://www.youtube.com/watch?v=AAAAAAAAAAA'
        )
        Question.objects.create(
            quiz=self.quiz_u1, question_title='Q1',
            question_options=['A','B','C','D'], answer='A'
        )

        self.detail_url = lambda qid: reverse('api-quiz-detail', kwargs={'id': qid})

    def test_requires_auth(self):
        '''Unauthenticated requests must return 401.'''

        resp = self.client.get(self.detail_url(self.quiz_u1.id))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_404_when_not_found(self):
        '''Requesting a non-existent quiz returns 404.'''

        self.client.force_authenticate(self.u1)
        resp = self.client.get(self.detail_url(999))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_403_when_not_owner(self):
        '''A different authenticated user must receive 403.'''

        self.client.force_authenticate(self.u2)
        resp = self.client.get(self.detail_url(self.quiz_u1.id))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_200_and_payload_for_owner(self):
        '''Owner can retrieve the quiz and sees nested questions.'''

        self.client.force_authenticate(self.u1)
        resp = self.client.get(self.detail_url(self.quiz_u1.id))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['id'], self.quiz_u1.id)
        self.assertEqual(resp.data['title'], 'My Quiz')
        self.assertTrue(isinstance(resp.data['questions'], list))
        self.assertEqual(resp.data['questions'][0]['answer'], 'A')