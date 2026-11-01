"""OAuth scope wire contract on AuthMethod (1e531f7 typegen docs).

Provider catalogs describe scopes in the provider's own wire names (what a
credential stores). ``scope_aliases`` are shorthand accepted on input only;
capabilities, allowed lists, and stored credentials use wire form.
"""

import json
from typing import Dict, List, get_type_hints

from inferencesh.types import (
    AuthMethod,
    AuthMethodCapability,
    AuthMethodKind,
    UpdateCredentialScopesRequest,
)

_GMAIL_SEND_WIRE = "https://www.googleapis.com/auth/gmail.send"
_GMAIL_READONLY_WIRE = "https://www.googleapis.com/auth/gmail.readonly"
_OPENID_WIRE = "openid"


def test_auth_method_capability_declares_wire_scope_list():
    hints = get_type_hints(AuthMethodCapability)
    assert hints["scopes"] == List[str]
    assert hints["key"] is str
    assert hints["satisfies"] == List[str]


def test_auth_method_capability_holds_provider_wire_names():
    """Capabilities compare and store scopes in provider wire form, not aliases."""
    cap: AuthMethodCapability = {
        "key": "send_mail",
        "scopes": [_GMAIL_SEND_WIRE],
        "satisfies": ["gmail"],
        "display_name": "Send email",
    }
    assert cap["scopes"] == [_GMAIL_SEND_WIRE]
    assert "gmail.send" not in cap["scopes"]


def test_auth_method_exposes_oauth_scope_configuration_fields():
    hints = get_type_hints(AuthMethod)
    assert hints["scopes"] == List[str]
    assert hints["scope_aliases"] == Dict[str, str]
    assert hints["required_scopes"] == List[str]
    assert hints["incremental_add_scopes"] is bool
    assert hints["add_scopes_params"] == Dict[str, str]
    assert hints["capabilities"] == List[AuthMethodCapability]


def test_auth_method_oauth_catalog_uses_wire_names_with_input_aliases():
    method: AuthMethod = {
        "kind": AuthMethodKind.AUTH_METHOD_O_AUTH2,
        "scopes": [_GMAIL_SEND_WIRE, _GMAIL_READONLY_WIRE],
        "scope_aliases": {
            "gmail.send": _GMAIL_SEND_WIRE,
            "gmail.readonly": _GMAIL_READONLY_WIRE,
        },
        "required_scopes": [_OPENID_WIRE, "email", "profile"],
        "incremental_add_scopes": True,
        "add_scopes_params": {"include_granted_scopes": "true"},
        "capabilities": [
            {
                "key": "send",
                "scopes": [_GMAIL_SEND_WIRE],
                "satisfies": ["send_mail"],
            },
        ],
    }
    assert method["capabilities"][0]["scopes"] == [_GMAIL_SEND_WIRE]
    assert method["scope_aliases"]["gmail.send"] == _GMAIL_SEND_WIRE
    assert _OPENID_WIRE in method["required_scopes"]


def test_auth_method_oauth_scope_fields_use_snake_case_json_keys():
    payload = {
        "kind": "oauth2",
        "scope_aliases": {"gmail.send": _GMAIL_SEND_WIRE},
        "required_scopes": [_OPENID_WIRE],
        "incremental_add_scopes": True,
        "add_scopes_params": {"include_granted_scopes": "true"},
    }
    wire = json.loads(json.dumps(payload))
    assert set(wire) >= {
        "scope_aliases",
        "required_scopes",
        "incremental_add_scopes",
        "add_scopes_params",
    }
    assert "scopeAliases" not in wire
    assert "requiredScopes" not in wire


def test_update_credential_scopes_request_accepts_wire_scope_strings():
    hints = get_type_hints(UpdateCredentialScopesRequest)
    assert hints["scopes"] == List[str]
    req: UpdateCredentialScopesRequest = {"scopes": [_GMAIL_READONLY_WIRE]}
    assert req["scopes"][0].startswith("https://")
