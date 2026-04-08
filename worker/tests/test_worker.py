from __future__ import annotations

import json
import logging

from shared.events import ItemEvent, ItemSnapshot
from worker import app as worker_app
from worker.app import EventProcessor, Worker


def build_payload(event_id: str = "evt-1") -> bytes:
    event = ItemEvent(
        event_id=event_id,
        event_type="item.created",
        item_id="item-1",
        timestamp="2026-04-07T00:00:00Z",
        item_snapshot=ItemSnapshot(
            id="item-1",
            name="Task",
            description="Desc",
            status="PENDENTE",
            created_at="2026-04-07T00:00:00Z",
            updated_at="2026-04-07T00:00:00Z",
        ),
    )
    return json.dumps(event.model_dump(mode="json")).encode("utf-8")


def test_processor_accepts_valid_event() -> None:
    processor = EventProcessor()

    event = processor.process(build_payload())

    assert event is not None
    assert event.event_id == "evt-1"
    assert "evt-1" in processor.processed_event_ids


def test_processor_is_idempotent_for_duplicate_event() -> None:
    processor = EventProcessor()
    payload = build_payload("evt-dup")

    first = processor.process(payload)
    second = processor.process(payload)

    assert first is not None
    assert second is not None
    assert len(processor.processed_event_ids) == 1


def test_processor_rejects_invalid_payload() -> None:
    processor = EventProcessor()

    event = processor.process(b'{"bad": true}')

    assert event is None


def test_main_logs_unexpected_worker_exception(monkeypatch, caplog) -> None:
    monkeypatch.setenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/%2F")

    def fail_start(self) -> None:
        raise OSError("bad file descriptor")

    monkeypatch.setattr(Worker, "start", fail_start)

    with caplog.at_level(logging.ERROR):
        exit_code = worker_app.main()

    assert exit_code == 1
    assert any(record.message == "worker_failed" for record in caplog.records)
    assert any(record.exc_info and "bad file descriptor" in str(record.exc_info[1]) for record in caplog.records)


def test_stop_logs_close_failures_instead_of_raising(caplog) -> None:
    class BrokenConnection:
        def close(self) -> None:
            raise OSError("close exploded")

    worker = Worker("amqp://guest:guest@rabbitmq:5672/%2F", "items.events")
    worker._connection = BrokenConnection()

    with caplog.at_level(logging.ERROR):
        worker.stop()

    assert worker._should_stop is True
    assert any(record.message == "worker_connection_close_failed" for record in caplog.records)


def test_start_logs_release_failures_instead_of_raising(monkeypatch, caplog) -> None:
    class BrokenConnection:
        def connect(self) -> None:
            return None

        def release(self) -> None:
            raise OSError("release exploded")

    class FakeBoundQueue:
        def declare(self) -> None:
            return None

    class FakeConsumer:
        def __init__(self, *_args, **_kwargs) -> None:
            return None

        def __enter__(self) -> "FakeConsumer":
            return self

        def __exit__(self, *_args) -> None:
            return None

    worker = Worker("amqp://guest:guest@rabbitmq:5672/%2F", "items.events")

    monkeypatch.setattr(worker, "_queue", lambda _connection: FakeBoundQueue())
    monkeypatch.setattr(worker_app, "Consumer", FakeConsumer)

    def stop_after_first_drain(*, timeout: int) -> None:
        assert timeout == 1
        worker._should_stop = True

    broken_connection = BrokenConnection()
    broken_connection.drain_events = stop_after_first_drain
    monkeypatch.setattr(worker_app, "Connection", lambda _url: broken_connection)

    with caplog.at_level(logging.ERROR):
        worker.start()

    assert any(record.message == "worker_connection_release_failed" for record in caplog.records)
