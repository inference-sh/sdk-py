"""AuthMethod.hosts wire (types regen fc69d24).

Credential auth methods may bind secrets to explicit outbound hosts so the egress
gateway injects values only on those targets (HostBinder). Empty or omitted hosts
preserve the legacy environment-variable semantics.
"""

import json
from pathlib import Path
from typing import List, get_type_hints

from inferencesh import types as gen
from inferencesh.types import (
    AuthMethod,
    AuthMethodAPIKeyIn,
    AuthMethodKind,
    CredentialRequirement,
)


def test_auth_method_declares_hosts_after_http_scheme_fields():
    hints = get_type_hints(AuthMethod)
    assert hints["hosts"] == List[str]
    assert "hosts" in hints
    assert hints["scheme"]
    assert hints["bearer_format"] is str


def test_auth_method_hosts_document_egress_host_binder():
    block = Path(gen.__file__).read_text(encoding="utf-8")
    start = block.index("AuthMethod = TypedDict")
    end = block.index("'authorization_endpoint'", start)
    hosts_block = block[start:end]
    assert "authmethod.HostBinder" in hosts_block
    assert "db.example.com:5432" in hosts_block
    assert "'hosts': 'List[str]'" in hosts_block


def test_api_key_auth_method_accepts_exact_hosts_including_port():
    method: AuthMethod = {
        "kind": AuthMethodKind.AUTH_METHOD_API_KEY,
        "in": AuthMethodAPIKeyIn.HEADER,
        "param_name": "X-Api-Key",
        "hosts": ["api.anthropic.com", "db.example.com:5432"],
    }
    assert method["hosts"][1].endswith(":5432")
    wire = json.dumps(method, default=lambda v: v.value if hasattr(v, "value") else v)
    parsed = json.loads(wire)
    assert parsed["hosts"] == ["api.anthropic.com", "db.example.com:5432"]
    assert parsed["in"] == "header"


def test_oauth2_auth_method_accepts_hosts_for_token_injection():
    method: AuthMethod = {
        "kind": AuthMethodKind.AUTH_METHOD_O_AUTH2,
        "authorization_endpoint": "https://provider.example/oauth/authorize",
        "hosts": ["api.provider.example"],
    }
    assert method["kind"] is AuthMethodKind.AUTH_METHOD_O_AUTH2
    assert method["hosts"] == ["api.provider.example"]


def test_credential_requirement_auth_method_may_carry_hosts():
    hints = get_type_hints(CredentialRequirement)
    assert hints["auth"] == AuthMethod | None

    req: CredentialRequirement = {
        "slug": "acme-db",
        "auth": {
            "kind": AuthMethodKind.AUTH_METHOD_API_KEY,
            "hosts": ["db.example.com:5432"],
        },
    }
    assert req["auth"]["hosts"] == ["db.example.com:5432"]


def test_auth_method_without_hosts_remains_valid_wire():
    """Unset hosts means secrets stay plain env vars, as before HostBinder."""
    method: AuthMethod = {
        "kind": AuthMethodKind.AUTH_METHOD_HTTP,
        "scheme": "bearer",
    }
    assert "hosts" not in method
