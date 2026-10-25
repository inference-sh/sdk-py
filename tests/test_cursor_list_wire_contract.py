"""Cursor list request/response wire contract (55ae6dd / api 473d9639b).

Cursor-based list endpoints use ``CursorListRequest`` / ``CursorListResponse``.
They are cursor-only: offset ``page`` and aggregate ``total_items`` belong on
other shapes (e.g. ``CountResponse``), not on these TypedDicts.
"""

from typing import Any, List, get_type_hints

from inferencesh.types import CountResponse, CursorListRequest, CursorListResponse


def test_cursor_list_request_exposes_cursor_pagination_fields():
    hints = get_type_hints(CursorListRequest)
    assert set(hints) == {
        "cursor",
        "limit",
        "direction",
        "search",
        "filters",
        "preloads",
        "sort",
        "fields",
        "permissions",
        "include_others",
        "include_private",
    }
    assert "page" not in hints


def test_cursor_list_response_exposes_cursor_metadata_not_totals():
    hints = get_type_hints(CursorListResponse)
    assert set(hints) == {
        "items",
        "next_cursor",
        "prev_cursor",
        "has_next",
        "has_previous",
        "items_per_page",
    }
    assert "total_items" not in hints


def test_cursor_list_request_serializes_without_page():
    req: CursorListRequest = {
        "cursor": "abc",
        "limit": 25,
        "direction": "next",
        "include_private": True,
    }
    assert req["cursor"] == "abc"
    assert "page" not in req


def test_cursor_list_response_accepts_cursor_page_without_total():
    page: CursorListResponse = {
        "items": [{"id": "sock-1"}],
        "next_cursor": "n1",
        "prev_cursor": "",
        "has_next": True,
        "has_previous": False,
        "items_per_page": 1,
    }
    items: List[Any] = page["items"]
    assert items[0]["id"] == "sock-1"
    assert page["has_next"] is True
    assert "total_items" not in page


def test_total_count_uses_count_response_not_list_envelope():
    """List pages carry cursors; total row counts use the count endpoint shape."""
    total: CountResponse = {"count": 128}
    assert total["count"] == 128
    assert "total_items" not in get_type_hints(CursorListResponse)
