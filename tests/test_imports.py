"""Import smoke tests.

Ensures every public module and submodule can be imported without errors.
This catches broken references like the AppSession/AppSessionDTO mismatch
that slipped into 0.7.2 because no test exercised the import path.
"""

import importlib
import pkgutil
from pathlib import Path
from typing import get_type_hints

import pytest
import tomllib

import inferencesh


# ── Package-wide recursive import ────────────────────────────────────────────

def _iter_submodules(package, prefix=""):
    """Yield dotted names of every submodule/subpackage under *package*."""
    for importer, modname, ispkg in pkgutil.walk_packages(
        package.__path__, prefix=package.__name__ + "."
    ):
        yield modname


def test_all_submodules_importable():
    """Every .py under inferencesh/ must import cleanly."""
    failures = []
    for modname in _iter_submodules(inferencesh):
        try:
            importlib.import_module(modname)
        except Exception as exc:
            failures.append(f"{modname}: {exc}")

    assert not failures, "Failed imports:\n" + "\n".join(failures)


# ── Top-level __all__ exports ────────────────────────────────────────────────

def test_all_exports_resolvable():
    """Every name in __all__ must be accessible on the package."""
    missing = [name for name in inferencesh.__all__ if not hasattr(inferencesh, name)]
    assert not missing, f"Names in __all__ but missing from package: {missing}"


def test_top_level_llminput_is_pydantic_model():
    """`from inferencesh import LLMInput` must be the app base model, not the
    generated TypedDict of the same name (apps subclass it: `class AppInput(LLMInput)`)."""
    from pydantic import BaseModel

    from inferencesh import LLMInput
    from inferencesh.models.llm import LLMInput as ModelLLMInput

    assert LLMInput is ModelLLMInput
    assert issubclass(LLMInput, BaseModel)


