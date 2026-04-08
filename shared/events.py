from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict


EventType = Literal["item.created", "item.updated", "item.deleted"]


class ItemSnapshot(BaseModel):
    id: str
    name: str
    description: str | None
    status: Literal["PENDENTE", "feito"]
    created_at: datetime
    updated_at: datetime


class ItemEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str
    event_type: EventType
    item_id: str
    timestamp: datetime
    item_snapshot: ItemSnapshot | None = None

    @classmethod
    def build(
        cls,
        *,
        event_type: EventType,
        item_id: str,
        item_snapshot: ItemSnapshot | None,
    ) -> "ItemEvent":
        return cls(
            event_id=str(uuid4()),
            event_type=event_type,
            item_id=item_id,
            timestamp=datetime.now(timezone.utc),
            item_snapshot=item_snapshot,
        )
