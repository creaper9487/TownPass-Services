"""範例 service：目前用記憶體存資料，之後可換成資料庫或外部 API。"""

from app.features.example.schemas import ItemCreate, ItemOut
from app.tools.exceptions import NotFoundError

_items: dict[int, ItemOut] = {}
_next_id = 1


def list_items() -> list[ItemOut]:
    return list(_items.values())


def get_item(item_id: int) -> ItemOut:
    item = _items.get(item_id)
    if item is None:
        raise NotFoundError(f"Item {item_id} not found")
    return item


def create_item(payload: ItemCreate) -> ItemOut:
    global _next_id
    item = ItemOut(id=_next_id, **payload.model_dump())
    _items[item.id] = item
    _next_id += 1
    return item
