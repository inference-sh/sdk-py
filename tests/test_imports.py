"""Import smoke tests.

Ensures every public module and submodule can be imported without errors.
This catches broken references like the AppSession/AppSessionDTO mismatch
that slipped into 0.7.2 because no test exercised the import path.
"""

import importlib
import pkgutil
from pathlib import Path

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
    # Agent config
    "AgentConfigInput", "AgentTool", "InternalToolsConfig",
    # Tool schema
    "Tool", "ToolFunction", "ToolParameters", "ToolCall", "ToolCallFunction",
    "ToolCallDelta", "ToolCallFunctionDelta", "LLMDelta",
    "ToolCallType", "ToolParamType",
    # Credentials
    "CredentialProvider", "CredentialType", "CredentialStatus",
    "InstanceStatus",
    "GraphEdgeType", "GraphNodeType", "GraphNodeStatus",
    # Suggest endpoint (0637e77)
    "SuggestRequest", "SuggestResponse", "SuggestResult",
    # Instance types (eff7d5e, 28cd082; engine-picker options 9d6a811)
    "InstanceTypeDTO", "InstanceTypeConfiguration",
    "InstanceTypeOptionDTO", "InstanceTypeOptionRegion",
    # API keys + workspace principals (INF-966, 2150d23 / bd09de9)
    "ApiKeyScope", "ApiKeyDTO", "CreateApiKeyRequest", "TeamMemberUserDTO",
    "TeamCapability", "ErrorCode",
    # Chat settings + MCP server catalog (080030a / d26bf0d typegen regen)
    "ChatSettingsRequest", "ChatData", "MCPServerDTO", "MCPServerSetup",
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
])
def test_generated_type_exists(name):
    """Typegen'd types must exist in inferencesh.types."""
    from inferencesh import types
    assert hasattr(types, name), f"inferencesh.types.{name} not found"


def test_engine_picker_instance_type_offer_lists_provider_options():
    """Engine-picker offers expose in-stock providers (cheapest first) on options."""
    from inferencesh.types import (
        InstanceCloudProvider,
        InstanceRentalType,
        InstanceTypeDTO,
        InstanceTypeOptionDTO,
        InstanceTypeOptionRegion,
    )

    us_east: InstanceTypeOptionRegion = {"region": "us-east-1", "hourly_price": 180}
    us_west: InstanceTypeOptionRegion = {"region": "us-west-2", "hourly_price": 210}

    primary: InstanceTypeOptionDTO = {
        "cloud": InstanceCloudProvider.CLOUD_AWS,
        "shade_instance_type": "gpu-a100-80gb",
        "cloud_instance_type": "p4d.24xlarge",
        "hourly_price": 180,
        "regions": [us_east, us_west],
    }
    alternate: InstanceTypeOptionDTO = {
        "cloud": InstanceCloudProvider.CLOUD_LAMBDA_LABS,
        "shade_instance_type": "gpu-a100-80gb",
        "cloud_instance_type": "gpu_8x_a100_80gb",
        "hourly_price": 195,
        "regions": [{"region": "us-east-1", "hourly_price": 195}],
    }

    offer: InstanceTypeDTO = {
        "cloud": InstanceCloudProvider.CLOUD_AWS,
        "region": "us-east-1",
        "shade_instance_type": "gpu-a100-80gb",
        "cloud_instance_type": "p4d.24xlarge",
        "hourly_price": 180,
        "rental_type": InstanceRentalType.ON_DEMAND,
        "options": [primary, alternate],
    }

    assert offer["options"][0]["cloud"] is InstanceCloudProvider.CLOUD_AWS
    assert offer["options"][0]["hourly_price"] <= offer["options"][1]["hourly_price"]
    assert offer["options"][0]["regions"][1]["hourly_price"] == 210
    assert offer["rental_type"] is InstanceRentalType.ON_DEMAND


def test_api_key_scope_personal_vs_workspace_keys():
    """Workspace keys act as the service account; personal keys act as the creator."""
    from inferencesh.types import (
        ApiKeyDTO,
        ApiKeyScope,
        CreateApiKeyRequest,
        ErrorCode,
        MeResponse,
        Scope,
        TeamCapability,
        TeamMemberUserDTO,
    )

    assert ApiKeyScope.USER.value == "user"
    assert ApiKeyScope.WORKSPACE.value == "workspace"
    assert TeamCapability.CREATE_KEYS.value == "create_keys"
    assert TeamCapability.MANAGE_KEYS.value == "manage_keys"
    assert ErrorCode.PERSON_REQUIRED.value == "person_required"
    assert ErrorCode.LAST_OWNER.value == "last_owner"

    create: CreateApiKeyRequest = {
        "name": "deploy-bot",
        "scopes": [Scope.ENGINES_READ.value],
        "scope": ApiKeyScope.WORKSPACE,
    }
    assert create["scope"] is ApiKeyScope.WORKSPACE

    creator: TeamMemberUserDTO = {
        "id": "user_admin",
        "email": "admin@example.com",
        "name": "admin",
    }
    listed: ApiKeyDTO = {
        "name": "deploy-bot",
        "scopes": [Scope.ENGINES_READ],
        "scope": ApiKeyScope.WORKSPACE,
        "created_by": "user_admin",
        "creator": creator,
        "source": "dashboard",
    }
    assert listed["scope"] is ApiKeyScope.WORKSPACE
    assert listed["creator"]["id"] == "user_admin"
    assert "last_used_at" not in listed

    used: ApiKeyDTO = {**listed, "last_used_at": "2026-10-01T12:00:00Z"}
    assert used["last_used_at"] == "2026-10-01T12:00:00Z"

    me: MeResponse = {
        "personal_team_id": "team_personal",
        "needs_username": True,
    }
    assert me["needs_username"] is True


def test_chat_settings_partial_updates_and_mcp_admin_headers():
    """Chat settings PATCH fields are independent; MCP catalog carries admin headers."""
    from inferencesh.types import (
        ChatData,
        ChatSettingsRequest,
        MCPServerDTO,
        MCPServerSetup,
        Visibility,
    )

    hooks_off: ChatSettingsRequest = {"disable_hooks": True}
    assert hooks_off["disable_hooks"] is True
    assert "allow_all_tools" not in hooks_off

    forget_only: ChatSettingsRequest = {"forget_memory": ["user_preference", "stale_fact"]}
    assert forget_only["forget_memory"] == ["user_preference", "stale_fact"]
    assert "disable_hooks" not in forget_only
    assert "name" not in forget_only

    combined: ChatSettingsRequest = {
        "disable_hooks": False,
        "forget_memory": ["one_key"],
    }
    assert combined["forget_memory"] == ["one_key"]
    assert combined["disable_hooks"] is False

    full_settings: ChatSettingsRequest = {
        "name": "review branch",
        "visibility": Visibility.TEAM,
        "allow_all_tools": True,
        "disable_hooks": True,
    }
    assert full_settings["visibility"] is Visibility.TEAM

    agent_data: ChatData = {
        "allow_all_tools": False,
        "disable_hooks": True,
    }
    assert agent_data["disable_hooks"] is True
    assert agent_data["allow_all_tools"] is False

    setup: MCPServerSetup = {
        "resource_app_id": "00000000-0000-0000-0000-000000000000",
        "recommended_headers": {"X-MCP-Toolsets": "read"},
    }
    server: MCPServerDTO = {
        "slug": "acme-mcp",
        "headers": {"X-MCP-Readonly": "true"},
        "setup": setup,
    }
    assert server["headers"]["X-MCP-Readonly"] == "true"
    assert server["setup"]["recommended_headers"]["X-MCP-Toolsets"] == "read"
