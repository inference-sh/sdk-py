"""Credential vault configs expose ``hook_url`` (models v0.8.156 / 3d3fa0d).

Installation-style apps (e.g. GitHub App) deliver events to a platform or
workspace webhook URL. ``hook_url`` is what operators paste into the app's
settings; OAuth sign-in providers that emit no app events omit it on the wire.
"""

import json
from typing import Optional, get_type_hints

from inferencesh.types import CredentialConfigDTO, CredentialDTO, CredentialGrant, CredentialProvider


def test_credential_config_dto_exposes_hook_url():
    hints = get_type_hints(CredentialConfigDTO)
    assert hints["hook_url"] is str


def test_github_app_installation_config_carries_hook_url_with_app_row():
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
        "hook_url": "https://hooks.inference.example/github-app/acme",
        "app": app_row,
        "credential": {
            "provider": CredentialProvider.GIT_HUB_APP.value,
            "grant": CredentialGrant.CREDENTIALS,
            "app_credential_id": "cred-app-root",
            "account_id": "install-99",
        },
    }
    assert cfg["hook_url"].startswith("https://")
    assert cfg["app"]["provider"] == "github-app"


def test_oauth_sign_in_config_may_omit_hook_url():
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
    assert "hook_url" not in cfg


def test_hook_url_serializes_on_wire_as_string():
    payload = {
        "slug": "github-app",
        "provider": "github-app",
        "hook_url": "https://hooks.inference.example/github-app/ws-1",
        "app": {"provider": "github-app", "grant": "credentials"},
    }
    wire = json.loads(json.dumps(payload))
    assert wire["hook_url"] == "https://hooks.inference.example/github-app/ws-1"
    hints = get_type_hints(CredentialConfigDTO)
    typed: CredentialConfigDTO = {**wire}
    assert typed["hook_url"].endswith("/ws-1")
    assert hints["app"] == Optional[CredentialDTO]
