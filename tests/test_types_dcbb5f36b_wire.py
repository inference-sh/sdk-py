"""Wire shapes after API dcbb5f36b / types regen 102a2bd (run requests, guards, workers).

``ApiAppRunRequest`` no longer carries task ``metadata``; ``TaskMetadata`` and
``TaskAction`` were removed from the generated contract. Agent config and
workers gained fields used by clients parsing engine and entitlement payloads.
"""

from typing import List, get_type_hints

from inferencesh import types as types_mod
from inferencesh.types import (
    AdminElevationStatus,
    AgentConfigInput,
    AgentTool,
    ApiAppRunRequest,
    CapacityAmount,
    ContentGuardConfig,
    ContentGuardMode,
    ContentTier,
    CredentialConnectResponse,
    EngineCapacity,
    EntitlementErrorMeta,
    FeatureRequirement,
    PublicationTheme,
    PublicationThemeColors,
    Visibility,
    VisibilityNotAllowedMeta,
    WorkerDTO,
    WorkerKind,
)


def test_api_app_run_request_has_no_task_metadata_field():
    hints = get_type_hints(ApiAppRunRequest)
    assert "metadata" not in hints
    assert "input" in hints
    assert "run_at" in hints


def test_task_metadata_and_action_types_removed():
    assert not hasattr(types_mod, "TaskMetadata")
    assert not hasattr(types_mod, "TaskAction")


def test_agent_config_exposes_content_guard():
    hints = get_type_hints(AgentConfigInput)
    assert hints["content_guard"] == ContentGuardConfig | None

    guard: ContentGuardConfig = {
        "mode": ContentGuardMode.CONTENT_GUARD_SHADOW,
        "ignore_rules": ["rule-1"],
    }
    cfg: AgentConfigInput = {"content_guard": guard}
    assert cfg["content_guard"]["mode"] is ContentGuardMode.CONTENT_GUARD_SHADOW


def test_agent_tool_supports_content_tier_override():
    hints = get_type_hints(AgentTool)
    assert hints["content_tier"] is ContentTier

    tool: AgentTool = {
        "name": "read_slack",
        "display_name": "Read Slack",
        "description": "Fetch mentions",
        "content_tier": ContentTier.THIRD_PARTY,
    }
    assert tool["content_tier"] is ContentTier.THIRD_PARTY


def test_engine_capacity_commits_apps_slice():
    hints = get_type_hints(EngineCapacity)
    assert hints["committed_apps"] is CapacityAmount

    cap: EngineCapacity = {
        "committed_apps": {"cpus": 0.5, "memory_bytes": 512 * 1024**2},
    }
    assert cap["committed_apps"]["cpus"] == 0.5


def test_entitlement_error_meta_purchase_required_fields():
    hints = get_type_hints(EntitlementErrorMeta)
    assert hints["requirement"] is FeatureRequirement
    assert hints["within_days"] is int
    assert hints["billing_page"] is str

    meta: EntitlementErrorMeta = {
        "requirement": FeatureRequirement.REQUIRE_RECENT_PURCHASE,
        "within_days": 30,
        "billing_page": "/settings/billing",
    }
    assert meta["requirement"].value == "recent_purchase"


def test_worker_dto_app_worker_sizing_fields():
    hints = get_type_hints(WorkerDTO)
    assert hints["kind"] is WorkerKind
    assert hints["vcpus"] is int

    row: WorkerDTO = {
        "kind": WorkerKind.APP,
        "vcpus": 2,
        "memory_mib": 4096,
        "memory_limit_mib": 8192,
        "memory_declared_mib": 0,
    }
    assert row["kind"] is WorkerKind.APP


def test_admin_elevation_status_staff_power_fields():
    hints = get_type_hints(AdminElevationStatus)
    assert "admin_power" in hints
    assert hints["admin_power_until"] == str | None

    status: AdminElevationStatus = {
        "elevated": True,
        "admin_until": "2026-01-01T00:00:00Z",
        "admin_power": True,
        "admin_power_until": "2026-01-01T01:00:00Z",
        "admin_power_withheld": "",
    }
    assert status["admin_power"] is True


def test_credential_connect_response_connect_url():
    hints = get_type_hints(CredentialConnectResponse)
    assert hints["connect_url"] is str

    resp: CredentialConnectResponse = {"connect_url": "https://app.example/c/x"}
    assert resp["connect_url"].startswith("https://")


def test_visibility_not_allowed_and_publication_theme_wire():
    hints_vm = get_type_hints(VisibilityNotAllowedMeta)
    assert hints_vm["visibility"] is Visibility
    assert hints_vm["allowed"] == List[Visibility]

    notice: VisibilityNotAllowedMeta = {
        "resource": "app:123",
        "visibility": Visibility.PRIVATE,
        "allowed": [Visibility.TEAM, Visibility.PUBLIC],
    }
    assert notice["allowed"][0] is Visibility.TEAM

    theme: PublicationTheme = {
        "light": {
            "primary": "#000",
            "secondary": "#111",
            "background": "#fff",
            "text": "#222",
            "border": "#ccc",
        },
        "dark": None,
    }
    light_hints = get_type_hints(PublicationThemeColors)
    assert set(light_hints) == {"primary", "secondary", "background", "text", "border"}
    assert theme["light"]["primary"] == "#000"
