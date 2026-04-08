from __future__ import annotations

import json
import logging
import os
import sys
from datetime import UTC, datetime
from types import TracebackType
from typing import Any


QUIET_LOGGERS = {
    "ddtrace": logging.WARNING,
    "ddtrace.internal": logging.WARNING,
    "ddtrace.vendor.dogstatsd": logging.WARNING,
    "amqp": logging.WARNING,
    "httpcore": logging.WARNING,
    "httpx": logging.WARNING,
    "kombu": logging.WARNING,
}

STANDARD_LOG_RECORD_FIELDS = set(logging.makeLogRecord({}).__dict__) | {"message", "asctime"}
LOGGER_EXCEPTION_NAME = "app.uncaught_exception"


class DatadogJSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self._format_timestamp(record.created),
            "level": record.levelname,
            "message": record.getMessage(),
        }

        for key, value in record.__dict__.items():
            if key in STANDARD_LOG_RECORD_FIELDS or key.startswith("_"):
                continue
            if key in payload:
                continue
            payload[key] = value

        if record.exc_info:
            payload["stack"] = self.formatException(record.exc_info)
        elif record.exc_text:
            payload["stack"] = record.exc_text

        return json.dumps(payload, ensure_ascii=False, default=self._coerce_value)

    def _format_timestamp(self, created: float) -> str:
        return datetime.fromtimestamp(created, tz=UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")

    def _coerce_value(self, value: Any) -> Any:
        if isinstance(value, (set, tuple)):
            return list(value)
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        return str(value)


def build_stream_handler() -> logging.Handler:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(DatadogJSONFormatter())
    return handler


def log_uncaught_exception(
    exc_type: type[BaseException],
    exc_value: BaseException,
    exc_traceback: TracebackType | None,
) -> None:
    if issubclass(exc_type, (KeyboardInterrupt, SystemExit)):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logging.getLogger(LOGGER_EXCEPTION_NAME).error(
        "uncaught_exception",
        exc_info=(exc_type, exc_value, exc_traceback),
    )


def configure_logging() -> None:
    level_name = os.getenv("LOG_LEVEL", "WARNING").upper()
    level = getattr(logging, level_name, logging.INFO)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(build_stream_handler())
    root.setLevel(level)

    for logger_name, logger_level in QUIET_LOGGERS.items():
        logging.getLogger(logger_name).setLevel(logger_level)

    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access", "ddtrace", "ddtrace.internal", "ddtrace.vendor.dogstatsd"):
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.propagate = True
        logger.setLevel(level)

    sys.excepthook = log_uncaught_exception
