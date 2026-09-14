import logging
import time

from django.core.management.base import BaseCommand
from django.utils import timezone

from outbox.dispatch import dispatch
from outbox.models import OutboxEvent

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 5
POLL_INTERVAL_SECONDS = 2
BATCH_SIZE = 100


class Command(BaseCommand):
    help = "Drains pending OutboxEvent rows to their destination channel."

    def handle(self, *args, **options):
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
        logger.info("Outbox relay started.")

        while True:
            try:
                rows = list(
                    OutboxEvent.objects.filter(delivered_at__isnull=True, attempts__lt=MAX_ATTEMPTS)
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
                    else:
                        logger.warning(f"Outbox delivery failed for {row.id} (attempt {row.attempts}), retrying", exc_info=True)
                    try:
                        row.save(update_fields=["attempts"])
                    except Exception:
                        logger.exception(f"Could not persist attempt count for outbox row {row.id}; it will be retried without the increment on the next poll")
            time.sleep(POLL_INTERVAL_SECONDS)