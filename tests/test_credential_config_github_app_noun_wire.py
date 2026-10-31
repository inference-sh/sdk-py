"""GitHub App vault configs expose ``app_noun`` (models v0.8.155 / ab0874b).

Installation-style providers (``CredentialProvider.GIT_HUB_APP``) connect an
app installation, not a person signing in through OAuth. ``app_noun`` is the
human label for that app (e.g. ``GitHub App``); OAuth sign-in configs leave it
empty or omit it on the wire.
"""

import json
from typing import Optional, get_type_hints

from inferencesh.types import CredentialConfigDTO, CredentialDTO, CredentialGrant, CredentialProvider


def test_credential_config_dto_exposes_app_noun():
    hints = get_type_hints(CredentialConfigDTO)
    assert hints["app_noun"] is str


def test_github_app_installation_config_carries_app_noun_and_app_row():
    app_row: CredentialDTO = {
        "provider": CredentialProvider.GIT_HUB_APP.value,
        "grant": CredentialGrant.CREDENTIALS,
        "display_name": "Acme GitHub App",
        "account_id": "install-99",
    }
    cfg: CredentialConfigDTO = {
        "slug": "github-app",
        "provider": CredentialProvider.GIT_HUB_APP.value,
        "name": "GitHub App",
        "app_noun": "GitHub App",
        "app": app_row,
        "credential": {
            "provider": CredentialProvider.GIT_HUB_APP.value,
            "grant": CredentialGrant.CREDENTIALS,
            "app_credential_id": "cred-app-root",
            "account_id": "install-99",
        },
    }
    assert cfg["app_noun"] == "GitHub App"
    assert cfg["app"]["provider"] == "github-app"
    assert cfg["credential"]["app_credential_id"] == "cred-app-root"


def test_oauth_sign_in_config_may_omit_app_noun():
    cfg: CredentialConfigDTO = {
        "slug": "github",
        "provider": CredentialProvider.GIT_HUB.value,
        "name": "GitHub",
        "app": {
            "provider": CredentialProvider.GIT_HUB.value,
            "grant": CredentialGrant.CREDENTIALS,
            "display_name": "Platform GitHub OAuth",
        },
        "credential": {
            "provider": CredentialProvider.GIT_HUB.value,
            "grant": CredentialGrant.TOKEN,
            "account_identifier": "octocat",
        },
    }
    assert "app_noun" not in cfg


def test_app_noun_serializes_on_wire_as_string():
    payload = {
        "slug": "github-app",
        "provider": "github-app",
        "app_noun": "GitHub App",
        "app": {"provider": "github-app", "grant": "credentials"},
    }
    wire = json.loads(json.dumps(payload))
    assert wire["app_noun"] == "GitHub App"
    hints = get_type_hints(CredentialConfigDTO)
    typed: CredentialConfigDTO = {**wire}
    assert typed["app_noun"] == "GitHub App"
    assert hints["app"] == Optional[CredentialDTO]
