import logging
import time
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from outbox.dispatch import dispatch
from outbox.models import OutboxEvent

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 150 
POLL_INTERVAL_SECONDS = 2
BASE_DELAY_SECONDS = 2
MAX_DELAY_SECONDS = 300
BATCH_SIZE = 100


def backoff_delay(attempts: int) -> int:
    return min(BASE_DELAY_SECONDS * (2 ** attempts), MAX_DELAY_SECONDS)

class Command(BaseCommand):
    help = "Drains pending OutboxEvent rows to their destination channel."

    def handle(self, *args, **options):
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
        logger.info("Outbox relay started.")

        while True:
            now = timezone.now()
            try:
                rows = list(
                    OutboxEvent.objects.filter(delivered_at__isnull=True, attempts__lt=MAX_ATTEMPTS)
                    .filter(Q(next_attempt_at__isnull=True) | Q(next_attempt_at__lte=now))
                    .order_by("created_at")[:BATCH_SIZE]
                )
            except Exception:
                logger.exception("Outbox query failed, will retry next poll")
                time.sleep(POLL_INTERVAL_SECONDS)
                continue

            rows.sort(key=lambda r: r.channel != OutboxEvent.Channel.REDIS_STREAM) # redis_stream rows go first 
            for row in rows:
                try:
                    dispatch(row.channel, row.payload)
                    row.delivered_at = timezone.now()
                    row.save(update_fields=["delivered_at"])
                except Exception:
                    row.attempts += 1
                    if row.attempts >= MAX_ATTEMPTS:
                        logger.warning(f"Outbox delivery permanently failed for {row.id} after {row.attempts} attempts, giving up", exc_info=True)
                        update_fields = ["attempts"]
                    else:
                        delay = backoff_delay(row.attempts)
                        row.next_attempt_at = timezone.now() + timedelta(seconds=delay)
                        logger.warning(f"Outbox delivery failed for {row.id} (attempt {row.attempts}), retrying in {delay}s", exc_info=True)
                        update_fields = ["attempts", "next_attempt_at"]
                    try:
                        row.save(update_fields=update_fields)
                    except Exception:
                        logger.exception(f"Could not persist attempt count for outbox row {row.id}; it will be retried without the increment on the next poll")
            time.sleep(POLL_INTERVAL_SECONDS)