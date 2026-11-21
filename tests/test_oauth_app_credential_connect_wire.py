"""OAuth app picker + connect routing (api-v1589 / 31d6123 typegen).

Workspaces can hold several OAuth apps per provider. ``CredentialConfigDTO.apps``
lists every app a connect may use; ``CredentialConnectRequest.app_credential_id``
names which app the login goes through when the default is ambiguous.
``OAuthAppDTO`` marks which row is default or the owner's usual app.
"""

import json
from typing import List, Optional, get_type_hints

from inferencesh.types import (
    CredentialConfigDTO,
    CredentialConnectRequest,
    CredentialDTO,
    OAuthAppDTO,
)


def test_oauth_app_dto_extends_credential_with_app_flags():
    hints = get_type_hints(OAuthAppDTO)
    base = get_type_hints(CredentialDTO)
    assert set(hints) >= set(base) | {"hook_url", "default", "usual"}
    assert hints["hook_url"] is str
    assert hints["default"] is bool
    assert hints["usual"] is bool

    usual: OAuthAppDTO = {
        "provider": "github",
        "display_name": "Acme GitHub",
        "hook_url": "",
        "default": True,
        "usual": True,
    }
    extra: OAuthAppDTO = {
        "provider": "github",
        "display_name": "Acme GitHub (staging)",
        "hook_url": "https://hooks.example/github",
        "default": False,
        "usual": False,
    }
    assert usual["default"] is True
    assert extra["hook_url"].startswith("https://")


def test_credential_connect_request_exposes_app_credential_id():
    hints = get_type_hints(CredentialConnectRequest)
    assert "app_credential_id" in hints
    assert hints["app_credential_id"] is str

    connect: CredentialConnectRequest = {
        "provider": "github",
        "app_credential_id": "cred_app_staging",
    }
    payload = json.dumps(connect)
    parsed = json.loads(payload)
    assert parsed["app_credential_id"] == "cred_app_staging"


def test_credential_config_lists_oauth_apps_for_multi_app_providers():
    hints = get_type_hints(CredentialConfigDTO)
    assert hints["apps"] == List[Optional[OAuthAppDTO]]

    default_app: OAuthAppDTO = {
        "provider": "github",
        "display_name": "Production",
        "default": True,
        "usual": True,
    }
    staging_app: OAuthAppDTO = {
        "provider": "github",
        "display_name": "Staging",
        "default": False,
        "usual": False,
    }
    config: CredentialConfigDTO = {
        "slug": "github",
        "provider": "github",
        "apps": [default_app, staging_app],
    }
    assert [row["display_name"] for row in config["apps"]] == [
        "Production",
        "Staging",
    ]
    assert config["apps"][0]["default"] is True


def test_connect_names_app_from_config_apps_list():
    """A connect that names an app must reference an id from CredentialConfigDTO.apps."""
    apps: List[OAuthAppDTO] = [
        {
            "provider": "google",
            "display_name": "Workspace",
            "default": True,
            "usual": True,
        },
        {
            "id": "cred_oauth_partner",
            "provider": "google",
            "display_name": "Partner portal",
            "default": False,
            "usual": False,
        },
    ]
    partner_id = apps[1]["id"]

    connect: CredentialConnectRequest = {
        "provider": "google",
        "app_credential_id": partner_id,
    }
    app_ids = {row.get("id") for row in apps}
    assert connect["app_credential_id"] in app_ids