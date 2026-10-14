"""Secret label and CredentialConfigDTO.multi_account (532530e typegen).

Creating or attaching a secret can name which key slot belongs to a provider
(prod vs personal). Credential catalog rows expose whether several accounts
can be connected side by side (multi_account) alongside the accounts list.
"""

from typing import List, Optional, get_type_hints

from inferencesh.types import (
    CredentialConfigDTO,
    CredentialDTO,
    CredentialScope,
    SecretCreateRequest,
    SecretProviderRequest,
    SecretUpdateRequest,
)


def test_secret_create_request_declares_label():
    hints = get_type_hints(SecretCreateRequest)
    assert hints["label"] is str
    assert "provider" in hints
    assert hints["connection_scope"] is CredentialScope


def test_secret_provider_request_declares_label():
    hints = get_type_hints(SecretProviderRequest)
    assert hints["label"] is str
    assert hints["provider"] is str


def test_secret_update_request_does_not_carry_label():
    """Label is chosen at create/attach time, not on value-only updates."""
    hints = get_type_hints(SecretUpdateRequest)
    assert "label" not in hints
    assert set(hints) <= {"value", "description"}


def test_credential_config_dto_declares_multi_account_and_accounts():
    hints = get_type_hints(CredentialConfigDTO)
    assert hints["multi_account"] is bool
    assert hints["accounts"] == List[Optional[CredentialDTO]]


def test_labeled_secret_create_and_provider_attach_rows():
    create: SecretCreateRequest = {
        "key": "OPENAI_API_KEY",
        "value": "sk-test",
        "provider": "openai",
        "label": "prod",
        "connection_scope": CredentialScope.TEAM,
    }
    attach: SecretProviderRequest = {
        "provider": "openai",
        "label": "personal",
        "connection_scope": CredentialScope.USER,
    }
    assert create["label"] == "prod"
    assert attach["label"] == "personal"


def test_multi_account_catalog_row_with_accounts_list():
    row: CredentialConfigDTO = {
        "slug": "openai",
        "provider": "openai",
        "name": "OpenAI",
        "multi_account": True,
        "accounts": [None, {"id": "cred_2", "provider": "openai", "is_primary": False}],
        "allows_byok": True,
        "available": True,
    }
    assert row["multi_account"] is True
    assert len(row["accounts"]) == 2