def test_package_version_matches_pyproject():
    """Release bumps must keep importlib metadata in sync with pyproject (User-Agent)."""
    pyproject = tomllib.loads(
        (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(encoding="utf-8")
    )
    assert inferencesh.__version__ == pyproject["project"]["version"]


# ── Core public API imports ──────────────────────────────────────────────────

@pytest.mark.parametrize("name", [
    # Base app types
    "BaseApp", "BaseAppInput", "BaseAppOutput", "BaseAppSetup", "File",
    # Client helpers (exported in 8cb6eaf)
    "parse_status", "is_terminal_status", "is_message_ready",
    # Client
    "Inference", "AsyncInference",
    # Namespaced APIs
    "TasksAPI", "AsyncTasksAPI",
    "FilesAPI", "AsyncFilesAPI",
    "AgentsAPI", "AsyncAgentsAPI",
    "SessionsAPI", "AsyncSessionsAPI",
    "SessionHandle", "AsyncSessionHandle",
    # Agent SDK
    "Agent", "AsyncAgent",
    # Tools
    "tool", "app_tool", "agent_tool", "http_tool", "call_tool", "mcp_tool",
    "lifecycle_hook", "learning_hooks",
    # Errors
    "APIError", "SessionError", "SessionNotFoundError",
    # Streamable
    "streamable", "streamable_raw",
    # Ref parsing
    "Ref",
    # Live control-frame keys (documented alongside AsyncLiveSession)
    "CLEAR_KEY", "ERROR_KEY", "LiveUpdate",
    # OutputMeta
    "OutputMeta", "TextMeta", "ImageMeta", "VideoMeta", "AudioMeta", "probe_video",
])
def test_public_name_importable(name):
    """Core public names must be importable from the top-level package."""
    assert hasattr(inferencesh, name), f"inferencesh.{name} not found"


# ── Submodule direct imports ─────────────────────────────────────────────────

@pytest.mark.parametrize("module", [
    "inferencesh.client",
    "inferencesh.types",
    "inferencesh.agent",
    "inferencesh.tools",
    "inferencesh.streamable",
    "inferencesh.api",
    "inferencesh.api.sessions",
    "inferencesh.api.tasks",
    "inferencesh.api.files",
    "inferencesh.api.agents",
    "inferencesh.models",
    "inferencesh.models.base",
    "inferencesh.models.file",
    "inferencesh.models.llm",
    "inferencesh.models.decision",
    "inferencesh.models.output_meta",
    "inferencesh.models.errors",
    "inferencesh.utils",
    "inferencesh.utils.storage",
    "inferencesh.utils.download",
])
def test_submodule_importable(module):
    """Each submodule must import without errors."""
    importlib.import_module(module)


@pytest.mark.parametrize("name", [
    "ChatInput",
    "ModelSettings",
    "ModelSettingsCapabilityMixin",
    "LLMDelta",
])
def test_models_llm_export_exists(name):
    """New LLM input types from v0.7.9 must be exported from models."""
    from inferencesh import models
    assert hasattr(models, name), f"inferencesh.models.{name} not found"


@pytest.mark.parametrize("name", [
    "DecisionInput",
    "DecisionVisionInput",
    "DecisionOutput",
])
def test_models_decision_export_exists(name):
    """v0.20 decision contract types must be exported from models."""
    from inferencesh import models

    assert hasattr(models, name), f"inferencesh.models.{name} not found"
    assert name in models.__all__


# ── Generated types (from typegen) ───────────────────────────────────────────

@pytest.mark.parametrize("name", [
    # Enums
    "ChatStatus", "ChatMessageRole", "ChatMessageStatus", "ChatMessageContentType",
    "PlanStepStatus", "FlowRunStatus", "AppCategory", "Visibility",
    "AppSessionStatus", "FilterOperator", "MetaItemType",
    "ToolType", "ToolInvocationStatus", "TaskStatus",
    "PageStatus", "PageType", "ProjectType", "TeamInviteStatus",
    "TeamRole", "TeamType", "TeamStatus", "ContentRating",
    "UsageEventResourceTier", "Infra", "TaskLogType", "Role",
    "GPUType", "Filter", "CursorListRequest",
    # DTOs
    "ChatDTO", "ChatMessageDTO", "AgentRunDTO", "AgentRunState", "InterruptReason",
    "AgentToolDTO", "ToolInvocationDTO",
    "AppSessionDTO", "PageDTO", "ProjectDTO", "TeamInviteDTO",
    "FileDTO", "UsageEventDTO",
    # Agent config + policy (v0.17.0 typegen)
    "AgentPermissions", "AgentConfigInput", "AgentTool", "InternalToolsConfig",
    "PolicyEffect", "PolicyKind", "PolicyRuleDTO",
    # Tool schema
    "Tool", "ToolFunction", "ToolParameters", "ToolCall", "ToolCallFunction",
    "ToolCallDelta", "ToolCallFunctionDelta", "LLMDelta",
    "ToolCallType", "ToolParamType",
    # Credentials
    "CredentialProvider", "CredentialType", "CredentialStatus",
    "InstanceStatus", "InstanceRentalType", "InstanceDTO", "InstanceTypeAvailability",
    "GraphEdgeType", "GraphNodeType", "GraphNodeStatus",
    # Suggest endpoint (0637e77)
    "SuggestRequest", "SuggestResponse", "SuggestResult",
    # Instance types (eff7d5e, 28cd082)
    "InstanceTypeDTO", "InstanceTypeConfiguration",
    # Billing, knowledge, oauth, notifications (0c6e23a regen)
    "SubscriptionStatus", "SubscriptionInterval", "SubscriptionDTO",
    "ResourceType", "SecretScope", "DeviceAuthStatus", "DeviceTokenKind",
    "DeviceAuthInitRequest", "DeviceAuthResponse", "DeviceAuthPollResponse",
    "UpdateCredentialScopesRequest", "CredentialCompleteOAuthRequest",
    "RequirementType", "CredentialConfigDTO",
    "Scope", "ScopeGroup", "AuthSessionDTO", "ScopesResponse", "ScopeDefinition",
    "ScopePreset", "EstimateCostRequest", "EstimateCostResponse", "AppPricing",
    "SetupActionType", "EngineStatus",
    "CredentialScope", "CredentialRequirement", "SecretRequirement",
    "EntitlementResource", "EntitlementSource", "EntitlementType", "EnforcementMode",
    "WorkerStatus", "EntitlementDTO",
    "PlanLimit", "PlanLimits", "PlanDTO", "PlanType", "PlanVersionDTO",
    "EntitlementErrorMeta",
    "AppStatus", "AppDTO", "SkillDTO",
    "CheckRequirementsRequest", "CheckRequirementsResponse",
    "KnowledgeDTO", "KnowledgeCreateRequest", "KnowledgeVersionDTO", "KnowledgeVersionInput",
    "KnowledgeType", "KnowledgeLifecycle",
    "OAuthAuthorizeInfoResponse", "CreateSubscriptionRequest",
    "NotificationType", "NotificationChannel", "NotificationStatus",
    "MCPServerAuthType", "ToolAuthType", "RefRouteType", "RefRouteMode", "RefRouteDTO", "ChannelType",
    "DescriptionLimit",
    "ChannelContext", "CreateAgentMessageRequest",
    # App store + user metadata (6fd3aac typegen regen)
    "AppStoreListingDTO", "UserMetadataDTO",
    # MCP elicitation + tool annotations (cc67205 typegen regen)
    "ElicitAction", "ResultType", "CacheScope", "ToolContentType",
    "ElicitationCapability", "ClientCapabilities", "InputRequest", "ElicitResult",
    "ServerInfo", "ResultMeta", "ResourceContent",
    "ToolCallRequest", "ToolCallResponse", "ToolContent",
    "AgentRunDTO", "FlowDTO",
    # Flow utility nodes + knowledge provenance (v0.7.86 typegen regen)
    "SelectorConfig", "UtilityConfig", "GateCondition",
    # A2UI widget migration (v0.7.63–v0.7.65 typegen regen)
    "A2UIComponentType", "A2UISurface", "Widget",
    # Gate hooks + interrupts (gate hooks / InterruptDTO typegen regen)
    "InterruptDTO", "InterruptStatus", "InterruptResolution", "InterruptResourceType",
    "HookEventDefinition", "LifecycleHookConfig",
    # Auth + catalog (v0.7.67+ typegen regen)
    "AuthResponse", "PublicAppStoreDTO",
    # User stats, flow run node state, telemetry (v0.7.97 typegen regen)
    "MeStatsResponse", "StatBuckets",
    "SubmitTelemetryRequest", "TelemetryReportDTO",
    # Store browse catalog (254df4b typegen regen)
    "StoreCategoryDTO", "StoreTagDTO",
])
def test_generated_type_exists(name):
    """Typegen'd types must exist in inferencesh.types."""
    from inferencesh import types
    assert hasattr(types, name), f"inferencesh.types.{name} not found"


def test_instance_rental_type_wire_values():
    """Engine-picker spot vs on-demand offers use these JSON enum strings."""
    from inferencesh.types import InstanceRentalType

    assert InstanceRentalType.ON_DEMAND.value == "on_demand"
    assert InstanceRentalType.SPOT.value == "spot"


def test_instance_type_spot_availability_includes_hourly_price_cents():
    from inferencesh.types import InstanceRentalType, InstanceTypeAvailability

    offer: InstanceTypeAvailability = {
        "available": True,
        "region": "us-east-1",
        "rental_type": InstanceRentalType.SPOT,
        "hourly_price": 199,
    }
    assert offer["rental_type"] is InstanceRentalType.SPOT
    assert offer["hourly_price"] == 199


def test_agent_permissions_on_version_config_contract():
    """Agent version permissions seed new chats; chat settings toggle an existing chat (INF-906)."""
    from inferencesh.types import (
        AgentConfigInput,
        AgentPermissions,
        AgentVersionDTO,
        ChatSettingsRequest,
    )

    perms: AgentPermissions = {"allow_all_tools": True}
    version_config: AgentConfigInput = {
        "name": "cron-runner",
        "permissions": perms,
    }
    assert version_config["permissions"]["allow_all_tools"] is True

    published: AgentVersionDTO = {
        "id": "ver_1",
        "permissions": {"allow_all_tools": False},
    }
    assert published["permissions"]["allow_all_tools"] is False

    chat_settings: ChatSettingsRequest = {"allow_all_tools": True}
    assert chat_settings["allow_all_tools"] is True
    assert "permissions" not in chat_settings


def test_policy_rule_kind_enum_contract():
    """PolicyRuleDTO.kind is PolicyKind (usage + execution kinds), not an untyped string (v0.17.0)."""
    from inferencesh.types import PolicyEffect, PolicyKind, PolicyRuleDTO

    assert PolicyKind.REMOTE_EXEC.value == "RemoteExec"
    assert PolicyKind.WEB_FETCH.value == "WebFetch"
    assert PolicyKind.MCP.value == "Mcp"
    assert get_type_hints(PolicyRuleDTO)["kind"] is PolicyKind

    exec_rule: PolicyRuleDTO = {
        "effect": PolicyEffect.ASK,
        "kind": PolicyKind.REMOTE_EXEC,
        "selector": "remote_laptop",
        "specifier": "git push:*",
        "label": "git push on Laptop",
    }
    usage_rule: PolicyRuleDTO = {
        "effect": PolicyEffect.DENY,
        "kind": PolicyKind.APP,
        "selector": "",
        "specifier": "app_storefront",
        "label": "block storefront app",
    }
    assert exec_rule["kind"] is PolicyKind.REMOTE_EXEC
    assert usage_rule["kind"] is PolicyKind.APP


def test_chat_data_uses_allow_all_tools_not_legacy_list():
    """Chat always-allow moved from always_allowed_tools list to allow_all_tools (v0.17.0)."""
    from inferencesh.types import ChatData

    hints = get_type_hints(ChatData)
    assert "allow_all_tools" in hints
    assert "always_allowed_tools" not in hints

    session: ChatData = {"allow_all_tools": True, "disable_hooks": False}
    assert session["allow_all_tools"] is True


def test_team_dto_dropped_usage_policy_id():
    """Team usage policy is no longer a field on TeamDTO (v0.17.0)."""
    from inferencesh.types import TeamDTO

    assert "usage_policy_id" not in get_type_hints(TeamDTO)


class TestDescriptionLimit:
    """Guards API description length constants (4bb3b0e typegen regen)."""

    def test_listing_and_skill_limits(self):
        from enum import IntEnum

        from inferencesh.types import DescriptionLimit

        assert issubclass(DescriptionLimit, IntEnum)
        assert DescriptionLimit.LISTING == 200
        assert DescriptionLimit.SKILL == 1024
        assert int(DescriptionLimit.LISTING) == 200
        assert int(DescriptionLimit.SKILL) == 1024
