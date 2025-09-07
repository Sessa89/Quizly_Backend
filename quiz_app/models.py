'''Data models for the quiz_app.

Models:
- Quiz: A quiz owned by a user and linked to a YouTube video.
- Question: A single multiple-choice question belonging to a quiz.

Notes:
- Questions are accessible from a quiz via the reverse relation 'questions'
  (see related_name on the ForeignKey).
- Basic integrity checks for Question are implemented in `clean()`.
'''

from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Quiz(models.Model):
    '''A quiz generated from a YouTube video transcript.'''

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    video_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        '''Readable representation used in admin and logs.'''

        return f"{self.title} (#{self.id})"
    
class Question(models.Model):
    '''A single multiple-choice question for a quiz.'''

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_title = models.CharField(max_length=500)
    question_options = models.JSONField()
    answer = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        '''Lightweight validation for options and answer consistency.

        Raises:
            ValueError: If the options are not a list of exactly 4 items,
                or if the answer is not among the options.
        '''
        
        if not isinstance(self.question_options, list) or len(self.question_options) != 4:
            raise ValueError('question_options must be a list of exactly 4 items.')
        if self.answer not in self.question_options:
            raise ValueError('answer must be one of question_options.')