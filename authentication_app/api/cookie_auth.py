'''Cookie-based JWT authentication backend.

This module provides `CookieJWTAuthentication`, a SimpleJWT-compatible
authentication class that accepts JWTs from either:
1) the standard `Authorization: Bearer <token>` header, or
2) an HttpOnly cookie named `access_token` (fallback).

Usage:
- Add to DRF settings (preferably *before* the default JWT auth) so the
  cookie fallback is attempted when no Authorization header is present:

    REST_FRAMEWORK = {
        'DEFAULT_AUTHENTICATION_CLASSES': [
            'authentication_app.api.cookie_auth.CookieJWTAuthentication',
            'rest_framework_simplejwt.authentication.JWTAuthentication',
        ],
    }

Security notes:
- This class only *reads* the cookie; setting/rotating cookies is done
  in the login/refresh views.
- Ensure cookies are issued with `HttpOnly`, `Secure` (in production),
  and an appropriate `SameSite` policy.
'''

from typing import Optional, Tuple
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken

class CookieJWTAuthentication(JWTAuthentication):
    '''Authenticate via Authorization header or, as a fallback, `access_token` cookie.

    Order of precedence:
      1) If an Authorization header is present, defer to the parent
         `JWTAuthentication` (standard behavior).
      2) Otherwise, look for an `access_token` in request cookies and validate it.

    Raises:
        AuthenticationFailed: If a cookie is present but contains an invalid token.

    Returns:
        Optional[Tuple[user, validated_token]]: None if no credentials are supplied.
    '''

    def authenticate(self, request: Request) -> Optional[Tuple[object, object]]:
        '''Attempt to authenticate the request.

        Args:
            request: The DRF request object.

        Returns:
            A tuple of (user, validated_token) if authentication succeeds,
            or None if no credentials are provided.

        Raises:
            AuthenticationFailed: If the cookie token is present but invalid.
        '''

        header = self.get_header(request)
        if header is not None:
            return super().authenticate(request)

        raw_token = request.COOKIES.get('access_token')
        if not raw_token:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
        except InvalidToken as exc:
            raise AuthenticationFailed('Invalid token.') from exc

        return self.get_user(validated_token), validated_token