from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from shared.events import ItemSnapshot


ItemStatus = Literal["PENDENTE", "feito"]


class ItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    status: ItemStatus = "PENDENTE"


class ItemUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    status: ItemStatus


class Item(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    status: ItemStatus
    created_at: datetime
    updated_at: datetime

    @classmethod
    def new(cls, item_id: str, data: ItemCreate) -> "Item":
        now = datetime.now(timezone.utc)
        return cls(
            id=item_id,
            name=data.name,
            description=data.description,
            status=data.status,
            created_at=now,
            updated_at=now,
        )

    def update_from(self, data: ItemUpdate) -> "Item":
        return self.model_copy(
            update={
                "name": data.name,
                "description": data.description,
                "status": data.status,
                "updated_at": datetime.now(timezone.utc),
            }
        )

    def to_snapshot(self) -> ItemSnapshot:
        return ItemSnapshot.model_validate(self.model_dump())
