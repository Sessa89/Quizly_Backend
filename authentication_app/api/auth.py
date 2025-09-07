"""
Authentication views and helpers for cookie-based JWT authentication.

Exposes the following endpoints (mounted under /api/):
- POST /api/login/          -> issues access/refresh tokens as HttpOnly cookies
- POST /api/logout/         -> blacklists the refresh token and deletes cookies
- POST /api/token/refresh/  -> reads refresh cookie, issues a new access cookie

Auth model:
- Login issues HttpOnly cookies: 'access_token' and 'refresh_token'.
- Refresh reads 'refresh_token' from cookie and rotates 'access_token'.
- Logout blacklists the refresh token (requires SimpleJWT blacklist app)
  and deletes both cookies.

Security notes:
- Cookies are set with 'secure=not DEBUG' and 'httponly=True'.
- You may configure 'COOKIE_SAMESITE' and 'COOKIE_DOMAIN' in settings.

Dependencies:
- Django, Django REST Framework
- djangorestframework-simplejwt (+ token_blacklist app)
"""

from django.conf import settings
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken


def _cookie_kwargs() -> dict:
    '''Common keyword arguments for JWT cookies.

    Returns:
        dict: Keyword arguments consistently applied when setting or deleting
        'access_token' and 'refresh_token' cookies. Includes:
        - httponly: always True
        - secure: True in production (DEBUG=False)
        - samesite: from settings.COOKIE_SAMESITE (default 'Lax')
        - path: '/'
        - domain: from settings.COOKIE_DOMAIN if provided
    '''

    kwargs = dict(
        httponly=True,
        secure=not settings.DEBUG,
        samesite=getattr(settings, 'COOKIE_SAMESITE', 'Lax'),
        path='/',
    )
    domain = getattr(settings, 'COOKIE_DOMAIN', None)
    if domain:
        kwargs['domain'] = domain
    return kwargs

def set_jwt_cookies(response: Response, refresh: RefreshToken) -> Response:
    '''Set HttpOnly JWT cookies for access and refresh tokens.

    Args:
        response: The response object to attach cookies to.
        refresh: A SimpleJWT RefreshToken instance for the authenticated user.

    Returns:
        Response: The same response with 'access_token' and 'refresh_token' cookies set.
    '''

    access = refresh.access_token
    common = _cookie_kwargs()
    secure_cookie = not settings.DEBUG

    response.set_cookie(
        key='access_token',
        value=str(access),
        httponly=True,
        samesite='Lax',
        secure=secure_cookie,
        max_age=int(
            settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()),
        path='/',
    )
    response.set_cookie(
        key='refresh_token',
        value=str(refresh),
        httponly=True,
        samesite='Lax',
        secure=secure_cookie,
        max_age=int(
            settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()),
        path='/',
    )
    return response

class LoginView(APIView):
    '''Authenticate a user and issue JWT cookies.

    Endpoint:
        POST /api/login/

    Request body (JSON):
        - username: str
        - password: str

    Responses:
        200: {'detail': 'Login successfully!', 'user': {...}} and sets cookies
        401: {'detail': 'Invalid credentials.'}
    '''

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        '''Authenticate credentials and set JWT cookies on success.'''

        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(request, username=username, password=password)
        if not user:
            return Response({'detail': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        resp = Response(
            {
                'detail': 'Login successfully!',
                "user": {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email},
            },
            status=status.HTTP_200_OK,
        )
        return set_jwt_cookies(resp, refresh)

class LogoutView(APIView):
    '''Invalidate refresh token and clear JWT cookies.

    Endpoint:
        POST /api/logout/

    Auth:
        Requires a valid access token (cookie or Authorization header).

    Responses:
        200: Detail message and both cookies cleared.
        401: If unauthenticated.
    '''

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        '''Blacklist the refresh token (if present) and delete cookies.'''

        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception:
                pass

        resp = Response(
            {'detail': 'Log-Out successfully! All Tokens will be deleted. Refresh token is now invalid.'},
            status=status.HTTP_200_OK
        )

        resp.delete_cookie('access_token', path='/', samesite='Lax')
        resp.delete_cookie('refresh_token', path='/', samesite='Lax')
        return resp

class CookieTokenRefreshView(APIView):
    '''Issue a new access token by reading the refresh token cookie.

    Endpoint:
        POST /api/token/refresh/

    Behavior:
        Reads 'refresh_token' from cookies, validates it (including blacklist),
        and sets a fresh 'access_token' cookie. Also returns the access token in the body.

    Responses:
        200: {'detail': 'Token refreshed', 'access': '<jwt>'} and sets cookie
        401: {'detail': 'Missing refresh token.'} or {'detail': 'Invalid refresh token.'}
    '''

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        '''Refresh the access token using the refresh cookie.'''
        
        refresh_str = request.COOKIES.get('refresh_token')
        if not refresh_str:
            return Response({'detail': 'Missing refresh token.'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            refresh = RefreshToken(refresh_str)
            new_access = refresh.access_token
        except Exception:
            return Response({'detail': 'Invalid refresh token.'}, status=status.HTTP_401_UNAUTHORIZED)

        resp = Response({'detail': 'Token refreshed', 'access': str(
            new_access)}, status=status.HTTP_200_OK)

        secure_cookie = not settings.DEBUG
        resp.set_cookie(
            key='access_token',
            value=str(new_access),
            httponly=True,
            samesite='Lax',
            secure=secure_cookie,
            max_age=int(
                settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()),
            path='/',
        )
        return resp