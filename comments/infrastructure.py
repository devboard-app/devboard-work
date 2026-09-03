import logging

import httpx
from django.conf import settings

from work.exceptions import ServiceUnavailable

logger = logging.getLogger(__name__)

MAX_BATCH_SIZE = 100


async def resolve_attachments(attachment_ids: list[str]) -> dict[str, dict]:
    if not attachment_ids:
        return {}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f'{settings.ATTACHMENTS_SERVICE_URL}/internal/attachments/batch',
                json={'attachment_ids': attachment_ids[:MAX_BATCH_SIZE]},
                headers={'X-Service-Key': settings.INTERNAL_API_KEY},
            )
        response.raise_for_status()
    except (httpx.TransportError, httpx.HTTPStatusError):
        logger.warning('Could not resolve attachments', exc_info=True)
        return {}
    return {item['id']: item for item in response.json()}

async def resolve_usernames(usernames: list[str]) -> dict[str, str]:
    if not usernames:
        return {}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f'{settings.CORE_SERVICE_URL}/api/users/lookup/',
                json={'usernames': usernames},
                headers={'X-Service-Key': settings.INTERNAL_API_KEY},
            )
        response.raise_for_status()
    except (httpx.TransportError, httpx.HTTPStatusError):
        logger.warning('Could not resolve mentions', exc_info=True)
        return {}
    return {item['username']: item['user_id'] for item in response.json()}

async def verify_attachments(attachment_ids: list[str], owner_id: str) -> set[str]:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f'{settings.ATTACHMENTS_SERVICE_URL}/internal/attachments/batch',
                json={'attachment_ids': attachment_ids, 'owner_id': owner_id},
                headers={'X-Service-Key': settings.INTERNAL_API_KEY},
            )
        response.raise_for_status()
    except (httpx.TransportError, httpx.HTTPStatusError):
        logger.warning('Could not verify attachments', exc_info=True)
        raise ServiceUnavailable()
    return {item['id'] for item in response.json()}