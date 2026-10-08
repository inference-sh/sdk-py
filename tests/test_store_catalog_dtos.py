"""Store catalog list DTOs (254df4b typegen).

``StoreCategoryDTO`` and ``StoreTagDTO`` are the element shapes for store
browse endpoints (categories and tags with usage counts). They replaced ad-hoc
dict parsing when the API started returning structured catalog rows.
"""

import re
from typing import get_type_hints

from inferencesh.types import StoreCategoryDTO, StoreTagDTO

_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def test_store_category_dto_field_contract():
    hints = get_type_hints(StoreCategoryDTO)
    assert set(hints) == {"slug", "name", "description", "icon", "rank", "count"}
    assert all(hint is int for key, hint in hints.items() if key in ("rank", "count"))
    assert all(hint is str for key, hint in hints.items() if key not in ("rank", "count"))


def test_store_tag_dto_field_contract():
    hints = get_type_hints(StoreTagDTO)
    assert set(hints) == {"slug", "title", "count"}
    assert hints["count"] is int
    assert hints["slug"] is str
    assert hints["title"] is str


def test_store_tag_uses_title_not_name():
    """Tags expose human labels as ``title``; categories use ``name``."""
    category_hints = get_type_hints(StoreCategoryDTO)
    tag_hints = get_type_hints(StoreTagDTO)
    assert "name" in category_hints and "title" not in category_hints
    assert "title" in tag_hints and "name" not in tag_hints


def test_partial_rows_are_valid_typed_dicts():
    category: StoreCategoryDTO = {"slug": "models", "name": "Models", "count": 42}
    tag: StoreTagDTO = {"slug": "text-to-image", "title": "Text to image", "count": 7}
    assert category["slug"] == "models"
    assert tag["count"] == 7
    assert _SLUG_RE.match(category["slug"])
    assert _SLUG_RE.match(tag["slug"])
