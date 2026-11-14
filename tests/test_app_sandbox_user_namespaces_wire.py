"""App package sandbox exceptions on AppVersionDTO (b0c15c8 typegen).

App ``inf.yml`` may declare ``sandbox.user_namespaces`` so Chromium-style apps
can create unprivileged user namespaces. The API stores the copy on
``AppVersionDTO.sandbox`` for engine enforcement and store review.
"""

import json
from typing import List, Optional, get_type_hints

from inferencesh.types import AppSandbox, AppVersionDTO


def test_app_sandbox_exposes_host_network_capabilities_and_user_namespaces():
    hints = get_type_hints(AppSandbox)
    assert hints["host_network"] is bool
    assert hints["capabilities"] == List[str]
    assert hints["user_namespaces"] is bool


def test_app_version_dto_carries_optional_sandbox_block():
    hints = get_type_hints(AppVersionDTO)
    assert hints["sandbox"] == Optional[AppSandbox]
    assert "sandbox" in hints


def test_app_sandbox_user_namespaces_is_optional_and_composes_with_other_flags():
    minimal: AppSandbox = {"host_network": True}
    chromium: AppSandbox = {
        "capabilities": ["SYS_PTRACE"],
        "user_namespaces": True,
    }
    assert minimal.get("user_namespaces") is None
    assert chromium["user_namespaces"] is True
    assert chromium["capabilities"] == ["SYS_PTRACE"]


def test_app_version_sandbox_round_trips_user_namespaces_on_wire():
    version: AppVersionDTO = {
        "id": "ver-1",
        "sandbox": {
            "host_network": False,
            "user_namespaces": True,
        },
    }
    wire = json.loads(
        json.dumps(version, default=lambda o: o.value if hasattr(o, "value") else o)
    )
    assert wire["sandbox"]["user_namespaces"] is True
    assert wire["sandbox"]["host_network"] is False
