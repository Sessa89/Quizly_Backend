from django.urls import path
from .auth import LoginView
from .views import RegisterView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='api-register'),
    path('login/', LoginView.as_view(), name='api-login'),
]