"""Unified ResourceImages with nested dark theme (ac1d673 typegen).

``AppImages`` and ``AgentImages`` collapsed onto ``ResourceImages``. Dark-theme
covers moved from ``ArtifactDTO.images_dark`` into ``images.dark``; clients that
still read a top-level ``images_dark`` field will miss theme-specific assets.
"""

from typing import Optional, get_type_hints

from inferencesh.types import (
    AgentDTO,
    AppDTO,
    ArtifactDTO,
    CreateAgentRequest,
    CreateAppRequest,
    PublicAppStoreDTO,
    ResourceImages,
)

_REMOVED_IMAGE_TYPEDICTS = ("AppImages", "AgentImages")


def test_legacy_app_and_agent_image_types_removed():
    import inferencesh.types as types

    for name in _REMOVED_IMAGE_TYPEDICTS:
        assert not hasattr(types, name), (
            f"{name} was folded into ResourceImages in ac1d673; use ResourceImages"
        )


def test_resource_images_field_contract():
    hints = get_type_hints(ResourceImages)
    assert set(hints) == {"card", "thumbnail", "banner", "dark"}
    assert hints["card"] is str
    assert hints["thumbnail"] is str
    assert hints["banner"] is str
    assert hints["dark"] == Optional[ResourceImages]


def test_listable_resources_use_resource_images_not_legacy_aliases():
    for dto in (
        AppDTO,
        AgentDTO,
        ArtifactDTO,
        CreateAppRequest,
        CreateAgentRequest,
        PublicAppStoreDTO,
    ):
        hints = get_type_hints(dto)
        assert hints["images"] is ResourceImages


def test_artifact_dto_dropped_top_level_images_dark():
    hints = get_type_hints(ArtifactDTO)
    assert "images" in hints
    assert "images_dark" not in hints


def test_theme_specific_covers_live_under_images_dark_slot():
    light: ResourceImages = {
        "card": "https://cdn.example/light-card.png",
        "thumbnail": "https://cdn.example/light-thumb.png",
    }
    dark: ResourceImages = {
        "card": "https://cdn.example/dark-card.png",
        "banner": "https://cdn.example/dark-banner.png",
    }
    row: ArtifactDTO = {
        "namespace": "acme",
        "name": "status-board",
        "title": "Status board",
        "images": {**light, "dark": dark},
    }
    assert row["images"]["card"] == light["card"]
    assert row["images"]["dark"]["card"] == dark["card"]
    assert row["images"]["dark"]["banner"] == dark["banner"]


def test_missing_dark_slot_means_light_images_serve_both_themes():
    app: AppDTO = {
        "namespace": "acme",
        "name": "router",
        "images": {"card": "https://cdn.example/card.png"},
    }
    assert "dark" not in app["images"]
    assert app["images"]["card"] == "https://cdn.example/card.png"

    create: CreateAppRequest = {
        "namespace": "acme",
        "name": "router",
        "images": {"thumbnail": "https://cdn.example/thumb.png"},
    }
    assert create["images"]["thumbnail"].endswith("thumb.png")
