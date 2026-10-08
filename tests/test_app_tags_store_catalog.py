"""App catalog tags are dynamic plain strings (771fb31 typegen).

Known tag slugs and titles moved from ``AppTag`` / ``AppTagTitle`` enums to
``GET /store/tags``. The SDK keeps ``List[str]`` on create/read paths so clients
can mix store-listed slugs with custom tags. Guards against reintroducing the
removed enums (which would mislead users away from the store endpoint).
"""

import re
from typing import List, get_type_hints

from inferencesh.types import AppCategory, AppDTO, CreateAppRequest

_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

# Slugs that used to be ``AppTag`` members; still valid on apps as strings.
_FORMER_KNOWN_SLUGS = (
    "text-to-image",
    "open-weights",
    "deep-research",
    "video-enhancement",
    "routing",
    "classification",
)

_REMOVED_TAG_ENUMS = ("AppTag", "AppTagTitle")


def test_app_tag_enums_removed_from_types_module():
    import inferencesh.types as types

    for name in _REMOVED_TAG_ENUMS:
        assert not hasattr(types, name), (
            f"{name} was removed in 771fb31; fetch titles via GET /store/tags"
        )


def test_app_category_decision_unchanged():
    assert AppCategory.DECISION.value == "decision"
    assert AppCategory("decision") is AppCategory.DECISION


def test_create_and_read_paths_use_plain_string_tags():
    hints_create = get_type_hints(CreateAppRequest)
    hints_app = get_type_hints(AppDTO)
    assert hints_create["tags"] == List[str]
    assert hints_app["tags"] == List[str]
    assert hints_create["category"] is AppCategory
    assert hints_app["category"] is AppCategory

    for slug in _FORMER_KNOWN_SLUGS:
        assert _SLUG_RE.match(slug)

    body: CreateAppRequest = {
        "namespace": "acme",
        "name": "router",
        "category": AppCategory.DECISION,
        "tags": list(_FORMER_KNOWN_SLUGS) + ["custom-trait"],
    }
    assert body["category"] is AppCategory.DECISION
    assert body["tags"][-1] == "custom-trait"

    app: AppDTO = {
        "namespace": "acme",
        "name": "classifier",
        "category": AppCategory.DECISION,
        "tags": ["classification", "beta"],
    }
    assert app["tags"][0] == "classification"
