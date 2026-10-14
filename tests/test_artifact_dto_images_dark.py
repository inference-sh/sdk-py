"""ArtifactDTO.images_dark (717aebf typegen).

Dark-theme gallery covers are optional: when absent or empty, ``images``
serves both themes. When set, clients must not fall back to light assets for
dark UI or theme-specific captures will be wrong.
"""

from typing import get_type_hints

from inferencesh.types import ArtifactDTO, ResourceImages


def test_artifact_dto_declares_images_and_images_dark():
    hints = get_type_hints(ArtifactDTO)
    assert "images" in hints
    assert "images_dark" in hints
    assert hints["images"] is ResourceImages
    assert hints["images_dark"] is ResourceImages


def test_artifact_row_carries_theme_specific_covers():
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
        "images": light,
        "images_dark": dark,
    }
    assert row["images"]["card"] == light["card"]
    assert row["images_dark"]["card"] == dark["card"]
    assert row["images_dark"]["banner"] == dark["banner"]


def test_artifact_without_images_dark_uses_light_covers_only():
    """Missing images_dark: API contract is that images serve both themes."""
    row: ArtifactDTO = {
        "namespace": "acme",
        "name": "notes",
        "images": {"card": "https://cdn.example/card.png"},
    }
    assert "images_dark" not in row
    assert row["images"]["card"] == "https://cdn.example/card.png"
