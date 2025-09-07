'''API tests for fully updating a quiz (PUT).

Covers:
- 401 when unauthenticated.
- 403 when the requester is not the owner.
- 404 when the quiz id does not exist.
- 200 on successful full update; questions remain unchanged.
- 400 on invalid payload (missing required fields or invalid URL).
- Normalization of 'video_url' to canonical YouTube form.

Notes:
- Uses the detail endpoint: PUT /api/quizzes/<id>/.
'''

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from quiz_app.models import Quiz, Question

class QuizUpdateTests(APITestCase):
    '''Tests for PUT /api/quizzes/<id>/.'''

    def setUp(self):
        '''Create two users and a quiz owned by the first user.'''

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
        '''Unauthenticated requests must return 401.'''

        resp = self.client.put(self.url, {}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_put_forbidden_if_not_owner(self):
        '''A different authenticated user must receive 403.'''

        self.client.force_authenticate(self.other)
        payload = {
            'title': 'New Title',
            'description': 'New Desc',
            'video_url': 'https://www.youtube.com/watch?v=BBBBBBBBBBB',
        }
        resp = self.client.put(self.url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_put_404_if_not_found(self):
        '''Updating a non-existent quiz returns 404.'''

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
        '''Owner can fully update metadata; questions remain intact.'''

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
        '''Missing required fields or invalid URL should yield 400.'''
        
        self.client.force_authenticate(self.owner)
        
        bad = {'title': 'X', 'description': 'Y'}
        resp = self.client.put(self.url, bad, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("video_url", resp.data)

        bad2 = {'title': 'X', 'description': 'Y', 'video_url': 'not-a-url'}
        resp = self.client.put(self.url, bad2, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)