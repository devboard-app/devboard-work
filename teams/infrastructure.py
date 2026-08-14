import httpx
from django.conf import settings


async def get_user_id_by_email(email: str)-> str | None:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f'{settings.CORE_SERVICE_URL}/api/users/search/',
            params={'email': email},
            headers={'X-Service-Key': settings.INTERNAL_API_KEY}
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json().get('user_id')