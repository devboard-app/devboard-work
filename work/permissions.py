import hmac

from django.conf import settings
from rest_framework.permissions import BasePermission


class IsInternalService(BasePermission):
    def has_permission(self, request, view):
        key = request.headers.get('X-Service-Key')
        if key is None:
            return False
        return hmac.compare_digest(key, settings.INTERNAL_API_KEY)