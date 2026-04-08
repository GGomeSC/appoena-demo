from __future__ import annotations

from collections.abc import Iterable

from api.app.models import Item, ItemCreate, ItemUpdate


class ItemRepository:
    def __init__(self) -> None:
        self._items: dict[str, Item] = {}
        self._next_id = 1

    def list_items(self) -> Iterable[Item]:
        return self._items.values()

    def get(self, item_id: str) -> Item | None:
        return self._items.get(item_id)

    def create(self, payload: ItemCreate) -> Item:
        item = Item.new(str(self._next_id), payload)
        self._items[item.id] = item
        self._next_id += 1
        return item

    def update(self, item_id: str, payload: ItemUpdate) -> Item | None:
        item = self.get(item_id)
        if item is None:
            return None

        updated = item.update_from(payload)
        self._items[item_id] = updated
        return updated

    def delete(self, item_id: str) -> Item | None:
        return self._items.pop(item_id, None)
