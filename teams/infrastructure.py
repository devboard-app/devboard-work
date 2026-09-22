import json

import httpx
from django.conf import settings

from work.exceptions import ServiceUnavailable
from work.redis import async_redis_client

USER_STATUS_TTL_SECONDS = 60

async def get_user_id_by_email(email: str) -> str | None:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f'{settings.CORE_SERVICE_URL}/api/users/search/',
                params={'email': email},
                headers={'X-Service-Key': settings.INTERNAL_API_KEY}
            )
        if response.status_code == 404:
            return None
        response.raise_for_status()
    except (httpx.TransportError, httpx.HTTPStatusError):
        raise ServiceUnavailable()

    return response.json().get('user_id')

async def get_user_status(user_id: str) -> str | None:
    cache_key = f"user_status:{user_id}"
    cached = await async_redis_client.get(cache_key)
    if cached is not None:
        return json.loads(cached)
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f'{settings.CORE_SERVICE_URL}/api/users/internal/{user_id}/status/',
                headers={'X-Service-Key': settings.INTERNAL_API_KEY}
            )
        if response.status_code == 404:
            status = None
        else:
            response.raise_for_status()
            status = response.json().get('status')
    except (httpx.TransportError, httpx.HTTPStatusError):
        raise ServiceUnavailable()

    await async_redis_client.setex(cache_key, USER_STATUS_TTL_SECONDS, json.dumps(status))
    return status

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
                f'{settings.EMAIL_SERVICE_URL}/email/send',
                json=payload,
                headers={'X-Service-Key': settings.INTERNAL_API_KEY}
            )
        response.raise_for_status()
    except (httpx.TransportError, httpx.HTTPStatusError):
        raise ServiceUnavailable()