"""ArtifactDTO.access and Permission.interact (4fb2a23 typegen).

Single-read artifact responses expose the caller's effective access level
(read, interact, or write). ``cover_version_id`` pins which version a
captured cover shows; empty means manual cover and capture must not replace it.
"""

from typing import get_type_hints

from inferencesh.types import ArtifactDTO, Permission


def test_permission_interact_wire_value():
    assert Permission.PERM_INTERACT == "interact"
    assert Permission.PERM_INTERACT.value == "interact"


def test_permission_enum_includes_interact_between_write_and_use():
    values = [p.value for p in Permission]
    assert values == ["read", "write", "interact", "use"]


def test_artifact_dto_declares_cover_version_id_and_access():
    hints = get_type_hints(ArtifactDTO)
    assert "cover_version_id" in hints
    assert hints["cover_version_id"] is str
    assert "access" in hints
    assert hints["access"] is Permission


def test_single_read_artifact_row_carries_access_and_cover_pin():
    row: ArtifactDTO = {
        "namespace": "acme",
        "name": "dashboard",
        "title": "Team dashboard",
        "url": "https://inference.sh/acme/dashboard",
        "shared_version_id": "ver_live",
        "cover_version_id": "ver_cover",
        "access": Permission.PERM_INTERACT,
        "views": 12,
    }
    assert row["access"] == Permission.PERM_INTERACT
    assert row["access"].value == "interact"
    assert row["cover_version_id"] == "ver_cover"


def test_manual_cover_uses_empty_cover_version_id():
    """Empty cover_version_id: capture must not overwrite a person-set cover."""
    row: ArtifactDTO = {
        "namespace": "acme",
        "name": "notes",
        "cover_version_id": "",
        "access": Permission.PERM_READ,
    }
    assert row["cover_version_id"] == ""
    assert row["access"] == Permission.PERM_READ
