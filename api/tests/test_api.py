from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from api.app.main import create_app
from api.app.publisher import EventPublisher
from api.app.repository import ItemRepository
from shared.events import ItemEvent


class FakePublisher(EventPublisher):
    def __init__(self) -> None:
        self.events: list[ItemEvent] = []

    def publish(self, event: ItemEvent) -> None:
        self.events.append(event)


@pytest.fixture
def publisher() -> FakePublisher:
    return FakePublisher()


@pytest.fixture
def client(publisher: FakePublisher) -> Iterator[TestClient]:
    app = create_app(repository=ItemRepository(), publisher=publisher)
    with TestClient(app) as test_client:
        yield test_client


def test_create_item_publishes_event(client: TestClient, publisher: FakePublisher) -> None:
    response = client.post(
        "/api/items",
        json={"name": "Write docs", "description": "Datadog demo", "status": "PENDENTE"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["id"] == "1"
    assert payload["name"] == "Write docs"
    assert len(publisher.events) == 1
    assert publisher.events[0].event_type == "item.created"
    assert publisher.events[0].item_snapshot is not None


def test_list_and_get_item(client: TestClient) -> None:
    created = client.post("/api/items", json={"name": "List me", "status": "PENDENTE"}).json()

    listing = client.get("/api/items")
    fetched = client.get(f"/api/items/{created['id']}")

    assert listing.status_code == 200
    assert len(listing.json()) == 1
    assert fetched.status_code == 200
    assert fetched.json()["id"] == created["id"]


def test_update_item_publishes_event(client: TestClient, publisher: FakePublisher) -> None:
    created = client.post("/api/items", json={"name": "Original", "status": "PENDENTE"}).json()

    response = client.put(
        f"/api/items/{created['id']}",
        json={"name": "Updated", "description": "Done", "status": "feito"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "feito"
    assert publisher.events[-1].event_type == "item.updated"
    assert publisher.events[-1].item_id == created["id"]


def test_delete_item_publishes_event(client: TestClient, publisher: FakePublisher) -> None:
    created = client.post("/api/items", json={"name": "Delete me", "status": "PENDENTE"}).json()

    response = client.delete(f"/api/items/{created['id']}")

    assert response.status_code == 204
    assert publisher.events[-1].event_type == "item.deleted"
    assert publisher.events[-1].item_snapshot is None


def test_missing_item_returns_404(client: TestClient) -> None:
    response = client.get("/api/items/missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "Item not found"


def test_invalid_payload_returns_422(client: TestClient) -> None:
    response = client.post("/api/items", json={"name": "", "status": "invalid"})

    assert response.status_code == 422
