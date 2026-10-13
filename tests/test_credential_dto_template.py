"""CredentialDTO.template (073a537 typegen).

Api_key providers expose a catalogue template row (empty platform credential
teams connect their own key against). Clients listing vault or admin provider
trees must distinguish that row from real connected keys via ``template``.
"""

from typing import get_type_hints

from inferencesh.types import CredentialDTO


def test_credential_dto_exposes_template_boolean():
    hints = get_type_hints(CredentialDTO)
    assert "template" in hints
    assert hints["template"] is bool


def test_catalogue_template_row_is_flagged():
    """Platform catalogue rows are template placeholders, not team secrets."""
    row: CredentialDTO = {
        "provider": "openai",
        "display_name": "OpenAI (catalogue)",
        "template": True,
    }
    assert row["template"] is True


def test_team_connected_key_is_not_template():
    row: CredentialDTO = {
        "provider": "openai",
        "display_name": "Production key",
        "template": False,
        "secrets": [
            {"id": "sec_1", "key": "OPENAI_API_KEY", "updated_at": "2026-10-13T10:00:00Z"},
        ],
    }
    assert row["template"] is False
    assert row["secrets"][0]["key"] == "OPENAI_API_KEY"
