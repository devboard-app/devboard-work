import redis
import redis.asyncio as redis_async
from django.conf import settings

redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
async_redis_client = redis_async.Redis.from_url(settings.REDIS_URL, decode_responses=True)