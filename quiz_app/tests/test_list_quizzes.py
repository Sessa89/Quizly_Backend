'''API tests for listing quizzes.

Covers:
- 401 when unauthenticated.
- 200 and filtering to only the authenticated user's quizzes.
- Ensures nested 'questions' are included with expected shape.

Notes:
- Uses the list endpoint: GET /api/quizzes/.
- Creates quizzes for two users; only the owner's quizzes should be returned.
'''

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from quiz_app.models import Quiz, Question

class QuizzesListTests(APITestCase):
    '''Tests for GET /api/quizzes/.'''

    def setUp(self):
        '''Create two users and three quizzes (two for u1, one for u2).'''

        self.url = reverse('api-quizzes')
        self.u1 = User.objects.create_user(username='u1', password='Abc123', email='u1@x.com')
        self.u2 = User.objects.create_user(username='u2', password='Abc123', email='u2@x.com')

        qz1 = Quiz.objects.create(owner=self.u1, title='QZ1', description='d1',
                                  video_url='https://www.youtube.com/watch?v=AAAAAAAAAAA')
        Question.objects.create(quiz=qz1, question_title='Q1',
                                question_options=['A','B','C','D'], answer='A')

        qz2 = Quiz.objects.create(owner=self.u1, title='QZ2', description='d2',
                                  video_url='https://www.youtube.com/watch?v=BBBBBBBBBBB')
        Question.objects.create(quiz=qz2, question_title='Q2',
                                question_options=['A','B','C','D'], answer='B')

        qz3 = Quiz.objects.create(owner=self.u2, title='QZ3', description='d3',
                                  video_url='https://www.youtube.com/watch?v=CCCCCCCCCCC')
        Question.objects.create(quiz=qz3, question_title='Q3',
                                question_options=['A','B','C','D'], answer='C')

    def test_list_quizzes_requires_auth(self):
        '''Unauthenticated requests must return 401.'''

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_quizzes_returns_only_own(self):
        '''Authenticated user sees only their own quizzes with nested questions.'''

        self.client.force_authenticate(self.u1)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 2)
        titles = {item['title'] for item in resp.data}
        self.assertSetEqual(titles, {'QZ1', 'QZ2'})
        
        self.assertTrue(isinstance(resp.data[0]['questions'], list))
        self.assertIn('question_title', resp.data[0]['questions'][0])