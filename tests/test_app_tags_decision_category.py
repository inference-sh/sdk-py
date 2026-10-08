"""App catalog tags and decision category (fd249fd typegen).

Apps expose lowercase slug tags on create and in AppDTO; AppTag/AppTagTitle are
the shared vocabulary. AppCategory.DECISION marks probability-out models (no
generation). Guards clients from sending wrong category values or drifting tag
slugs relative to the API contract.
"""

import re
from typing import List, get_type_hints

from inferencesh.types import (
    AppCategory,
    AppDTO,
    AppTag,
    AppTagTitle,
    CreateAppRequest,
)

_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def test_app_category_decision_slug():
    assert AppCategory.DECISION.value == "decision"
    assert AppCategory("decision") is AppCategory.DECISION


def test_app_tag_slugs_are_lowercase_kebab_case():
    assert len(AppTag.__members__) == len(AppTagTitle.__members__)
    assert set(AppTag.__members__) == set(AppTagTitle.__members__)

    for name, tag in AppTag.__members__.items():
        assert _SLUG_RE.match(tag.value), f"{name} slug {tag.value!r} is not kebab-case"
        title = AppTagTitle[name]
        assert title.name == name
        assert title.value.strip() == title.value
        assert title.value[0].isupper()


def test_known_app_tags_match_shared_constants():
    assert AppTag.TEXT_TO_IMAGE.value == "text-to-image"
    assert AppTagTitle.TEXT_TO_IMAGE.value == "Text to Image"
    assert AppTag.LO_RA.value == "lora"
    assert AppTagTitle.LO_RA.value == "LoRA"


def test_create_app_request_accepts_tags_replace_semantics():
    hints = get_type_hints(CreateAppRequest)
    assert hints["tags"] == List[str]
    assert hints["category"] is AppCategory

    body: CreateAppRequest = {
        "namespace": "acme",
        "name": "router",
        "category": AppCategory.DECISION,
        "tags": [AppTag.ROUTING.value, AppTag.REASONING.value, "custom-trait"],
    }
    assert body["category"] is AppCategory.DECISION
    assert body["tags"] == ["routing", "reasoning", "custom-trait"]


def test_app_dto_surfaces_tags_on_read():
    hints = get_type_hints(AppDTO)
    assert hints["tags"] == List[str]
    assert hints["category"] is AppCategory

    app: AppDTO = {
        "namespace": "acme",
        "name": "classifier",
        "category": AppCategory.DECISION,
        "tags": [AppTag.CLASSIFICATION.value, "beta"],
    }
    assert app["tags"][0] == "classification"
