from django.conf import settings

from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Quiz
from .serializers import QuizSerializer
from .services import create_quiz_from_youtube

class CreateQuizView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        url = request.data.get('url', '').strip()
        if not url:
            return Response({'detail': "Missing 'url'."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            quiz = create_quiz_from_youtube(url, owner=request.user, num_questions=10)
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            if settings.DEBUG:
                return Response({'detail': f"Internal server error: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({'detail': 'Internal server error.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(QuizSerializer(quiz).data, status=status.HTTP_201_CREATED)
    
class QuizzesListView(ListAPIView):
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Quiz.objects
            .filter(owner=self.request.user)
            .prefetch_related('questions')
            .order_by('-created_at')
        )
    
class QuizDetailView(RetrieveAPIView):
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        quiz_id = self.kwargs.get('id') or self.kwargs.get('pk')
        try:
            obj = (Quiz.objects
                   .prefetch_related('questions')
                   .get(pk=quiz_id))
        except Quiz.DoesNotExist:
            raise NotFound('Quiz not found.')

        if obj.owner_id != self.request.user.id:
            raise PermissionDenied('You do not have permission to access this quiz.')

        return obj