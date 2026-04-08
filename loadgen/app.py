from __future__ import annotations

import logging
import os
import random
import string
import time

import httpx

from shared.logging_config import configure_logging

configure_logging()

logger = logging.getLogger(__name__)


def random_name() -> str:
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"load-{suffix}"


def build_payload(done: bool = False) -> dict[str, str | None]:
    return {
        "name": random_name(),
        "description": "generated automatically for Datadog tracing live tail",
        "status": "feito" if done else "PENDENTE",
    }


def main() -> int:
    base_url = os.getenv("LOADGEN_BASE_URL", "http://apache")
    interval_seconds = float(os.getenv("LOADGEN_INTERVAL_SECONDS", "2"))
    timeout_seconds = float(os.getenv("LOADGEN_TIMEOUT_SECONDS", "10"))

    logger.info(
        "loadgen_started",
        extra={
            "base_url": base_url,
            "interval_seconds": interval_seconds,
            "timeout_seconds": timeout_seconds,
        },
    )

    with httpx.Client(base_url=base_url, timeout=timeout_seconds) as client:
        while True:
            try:
                health = client.get("/health")
                health.raise_for_status()

                created = client.post("/api/items", json=build_payload())
                created.raise_for_status()
                item = created.json()
                item_id = item["id"]

                listing = client.get("/api/items")
                listing.raise_for_status()

                fetched = client.get(f"/api/items/{item_id}")
                fetched.raise_for_status()

                updated = client.put(
                    f"/api/items/{item_id}",
                    json={
                        "name": item["name"],
                        "description": "updated by automatic load generator",
                        "status": "feito",
                    },
                )
                updated.raise_for_status()

                deleted = client.delete(f"/api/items/{item_id}")
                deleted.raise_for_status()

                logger.info("loadgen_cycle_completed", extra={"item_id": item_id})
            except httpx.HTTPError:
                logger.exception("loadgen_cycle_failed")

            time.sleep(interval_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
