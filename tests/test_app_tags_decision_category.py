"""App catalog tags and decision category (e43aea2 / fd249fd typegen).

Apps expose lowercase slug tags on create and in AppDTO; AppTag/AppTagTitle are
the shared vocabulary for tags that meet the public-app threshold. AppCategory.DECISION
marks probability-out models (no generation). Guards clients from drifting tag
slugs or reintroducing dropped enum members after catalog pruning.
"""

import re
from typing import List, get_type_hints

import pytest

from inferencesh.types import (
    AppCategory,
    AppDTO,
    AppTag,
    AppTagTitle,
    CreateAppRequest,
)

_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

# Tags removed from the known catalog in e43aea2 (still valid plain strings on apps).
_DROPPED_KNOWN_TAG_MEMBERS = frozenset(
    {
        "VIRTUAL_TRY_ON",
        "FACE_SWAP",
        "VIDEO_CAPTIONS",
        "SPEECH_TO_SPEECH",
        "VIDEO_TO_AUDIO",
        "DUBBING",
        "TEXT_TO3D",
        "IMAGE_TO3D",
        "OCR",
        "EMBEDDINGS",
    }
)

# Slugs added when the known list was trimmed to high-traffic tags (e43aea2).
_ADDED_KNOWN_TAG_SLUGS = frozenset(
    {
        "video-enhancement",
        "deep-research",
        "research-papers",
        "social-media",
        "messaging",
        "productivity",
        "media-utilities",
        "rendering",
        "evaluation",
    }
)


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


def test_known_app_tag_catalog_size_and_new_slugs():
    assert len(AppTag) == 42
    catalog_slugs = {tag.value for tag in AppTag}
    assert _ADDED_KNOWN_TAG_SLUGS <= catalog_slugs


def test_dropped_tags_are_not_enum_members_but_plain_strings_still_work():
    for name in _DROPPED_KNOWN_TAG_MEMBERS:
        assert name not in AppTag.__members__

    body: CreateAppRequest = {
        "namespace": "acme",
        "name": "legacy",
        "category": AppCategory.IMAGE,
        "tags": ["virtual-try-on", "ocr"],
    }
    assert "virtual-try-on" in body["tags"]


def test_known_app_tags_match_shared_constants():
    assert AppTag.TEXT_TO_IMAGE.value == "text-to-image"
    assert AppTagTitle.TEXT_TO_IMAGE.value == "Text to Image"
    assert AppTag.LO_RA.value == "lora"
    assert AppTagTitle.LO_RA.value == "LoRA"
    assert AppTag.DEEP_RESEARCH.value == "deep-research"
    assert AppTagTitle.MEDIA_UTILITIES.value == "Media Utilities"


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


@pytest.mark.parametrize(
    "member,slug,title",
    [
        (AppTag.VIDEO_ENHANCEMENT, "video-enhancement", "Video Enhancement"),
        (AppTag.EVALUATION, "evaluation", "Evaluation"),
    ],
)
def test_new_catalog_entries_pair_slug_and_title(member, slug, title):
    assert member.value == slug
    assert AppTagTitle[member.name].value == title
