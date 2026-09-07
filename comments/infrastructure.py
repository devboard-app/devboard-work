import logging

import httpx
from django.conf import settings
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from work.exceptions import ServiceUnavailable

logger = logging.getLogger(__name__)

MAX_BATCH_SIZE = 100
ATTEMPT_TIMEOUT = 2.0

@retry(
    retry=retry_if_exception_type(httpx.TransportError),
    stop=stop_after_attempt(3),
    wait=wait_random_exponential(multiplier=0.1, max=1.0),
    reraise=True
)
async def _attachments_batch(payload: dict) -> list[dict]:
    async with httpx.AsyncClient(timeout=ATTEMPT_TIMEOUT) as client:
        response = await client.post(
            f'{settings.ATTACHMENTS_SERVICE_URL}/internal/attachments/batch',
            json=payload,
            headers={'X-Service-Key': settings.INTERNAL_API_KEY},
        )
    response.raise_for_status()
    return response.json()


async def resolve_attachments(attachment_ids: list[str]) -> dict[str, dict]:
    if not attachment_ids:
        return {}
    try:
        items = await _attachments_batch({'attachment_ids': attachment_ids[:MAX_BATCH_SIZE]})
    except (httpx.TransportError, httpx.HTTPStatusError):
        logger.warning('Could not resolve attachments', exc_info=True)
        return {}
    return {item['id']: item for item in items}

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
        items = await _attachments_batch({
            'attachment_ids': attachment_ids[:MAX_BATCH_SIZE],
            'owner_id': owner_id,
        })
    except (httpx.TransportError, httpx.HTTPStatusError):
        logger.warning('Could not verify attachments', exc_info=True)
        raise ServiceUnavailable()
    return {item['id'] for item in items}
