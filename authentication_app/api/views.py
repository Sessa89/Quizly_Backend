'''Registration view for the authentication_app.

Exposes:
- POST /api/register/  -> Create a new user account.

Notes:
- This endpoint intentionally overrides the project-wide default permission
  (IsAuthenticated) with AllowAny so unauthenticated users can register.
- Validation rules are enforced by RegistrationSerializer:
  * unique username and email
  * password validated by Django's AUTH_PASSWORD_VALIDATORS
  * password is write-only
'''

from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from .serializers import RegistrationSerializer

class RegisterView(CreateAPIView):
    '''Create a new user account.

    Endpoint:
        POST /api/register/

    Request body (JSON):
        - username: str (unique, required)
        - email: str (unique, required, valid email)
        - password: str (required; validated by Django's password validators)

    Responses:
        201: {'detail': 'User created successfully!'}
        400: Validation errors for username/email/password
    '''

    serializer_class = RegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request: Request, *args, **kwargs) -> Response:
        '''Validate payload, create the user, and return a success message.'''
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        return Response(
            {'detail': 'User created successfully!'},
            status=status.HTTP_201_CREATED,
            headers=headers
        )