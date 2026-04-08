from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Response, status

from api.app.models import Item, ItemCreate, ItemUpdate
from api.app.publisher import EventPublisher, NullPublisher, RabbitMQPublisher
from api.app.repository import ItemRepository
from shared.events import ItemEvent
from shared.logging_config import configure_logging

configure_logging()

logger = logging.getLogger(__name__)


def build_publisher() -> EventPublisher:
    rabbitmq_url = os.getenv("RABBITMQ_URL")
    queue_name = os.getenv("RABBITMQ_QUEUE", "items.events")
    if not rabbitmq_url:
        return NullPublisher()
    return RabbitMQPublisher(rabbitmq_url, queue_name)


def create_app(
    *,
    repository: ItemRepository | None = None,
    publisher: EventPublisher | None = None,
) -> FastAPI:
    repo = repository or ItemRepository()
    event_publisher = publisher or build_publisher()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        logger.info("api_started")
        yield
        logger.info("api_stopped")

    app = FastAPI(title="CRUD Observability Demo", lifespan=lifespan)
    app.state.repository = repo
    app.state.publisher = event_publisher

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/items", response_model=list[Item])
    def list_items() -> list[Item]:
        return list(app.state.repository.list_items())

    @app.get("/api/items/{item_id}", response_model=Item)
    def get_item(item_id: str) -> Item:
        item = app.state.repository.get(item_id)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
        return item

    @app.post("/api/items", response_model=Item, status_code=status.HTTP_201_CREATED)
    def create_item(payload: ItemCreate) -> Item:
        item = app.state.repository.create(payload)
        event = ItemEvent.build(
            event_type="item.created",
            item_id=item.id,
            item_snapshot=item.to_snapshot(),
        )
        app.state.publisher.publish(event)
        logger.info("item_created", extra={"item_id": item.id})
        return item

    @app.put("/api/items/{item_id}", response_model=Item)
    def update_item(item_id: str, payload: ItemUpdate) -> Item:
        item = app.state.repository.update(item_id, payload)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
        event = ItemEvent.build(
            event_type="item.updated",
            item_id=item.id,
            item_snapshot=item.to_snapshot(),
        )
        app.state.publisher.publish(event)
        logger.info("item_updated", extra={"item_id": item.id})
        return item

    @app.delete("/api/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_item(item_id: str) -> Response:
        item = app.state.repository.delete(item_id)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
        event = ItemEvent.build(
            event_type="item.deleted",
            item_id=item.id,
            item_snapshot=None,
        )
        app.state.publisher.publish(event)
        logger.info("item_deleted", extra={"item_id": item.id})
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return app


app = create_app()
