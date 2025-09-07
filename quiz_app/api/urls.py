'''URL routes for the quiz API.

Exposes:
- POST /api/createQuiz/          -> CreateQuizView (runs yt-dlp → Whisper → Gemini)
- GET  /api/quizzes/             -> QuizzesListView (list own quizzes with questions)
- GET  /api/quizzes/<id>/        -> QuizDetailView (retrieve a single quiz)
- PUT  /api/quizzes/<id>/        -> QuizDetailView (full update of metadata)
- PATCH /api/quizzes/<id>/       -> QuizDetailView (partial update of metadata)
- DELETE /api/quizzes/<id>/      -> QuizDetailView (delete quiz)

These paths are typically included under the project-level '/api/' prefix, e.g.:
    path('api/', include('quiz_app.api.urls'))
'''

from django.urls import path
from .views import CreateQuizView, QuizzesListView, QuizDetailView

urlpatterns = [
    path('createQuiz/', CreateQuizView.as_view(), name='api-create-quiz'),
    path('quizzes/', QuizzesListView.as_view(),  name='api-quizzes'),
    path('quizzes/<int:id>/', QuizDetailView.as_view(),  name='api-quiz-detail'),
]