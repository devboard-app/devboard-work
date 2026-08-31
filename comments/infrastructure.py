import logging

import httpx
from django.conf import settings

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