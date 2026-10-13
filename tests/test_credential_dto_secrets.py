"""CredentialDTO.secrets and CredentialSecretRef (09345b2 typegen).

Vault api_key configs and the admin provider tree attach secret row metadata
to credentials (id, key, updated_at) — never raw values. Clients that list or
edit connected accounts rely on this shape staying ref-only.
"""

from typing import get_args, get_origin, get_type_hints

from inferencesh.types import CredentialConfigDTO, CredentialDTO, CredentialSecretRef


def test_credential_secret_ref_is_metadata_only():
    hints = get_type_hints(CredentialSecretRef)
    assert set(hints) == {"id", "key", "updated_at"}
    assert all(h is str for h in hints.values())


def test_credential_dto_exposes_secrets_as_secret_refs():
    hints = get_type_hints(CredentialDTO)
    assert "secrets" in hints
    assert get_origin(hints["secrets"]) is list
    assert get_args(hints["secrets"])[0] is CredentialSecretRef


def test_vault_credential_row_parses_without_secret_values():
    row: CredentialDTO = {
        "provider": "openai",
        "display_name": "Workspace key",
        "secrets": [
            {
                "id": "sec_1",
                "key": "OPENAI_API_KEY",
                "updated_at": "2026-10-13T10:00:00Z",
            },
        ],
    }
    ref = row["secrets"][0]
    assert ref["key"] == "OPENAI_API_KEY"
    assert set(ref) == {"id", "key", "updated_at"}


def test_credential_config_nested_login_can_carry_secrets():
    config: CredentialConfigDTO = {
        "slug": "openai",
        "credential": {
            "provider": "openai",
            "secrets": [
                {"id": "s1", "key": "api_key", "updated_at": "2026-01-01T00:00:00Z"},
            ],
        },
    }
    secrets = config["credential"]["secrets"]
    assert len(secrets) == 1
    assert secrets[0]["id"] == "s1"
