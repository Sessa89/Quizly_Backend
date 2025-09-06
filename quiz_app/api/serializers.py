from rest_framework import serializers
from ..models import Quiz, Question

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'question_title', 'question_options', 'answer', 'created_at', 'updated_at']

class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True)

    class Meta:
        model = Quiz
        fields = ['id', 'title', 'description', 'created_at', 'updated_at', 'video_url', 'questions']

class QuizUpdateSerializer(serializers.ModelSerializer):
    title = serializers.CharField(required=True, max_length=255)
    description = serializers.CharField(required=True, allow_blank=False)
    video_url = serializers.URLField(required=True)

    class Meta:
        model = Quiz
        fields = ['title', 'description', 'video_url']

    def validate_video_url(self, value: str) -> str:
        from .services import extract_youtube_id, YOUTUBE_CANONICAL
        try:
            vid = extract_youtube_id(value)
        except ValueError:
            raise serializers.ValidationError('Invalid YouTube URL.')
        return YOUTUBE_CANONICAL.format(vid=vid)