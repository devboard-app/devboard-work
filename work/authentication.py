from dataclasses import dataclass

from django.conf import settings
from jose import JWTError, jwt
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


@dataclass
class TokenUser:
    user_id: str
    email: str | None
    role: str | None
    is_authenticated: bool = True


class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ')[1]

        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=['HS256'])
        except JWTError:
            raise AuthenticationFailed('Invalid or expired token')

        user_id = payload.get('sub')
        email = payload.get('email')
        role = payload.get('role')

        if not user_id:
            raise AuthenticationFailed('Invalid token payload')

        return (TokenUser(user_id=user_id, email=email, role=role), token)
