'''URL routes for authentication endpoints.

Exposes:
- POST /api/register/        -> RegisterView
- POST /api/login/           -> LoginView (sets JWT cookies)
- POST /api/logout/          -> LogoutView (blacklists refresh + clears cookies)
- POST /api/token/refresh/   -> CookieTokenRefreshView (rotates access cookie)

These paths are typically included under the project-level '/api/' prefix, e.g.:
    path('api/', include('authentication_app.api.urls'))
'''

from django.urls import path
from .auth import LoginView, LogoutView, CookieTokenRefreshView
from .views import RegisterView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='api-register'),
    path('login/', LoginView.as_view(), name='api-login'),
    path('logout/', LogoutView.as_view(), name='api-logout'),
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='api-token-refresh'),
]