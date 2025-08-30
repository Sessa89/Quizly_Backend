from django.conf import settings
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

def set_jwt_cookies(response, refresh: RefreshToken):
    access = refresh.access_token
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
