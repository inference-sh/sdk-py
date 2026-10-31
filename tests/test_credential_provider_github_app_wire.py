"""Credential provider slugs and GitHub App rows (models v0.8.154 / bcb5001).

``CredentialProvider.GIT_HUB_APP`` is the wire slug for GitHub App
installations; it must stay distinct from ``GIT_HUB`` (user OAuth).
``CredentialDTO.app_credential_id`` links a login row to its parent app
credential and is part of the same vault surface.
"""

import json
from typing import Optional, get_type_hints

from inferencesh.types import CredentialDTO, CredentialGrant, CredentialProvider


def test_credential_provider_github_app_wire_slug():
    assert CredentialProvider.GIT_HUB_APP.value == "github-app"
    assert CredentialProvider("github-app") is CredentialProvider.GIT_HUB_APP


def test_credential_provider_github_app_distinct_from_user_oauth():
    assert CredentialProvider.GIT_HUB.value == "github"
    assert CredentialProvider.GIT_HUB_APP is not CredentialProvider.GIT_HUB


def test_credential_provider_github_app_serializes_as_wire_string():
    wire = json.loads(json.dumps({"provider": CredentialProvider.GIT_HUB_APP}))
    assert wire == {"provider": "github-app"}


def test_credential_dto_exposes_app_credential_id_for_installation_rows():
    hints = get_type_hints(CredentialDTO)
    assert hints["app_credential_id"] == Optional[str]

    app_row: CredentialDTO = {
        "provider": CredentialProvider.GIT_HUB_APP.value,
        "grant": CredentialGrant.CREDENTIALS,
        "display_name": "Acme GitHub App",
        "account_id": "app-install-1",
    }
    login_row: CredentialDTO = {
        "provider": CredentialProvider.GIT_HUB.value,
        "grant": CredentialGrant.TOKEN,
        "app_credential_id": "cred-app-parent",
        "account_id": "user-42",
        "account_identifier": "octocat",
    }
    assert app_row["provider"] == "github-app"
    assert login_row["app_credential_id"] == "cred-app-parent"
