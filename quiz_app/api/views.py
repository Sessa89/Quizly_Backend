'''Views for the quiz API.

Exposes:
- POST /api/createQuiz/          -> CreateQuizView (runs yt-dlp → Whisper → Gemini)
- GET  /api/quizzes/             -> QuizzesListView (list own quizzes with questions)
- GET  /api/quizzes/<id>/        -> QuizDetailView (retrieve a single quiz)
- PUT  /api/quizzes/<id>/        -> QuizDetailView (full update of metadata)
- PATCH /api/quizzes/<id>/       -> QuizDetailView (partial update of metadata)
- DELETE /api/quizzes/<id>/      -> QuizDetailView (delete quiz)

Notes:
- All endpoints require authentication via cookie-based JWT (or Authorization header).
- The service layer raises ValueError for expected client errors (mapped to 400),
  everything else bubbles up as 500 (with debug detail in DEBUG mode).
'''

from django.conf import settings

from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Quiz
from .serializers import QuizSerializer, QuizUpdateSerializer, QuizPartialUpdateSerializer
from .services import create_quiz_from_youtube

class CreateQuizView(APIView):
    '''Create a new quiz from a YouTube URL (full pipeline).

    Endpoint:
        POST /api/createQuiz/

    Request body (JSON):
        - url: str (required) — any valid YouTube URL (watch/embed/short).

    Responses:
        201: Returns the created quiz with nested questions.
        400: For expected failures (invalid URL, unavailable video, missing FFmpeg,
             missing GEMINI_API_KEY, invalid LLM JSON, etc.).
        500: Unexpected server errors (shows exception text in DEBUG mode).
    '''

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
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
    '''List all quizzes owned by the authenticated user.

    Endpoint:
        GET /api/quizzes/

    Responses:
        200: A list of quizzes with nested questions.
        401: If unauthenticated.
    '''

    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Quiz.objects
            .filter(owner=self.request.user)
            .prefetch_related('questions')
            .order_by('-created_at')
        )
    
class QuizDetailView(RetrieveUpdateDestroyAPIView):
    '''Retrieve, update, or delete a single quiz by id.

    Endpoints:
        GET    /api/quizzes/<id>/   -> retrieve quiz with questions
        PUT    /api/quizzes/<id>/   -> full update of metadata (title/description/video_url)
        PATCH  /api/quizzes/<id>/   -> partial update of metadata
        DELETE /api/quizzes/<id>/   -> delete quiz (204 No Content)

    Permission rules:
        - 404 if the quiz does not exist.
        - 403 if the quiz exists but the current user is not the owner.
    '''
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'PUT':
            return QuizUpdateSerializer
        if self.request.method == 'PATCH':
            return QuizPartialUpdateSerializer
        return QuizSerializer

    def get_object(self) -> Quiz:
        quiz_id = self.kwargs.get('id') or self.kwargs.get('pk')
        try:
            obj = (Quiz.objects.prefetch_related('questions').get(pk=quiz_id))
        except Quiz.DoesNotExist:
            raise NotFound('Quiz not found.')
        if obj.owner_id != self.request.user.id:
            raise PermissionDenied('You do not have permission to access this quiz.')
        return obj
    
    def put(self, request: Request, *args, **kwargs) -> Response:
        '''Full update (replace) of quiz metadata.'''

        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(QuizSerializer(instance).data, status=status.HTTP_200_OK)
    
    def patch(self, request: Request, *args, **kwargs) -> Response:
        '''Partial update of quiz metadata.'''

        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(QuizSerializer(instance).data, status=status.HTTP_200_OK)
    
    def delete(self, request: Request, *args, **kwargs) -> Response:
        '''Delete the quiz and return 204 No Content.'''
        
        instance = self.get_object()
        instance.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)