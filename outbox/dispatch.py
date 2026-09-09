import httpx
import redis
from django.conf import settings

from .models import OutboxEvent

STREAM = "devboard:events"

_redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)


def dispatch(channel: str, payload: dict) -> None:
    if channel == OutboxEvent.Channel.REDIS_STREAM:
        _redis_client.xadd(STREAM, payload)
    elif channel == OutboxEvent.Channel.EMAIL:
        response = httpx.post(
            f"{settings.EMAIL_SERVICE_URL}/email/send",
            json=payload,
            headers={"X-Service-Key": settings.INTERNAL_API_KEY},
            timeout=5.0,
        )
        response.raise_for_status()
    else:
        raise ValueError(f"Unknown outbox channel: {channel}")