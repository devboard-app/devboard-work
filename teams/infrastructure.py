import httpx
from django.conf import settings


async def get_user_id_by_email(email: str)-> str | None:
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(
            f'{settings.CORE_SERVICE_URL}/api/users/search/',
            params={'email': email},
            headers={'X-Service-Key': settings.INTERNAL_API_KEY}
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json().get('user_id')

async def send_invitation_email(to: str, team_name: str, inviter_name: str) -> None:
    payload = {
        "to": to,
        "subject": "You were invited to a team",
        "template": "team_invitation",
        "variables": {
            "team_name": team_name,
            "inviter_name": inviter_name
        }
    }
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.post(
            f'{settings.EMAIL_SERVICE_URL}',
            json=payload,
            headers={'X-Service-Key': settings.INTERNAL_API_KEY}
        )
        response.raise_for_status()