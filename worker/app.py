from __future__ import annotations

import json
import logging
import os
import signal
import socket
import sys
from dataclasses import dataclass, field
from typing import Any

from shared.tracing import patch_kombu

patch_kombu()

from kombu import Connection, Consumer, Exchange, Queue
from pydantic import ValidationError

from shared.events import ItemEvent
from shared.logging_config import configure_logging

configure_logging()

logger = logging.getLogger(__name__)


@dataclass
class EventProcessor:
    processed_event_ids: set[str] = field(default_factory=set)

    def process(self, body: bytes) -> ItemEvent | None:
        try:
            payload = json.loads(body)
            event = ItemEvent.model_validate(payload)
        except (json.JSONDecodeError, ValidationError):
            logger.exception("event_decode_failed")
            return None

        if event.event_id in self.processed_event_ids:
            logger.info(
                "event_duplicate_skipped",
                extra={"event_id": event.event_id, "item_id": event.item_id},
            )
            return event

        self.processed_event_ids.add(event.event_id)
        logger.info(
            "event_processed",
            extra={
                "event_id": event.event_id,
                "event_type": event.event_type,
                "item_id": event.item_id,
            },
        )
        return event


class Worker:
    def __init__(self, url: str, queue_name: str, processor: EventProcessor | None = None) -> None:
        self._url = url
        self._queue_name = queue_name
        self._processor = processor or EventProcessor()
        self._connection: Connection | None = None
        self._should_stop = False
        self._exchange = Exchange("", type="direct", durable=True)
        self._queue = Queue(name=queue_name, exchange=self._exchange, routing_key=queue_name, durable=True)

    def stop(self, *_: Any) -> None:
        logger.info("worker_stopping")
        self._should_stop = True
        if self._connection is not None:
            try:
                self._connection.close()
            except Exception:
                logger.exception("worker_connection_close_failed")

    def start(self) -> None:
        try:
            self._connection = Connection(self._url)
            self._connection.connect()
            queue = self._queue(self._connection)
            queue.declare()

            with Consumer(
                self._connection,
                queues=[queue],
                callbacks=[self._on_message],
                accept=["json"],
                prefetch_count=1,
            ):
                logger.info("worker_started", extra={"queue_name": self._queue_name})
                while not self._should_stop:
                    try:
                        self._connection.drain_events(timeout=1)
                    except socket.timeout:
                        continue
        finally:
            if self._connection is not None:
                try:
                    self._connection.release()
                except Exception:
                    logger.exception("worker_connection_release_failed")

    def _on_message(self, body: dict[str, Any], message: Any) -> None:
        event = self._processor.process(json.dumps(body).encode("utf-8"))
        message.ack()
        if event is None:
            return


def main() -> int:
    rabbitmq_url = os.getenv("RABBITMQ_URL")
    if not rabbitmq_url:
        logger.error("missing_rabbitmq_url")
        return 1

    queue_name = os.getenv("RABBITMQ_QUEUE", "items.events")
    worker = Worker(rabbitmq_url, queue_name)
    signal.signal(signal.SIGTERM, worker.stop)
    signal.signal(signal.SIGINT, worker.stop)

    try:
        worker.start()
    except Exception:
        logger.exception("worker_failed")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
