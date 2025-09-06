from django.urls import path
from .views import CreateQuizView, QuizzesListView

urlpatterns = [
    path('createQuiz/', CreateQuizView.as_view(), name='api-create-quiz'),
    path('quizzes/', QuizzesListView.as_view(),  name='api-quizzes'),
]
