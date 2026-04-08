from __future__ import annotations

import json
import logging
import sys

from shared.logging_config import DatadogJSONFormatter, configure_logging


def test_formatter_preserves_extra_and_datadog_fields() -> None:
    formatter = DatadogJSONFormatter()
    logger = logging.getLogger("tests.logging")
    record = logger.makeRecord(
        name=logger.name,
        level=logging.INFO,
        fn=__file__,
        lno=11,
        msg="structured_info",
        args=(),
        exc_info=None,
        extra={
            "item_id": "123",
            "dd.trace_id": "456",
            "dd.span_id": "789",
            "dd.env": "test",
            "dd.service": "demo-api",
            "dd.version": "1.0.0",
        },
    )

    payload = json.loads(formatter.format(record))

    assert payload["level"] == "INFO"
    assert payload["message"] == "structured_info"
    assert payload["item_id"] == "123"
    assert payload["dd.trace_id"] == "456"
    assert payload["dd.span_id"] == "789"
    assert payload["dd.env"] == "test"
    assert payload["dd.service"] == "demo-api"
    assert payload["dd.version"] == "1.0.0"


def test_formatter_emits_stack_only_for_exceptions() -> None:
    formatter = DatadogJSONFormatter()
    logger = logging.getLogger("tests.logging")

    try:
        raise RuntimeError("boom")
    except RuntimeError:
        record = logger.makeRecord(
            name=logger.name,
            level=logging.ERROR,
            fn=__file__,
            lno=17,
            msg="structured_failure",
            args=(),
            exc_info=sys.exc_info(),
            extra={"item_id": "123"},
        )

    payload = json.loads(formatter.format(record))

    assert payload["message"] == "structured_failure"
    assert payload["level"] == "ERROR"
    assert payload["item_id"] == "123"
    assert {"timestamp", "level", "message", "stack", "item_id"} <= set(payload)
    assert "RuntimeError: boom" in payload["stack"]
    assert "Traceback" in payload["stack"]


def test_configure_logging_reuses_root_handler_for_uvicorn() -> None:
    configure_logging()

    root = logging.getLogger()
    uvicorn_error = logging.getLogger("uvicorn.error")
    uvicorn_access = logging.getLogger("uvicorn.access")
    ddtrace_vendor = logging.getLogger("ddtrace.vendor.dogstatsd")

    assert len(root.handlers) == 1
    assert isinstance(root.handlers[0].formatter, DatadogJSONFormatter)
    assert uvicorn_error.propagate is True
    assert uvicorn_access.propagate is True
    assert ddtrace_vendor.propagate is True
    assert uvicorn_error.handlers == []
    assert uvicorn_access.handlers == []
    assert ddtrace_vendor.handlers == []


def test_uncaught_exception_hook_emits_json(capsys) -> None:
    configure_logging()

    try:
        raise RuntimeError("uncaught boom")
    except RuntimeError as exc:
        sys.excepthook(type(exc), exc, exc.__traceback__)

    captured = capsys.readouterr()
    payload = json.loads(captured.out.strip())

    assert payload["message"] == "uncaught_exception"
    assert payload["level"] == "ERROR"
    assert "RuntimeError: uncaught boom" in payload["stack"]
