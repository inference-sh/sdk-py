"""AppDTO.resolved_function pins the function named by a ref lookup (2263be6 typegen).

Only present on get-by-ref responses: ``ns/app:fn`` in the ref, or a route that
maps a retired name to a function on another app. Empty means the client chooses,
starting from the version's ``default_function``.
"""

from typing import get_type_hints

from inferencesh.types import AppCategory, AppDTO, AppStatus, AppVersionDTO


def test_app_dto_declares_resolved_function_as_str():
    hints = get_type_hints(AppDTO)
    assert "resolved_function" in hints
    assert hints["resolved_function"] is str


def test_app_version_dto_does_not_duplicate_resolved_function():
    """Resolved function is lookup metadata on AppDTO, not on AppVersionDTO."""
    assert "resolved_function" not in get_type_hints(AppVersionDTO)
    assert "default_function" in get_type_hints(AppVersionDTO)


def test_ref_lookup_payloads_carry_resolved_function_or_empty_default():
    pinned: AppDTO = {
        "namespace": "acme",
        "name": "dialogue-v2",
        "status": AppStatus.ACTIVE,
        "category": AppCategory.CHAT,
        "resolved_function": "dialogue",
        "version": {"default_function": "chat", "functions": {}},
    }
    unpinned: AppDTO = {
        "namespace": "acme",
        "name": "seedance",
        "status": AppStatus.ACTIVE,
        "category": AppCategory.VIDEO,
        "resolved_function": "",
        "version": {"default_function": "generate", "functions": {}},
    }
    assert pinned["resolved_function"] == "dialogue"
    assert unpinned["resolved_function"] == ""
    assert pinned["version"]["default_function"] == "chat"
    assert unpinned["version"]["default_function"] == "generate"
