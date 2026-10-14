"""SecretDTO credential preload fields (f969c81 typegen).

Secret list rows can include provider slug, display name, account label, and
whether the linked credential is the owner's default. Those fields come from
the preloaded credential; a row read without that join leaves them empty.
``credential_default`` is always serialised so a linked non-default key and an
unlabelled plain secret do not look identical in the UI.
"""

from typing import get_type_hints

from inferencesh.types import SecretDTO, SecretScope


def test_secret_dto_declares_credential_preload_fields():
    hints = get_type_hints(SecretDTO)
    assert hints["provider"] is str
    assert hints["provider_name"] is str
    assert hints["label"] is str
    assert hints["credential_default"] is bool
    assert hints["credential_id"] is str
    assert hints["scope"] is SecretScope


def test_secret_dto_listing_row_with_preloaded_credential():
    row: SecretDTO = {
        "key": "ANTHROPIC_API_KEY",
        "masked_value": "sk-ant-…abc",
        "description": "Prod workspace",
        "scope": SecretScope.TEAM,
        "credential_id": "cred_prod",
        "provider": "anthropic",
        "provider_name": "Anthropic",
        "label": "prod",
        "credential_default": False,
    }
    assert row["provider"] == "anthropic"
    assert row["provider_name"] == "Anthropic"
    assert row["label"] == "prod"
    assert row["credential_default"] is False


def test_credential_default_false_is_distinct_from_plain_secret_row():
    """API must send explicit false; omitting the field is not the same contract."""
    linked_non_default: SecretDTO = {
        "key": "OPENAI_API_KEY",
        "masked_value": "sk-…",
        "credential_id": "cred_2",
        "provider": "openai",
        "label": "personal",
        "credential_default": False,
    }
    plain: SecretDTO = {
        "key": "CUSTOM_TOKEN",
        "masked_value": "tok-…",
        "credential_id": "",
    }
    assert linked_non_default["credential_default"] is False
    assert "credential_default" not in plain


def test_default_credential_row_sets_credential_default_true():
    row: SecretDTO = {
        "key": "OPENAI_API_KEY",
        "masked_value": "sk-…",
        "credential_id": "cred_primary",
        "provider": "openai",
        "provider_name": "OpenAI",
        "label": "",
        "credential_default": True,
    }
    assert row["credential_default"] is True
    assert row["label"] == ""
