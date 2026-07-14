"""Import smoke tests.

Ensures every public module and submodule can be imported without errors.
This catches broken references like the AppSession/AppSessionDTO mismatch
that slipped into 0.7.2 because no test exercised the import path.
"""

import importlib
import pkgutil

import pytest

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
    # DTOs
    "ChatDTO", "ChatMessageDTO", "AgentToolDTO", "ToolInvocationDTO",
    "AppSessionDTO",
    # Agent config
    "AgentConfigInput", "AgentTool", "InternalToolsConfig",
    # Tool schema
    "Tool", "ToolFunction", "ToolParameters", "ToolCall", "ToolCallFunction",
    "ToolCallType", "ToolParamType",
    # Integrations
    "IntegrationProvider", "IntegrationAuthType", "IntegrationStatus",
    "InstanceStatus",
    "GraphEdgeType", "GraphNodeType", "GraphNodeStatus",
    # Suggest endpoint (0637e77)
    "SuggestRequest", "SuggestResponse", "SuggestResult",
    # Instance types (eff7d5e, 28cd082)
    "InstanceTypeDTO", "InstanceTypeConfiguration",
    # Billing, knowledge, oauth, notifications (0c6e23a regen)
    "SubscriptionStatus", "SubscriptionInterval", "SubscriptionDTO",
    "ResourceType", "SecretScope", "DeviceAuthStatus", "DeviceTokenKind",
    "DeviceAuthInitRequest", "DeviceAuthResponse", "DeviceAuthPollResponse",
    "UpdateIntegrationScopesRequest",
    "RequirementType", "IntegrationConfigDTO",
    "Scope", "ScopeGroup", "AuthSessionDTO", "ScopesResponse", "ScopeDefinition",
    "SetupActionType", "EngineStatus",
    "IntegrationScope", "IntegrationRequirement", "SecretRequirement",
    "EntitlementResource", "EntitlementSource", "EntitlementType", "EnforcementMode",
    "WorkerStatus", "EntitlementDTO",
    "PlanLimit", "PlanLimits", "PlanDTO",
    "CheckRequirementsRequest", "CheckRequirementsResponse",
    "KnowledgeDTO", "KnowledgeCreateRequest", "KnowledgeVersionDTO",
    "KnowledgeType", "KnowledgeLifecycle",
    "OAuthAuthorizeInfoResponse", "CreateSubscriptionRequest",
    "NotificationType", "NotificationChannel", "NotificationStatus",
    "MCPServerAuthType", "RefRouteType", "IntegrationType",
    # App store + user metadata (6fd3aac typegen regen)
    "AppStoreListingDTO", "UserMetadataDTO",
])
def test_generated_type_exists(name):
    """Typegen'd types must exist in inferencesh.types."""
    from inferencesh import types
    assert hasattr(types, name), f"inferencesh.types.{name} not found"
