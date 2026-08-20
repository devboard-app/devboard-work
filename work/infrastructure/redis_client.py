import redis.asyncio as aioredis
from django.conf import settings

redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)