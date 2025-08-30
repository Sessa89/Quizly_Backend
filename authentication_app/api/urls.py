from django.urls import path
from .auth import LoginView, LogoutView, CookieTokenRefreshView
from .views import RegisterView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='api-register'),
    path('login/', LoginView.as_view(), name='api-login'),
    path('logout/', LogoutView.as_view(), name='api-logout'),
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='api-token-refresh'),
]