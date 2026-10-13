"""CredentialDTO.template removed (32f1125 typegen).

The catalogue api_key placeholder flag lived on credential rows briefly;
auth scheme metadata carries that now. Clients must not branch on
``template`` on CredentialDTO or they will drift from the API.
"""

from typing import get_type_hints

from inferencesh.types import CredentialDTO


def test_credential_dto_no_longer_declares_template():
    hints = get_type_hints(CredentialDTO)
    assert "template" not in hints


def test_vault_api_key_row_parses_without_template():
    """Connected keys still expose secret refs; catalogue rows omit template."""
    row: CredentialDTO = {
        "provider": "openai",
        "display_name": "Production key",
        "secrets": [
            {"id": "sec_1", "key": "OPENAI_API_KEY", "updated_at": "2026-10-13T10:00:00Z"},
        ],
    }
    assert row["secrets"][0]["key"] == "OPENAI_API_KEY"


def test_catalogue_placeholder_row_has_no_template_field():
    row: CredentialDTO = {
        "provider": "openai",
        "display_name": "OpenAI (catalogue)",
    }
    assert "template" not in row
