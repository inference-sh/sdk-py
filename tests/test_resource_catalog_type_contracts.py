"""Resource images, vault secrets, and artifact access (typegen 4fb2a23–f969c81).

``ResourceImages.dark`` nests the same slots for dark-theme UIs; apps, agents,
and artifacts all share that shape after AppImages/AgentImages were folded in.
``CredentialConfigDTO.multi_account`` and ``accounts`` model several logins per
provider. ``SecretDTO`` denormalizes credential metadata for list rows.
``ArtifactDTO.access`` exposes the viewer's ``Permission`` (including interact).
"""

import json
from typing import List, Optional, get_type_hints

from inferencesh.types import (
    AgentDTO,
    AppDTO,
    ArtifactDTO,
    CredentialConfigDTO,
    CredentialDTO,
    Permission,
    ResourceImages,
    SecretCreateRequest,
    SecretDTO,
    SecretProviderRequest,
)


def test_resource_images_supports_nested_dark_theme_slots():
    hints = get_type_hints(ResourceImages)
    assert set(hints) >= {"card", "thumbnail", "banner", "dark"}
    assert hints["dark"] == ResourceImages | None

    images: ResourceImages = {
        "card": "https://cdn.example/light-card.png",
        "dark": {
            "card": "https://cdn.example/dark-card.png",
            "thumbnail": "https://cdn.example/dark-thumb.png",
        },
    }
    assert images["dark"]["card"].endswith("dark-card.png")


def test_listable_resources_use_resource_images_not_legacy_types():
    for dto in (AppDTO, AgentDTO, ArtifactDTO):
        hints = get_type_hints(dto)
        assert hints["images"] == ResourceImages


def test_credential_config_exposes_multi_account_and_accounts():
    hints = get_type_hints(CredentialConfigDTO)
    assert hints["multi_account"] is bool
    assert hints["accounts"] == List[Optional[CredentialDTO]]

    primary: CredentialDTO = {
        "provider": "github",
        "account_id": "acct-1",
        "account_identifier": "work@example.com",
        "is_primary": True,
    }
    secondary: CredentialDTO = {
        "provider": "github",
        "account_id": "acct-2",
        "account_identifier": "personal@example.com",
        "is_primary": False,
    }
    config: CredentialConfigDTO = {
        "slug": "github",
        "provider": "github",
        "multi_account": True,
        "credential": primary,
        "accounts": [primary, secondary],
    }
    assert config["multi_account"] is True
    assert [a["account_id"] for a in config["accounts"]] == ["acct-1", "acct-2"]


def test_secret_create_and_provider_requests_expose_label():
    for cls in (SecretCreateRequest, SecretProviderRequest):
        hints = get_type_hints(cls)
        assert hints["label"] is str

    create: SecretCreateRequest = {"key": "OPENAI_API_KEY", "provider": "openai", "label": "prod"}
    attach: SecretProviderRequest = {"provider": "openai", "label": "personal"}
    assert create["label"] == "prod"
    assert attach["label"] == "personal"


def test_secret_dto_denormalizes_credential_metadata_for_list_rows():
    hints = get_type_hints(SecretDTO)
    assert set(hints) >= {
        "provider",
        "provider_name",
        "label",
        "credential_default",
        "credential_id",
    }
    assert hints["credential_default"] is bool

    row: SecretDTO = {
        "key": "OPENAI_API_KEY",
        "masked_value": "sk-…",
        "credential_id": "cred-9",
        "provider": "openai",
        "provider_name": "OpenAI",
        "label": "prod",
        "credential_default": False,
    }
    assert row["provider_name"] == "OpenAI"
    assert row["credential_default"] is False


def test_artifact_dto_access_uses_permission_including_interact():
    hints = get_type_hints(ArtifactDTO)
    assert hints["access"] == Permission
    assert hints["cover_version_id"] is str

    artifact: ArtifactDTO = {
        "namespace": "acme",
        "name": "dashboard",
        "access": Permission.PERM_INTERACT,
        "cover_version_id": "ver-cover",
        "images": {"card": "https://cdn.example/card.png"},
    }
    wire = json.loads(json.dumps(artifact, default=lambda o: o.value if isinstance(o, Permission) else o))
    assert wire["access"] == "interact"
    assert wire["cover_version_id"] == "ver-cover"


def test_permission_interact_wire_value_is_stable():
    assert Permission.PERM_INTERACT.value == "interact"
