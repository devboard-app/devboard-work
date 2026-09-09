from asgiref.sync import sync_to_async
from django.db import transaction

from .models import OutboxEvent


def write_with_outbox(domain_write_fn, events: list[tuple[str, dict]]):
    with transaction.atomic():
        result = domain_write_fn()
        for channel, payload in events:
            OutboxEvent.objects.create(channel=channel, payload=payload)
    return result


async def awrite_with_outbox(domain_write_fn, events: list[tuple[str, dict]]):
    return await sync_to_async(write_with_outbox, thread_sensitive=True)(domain_write_fn, events)
