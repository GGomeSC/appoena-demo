from __future__ import annotations

import json
import logging
from typing import Protocol

from shared.tracing import patch_kombu

patch_kombu()

from kombu import Connection, Exchange, Producer, Queue
from kombu.exceptions import KombuError

from shared.events import ItemEvent

logger = logging.getLogger(__name__)


class EventPublisher(Protocol):
    def publish(self, event: ItemEvent) -> None:
        ...


class NullPublisher:
    def publish(self, event: ItemEvent) -> None:
        logger.info("publish_skipped", extra={"event_id": event.event_id, "reason": "disabled"})


class RabbitMQPublisher:
    def __init__(self, url: str, queue_name: str) -> None:
        self._url = url
        self._queue_name = queue_name
        self._exchange = Exchange("", type="direct", durable=True)
        self._queue = Queue(name=queue_name, exchange=self._exchange, routing_key=queue_name, durable=True)

    def publish(self, event: ItemEvent) -> None:
        payload = event.model_dump(mode="json")

        try:
            with Connection(self._url) as connection:
                with Producer(connection) as producer:
                    producer.publish(
                        payload,
                        exchange=self._exchange,
                        routing_key=self._queue_name,
                        declare=[self._queue],
                        serializer="json",
                        delivery_mode=2,
                        headers={
                            "event_id": event.event_id,
                            "event_type": event.event_type,
                            "item_id": event.item_id,
                        },
                    )
        except KombuError:
            logger.exception("publish_failed", extra={"event_id": event.event_id})
            raise

        logger.info(
            "event_published",
            extra={
                "event_id": event.event_id,
                "event_type": event.event_type,
                "item_id": event.item_id,
                "queue_name": self._queue_name,
            },
        )
