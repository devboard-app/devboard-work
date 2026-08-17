import httpx
from django.conf import settings
from rest_framework.exceptions import APIException, ValidationError


class ServiceUnavaiable(APIException):
    status_code = 502
    default_detail = 'A downstream service is unavailable.'
    

async def get_user_id_by_email(email: str) -> str | None:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f'{settings.CORE_SERVICE_URL}/api/users/search/',
                params={'email': email},
                headers={'X-Service-Key': settings.INTERNAL_API_KEY}
            )
    except httpx.TransportError:
        raise ServiceUnavaiable()

    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json().get('user_id')

async def send_member_notification(to: str, team_name: str, inviter_name: str) -> None:
    payload = {
        "to": to,
        "subject": "You were invited to a team",
        "template": "team_invitation",
        "variables": {
            "team_name": team_name,
            "inviter_name": inviter_name
        }
    }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f'{settings.EMAIL_SERVICE_URL}',
                json=payload,
                headers={'X-Service-Key': settings.INTERNAL_API_KEY}
            )
    except httpx.TransportError:
        raise ServiceUnavaiable()

    response.raise_for_status()