from django.urls import path
from .views import CreateQuizView, QuizzesListView, QuizDetailView

urlpatterns = [
    path('createQuiz/', CreateQuizView.as_view(), name='api-create-quiz'),
    path('quizzes/', QuizzesListView.as_view(),  name='api-quizzes'),
    path('quizzes/<int:id>/', QuizDetailView.as_view(),  name='api-quiz-detail'),
]
