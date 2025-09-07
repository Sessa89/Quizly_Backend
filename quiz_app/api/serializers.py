'''Serializers for the quiz app API.

Provides:
- QuestionSerializer: read-only representation of a question model.
- QuizSerializer: quiz with nested questions (used for GET responses).
- QuizUpdateSerializer: strict full update (PUT) of quiz metadata.
- QuizPartialUpdateSerializer: partial update (PATCH) of quiz metadata.

Notes:
- Question options are stored as a JSON list on the model and serialized as-is.
- Video URLs are normalized to the canonical YouTube form
  'https://www.youtube.com/watch?v=<id>' via validation.
'''

from rest_framework import serializers
from ..models import Quiz, Question

class QuestionSerializer(serializers.ModelSerializer):
    '''Serialize a single quiz question.

    Fields:
        id: PK.
        question_title: The text of the question.
        question_options: A list of exactly 4 distinct answer options.
        answer: The correct option (must be one of question_options).
        created_at / updated_at: Timestamps.
    '''

    class Meta:
        model = Question
        fields = ['id', 'question_title', 'question_options', 'answer', 'created_at', 'updated_at']

class QuizSerializer(serializers.ModelSerializer):
    '''Serialize a quiz including its nested questions (read-only for questions).'''

    questions = QuestionSerializer(many=True)

    class Meta:
        model = Quiz
        fields = ['id', 'title', 'description', 'created_at', 'updated_at', 'video_url', 'questions']

class QuizUpdateSerializer(serializers.ModelSerializer):
    '''Serializer for full replacement (PUT) of quiz metadata.

    Requires all three fields. The provided YouTube URL is validated and
    normalized to the canonical watch URL.
    '''

    title = serializers.CharField(required=True, max_length=255)
    description = serializers.CharField(required=True, allow_blank=False)
    video_url = serializers.URLField(required=True)

    class Meta:
        model = Quiz
        fields = ['title', 'description', 'video_url']

    def validate_video_url(self, value: str) -> str:
        '''Validate and normalize a YouTube URL to the canonical watch form.'''

        from .services import extract_youtube_id, YOUTUBE_CANONICAL
        try:
            vid = extract_youtube_id(value)
        except ValueError:
            raise serializers.ValidationError('Invalid YouTube URL.')
        return YOUTUBE_CANONICAL.format(vid=vid)
    
class QuizPartialUpdateSerializer(serializers.ModelSerializer):
    '''Serializer for partial updates (PATCH) of quiz metadata.

    At least one of the fields must be present. If 'video_url' is provided,
    it is validated and normalized to the canonical watch URL.
    '''

    title = serializers.CharField(required=False, max_length=255)
    description = serializers.CharField(required=False, allow_blank=False)
    video_url = serializers.URLField(required=False)

    class Meta:
        model = Quiz
        fields = ['title', 'description', 'video_url']

    def validate(self, attrs):
        '''Ensure that the payload contains at least one field.'''

        if not attrs:
            raise serializers.ValidationError('At least one field must be provided.')
        return attrs

    def validate_video_url(self, value: str) -> str:
        '''Validate and normalize a YouTube URL to the canonical watch form.'''
        
        from .services import extract_youtube_id, YOUTUBE_CANONICAL
        try:
            vid = extract_youtube_id(value)
        except ValueError:
            raise serializers.ValidationError('Invalid YouTube URL.')
        return YOUTUBE_CANONICAL.format(vid=vid)