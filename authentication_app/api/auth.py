from django.conf import settings
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

def _cookie_kwargs():
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

def set_jwt_cookies(response, refresh: RefreshToken):
    access = refresh.access_token
    common = _cookie_kwargs()
    secure_cookie = not settings.DEBUG

    response.set_cookie(
        key='access_token',
        value=str(access),
        httponly=True,
        samesite='Lax',
        secure=secure_cookie,
        max_age=int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()),
        path='/',
    )
    response.set_cookie(
        key='refresh_token',
        value=str(refresh),
        httponly=True,
        samesite='Lax',
        secure=secure_cookie,
        max_age=int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()),
        path='/',
    )
    return response

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
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
    permission_classes = [IsAuthenticated]

    def post(self, request):
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
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_str = request.COOKIES.get('refresh_token')
        if not refresh_str:
            return Response({'detail': 'Missing refresh token.'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            refresh = RefreshToken(refresh_str)
            new_access = refresh.access_token
        except Exception:
            return Response({'detail': 'Invalid refresh token.'}, status=status.HTTP_401_UNAUTHORIZED)

        resp = Response({'detail': 'Token refreshed', 'access': str(new_access)}, status=status.HTTP_200_OK)

        secure_cookie = not settings.DEBUG
        resp.set_cookie(
            key='access_token',
            value=str(new_access),
            httponly=True,
            samesite='Lax',
            secure=secure_cookie,
            max_age=int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()),
            path='/',
        )
        return resp