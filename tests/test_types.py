"""Tests for generated enum constants (gotypegen acronym preservation)."""

import pytest

from inferencesh.types import (
    DeviceAuthStatus,
    DeviceTokenKind,
    EntitlementResource,
    GPUType,
    GraphEdgeType,
    GraphNodeStatus,
    GraphNodeType,
    InstanceCloudProvider,
    InstanceStatus,
    InstanceTypeDeploymentType,
    IntegrationAuthType,
    IntegrationProvider,
    IntegrationScope,
    IntegrationStatus,
    IntegrationType,
    RequirementType,
    KnowledgeLifecycle,
    KnowledgeType,
    MCPServerAuthType,
    NotificationChannel,
    NotificationPriority,
    NotificationStatus,
    NotificationType,
    RefRouteType,
    ResourceType,
    SecretScope,
    SubscriptionInterval,
    SubscriptionStatus,
    ToolCallType,
    ToolParamType,
    ToolType,
    VideoResolution,
)


@pytest.mark.parametrize(
    "enum_cls,member,value",
    [
        (ToolType, "HTTP", "http"),
        (ToolType, "MCP", "mcp"),
        (ToolType, "CALL", "call"),
        (InstanceCloudProvider, "CLOUD_AWS", "aws"),
        (GPUType, "AMD", "amd"),
        (InstanceTypeDeploymentType, "VM", "vm"),
        (VideoResolution, "VIDEO_RES1080P", "1080p"),
    ],
)
def test_enum_member_accessible_with_acronym_name(enum_cls, member, value):
    """Regenerated enums must use readable names (HTTP not H_T_T_P)."""
    assert hasattr(enum_cls, member), f"{enum_cls.__name__}.{member} missing"
    assert getattr(enum_cls, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("OBJECT", "object"),
        ("STRING", "string"),
        ("INTEGER", "integer"),
        ("NUMBER", "number"),
        ("BOOLEAN", "boolean"),
        ("ARRAY", "array"),
        ("NULL", "null"),
    ],
)
def test_tool_param_type_json_schema_values(member, value):
    """ToolParamType is a dedicated enum for JSON Schema parameter types."""
    assert hasattr(ToolParamType, member)
    assert getattr(ToolParamType, member).value == value


def test_tool_call_type_only_function_kind():
    """Parameter schema types moved to ToolParamType; ToolCallType is call kind only."""
    assert ToolCallType.TOOL_TYPE_FUNCTION.value == "function"
    assert not hasattr(ToolCallType, "TOOL_PARAM_TYPE_OBJECT")
    assert not hasattr(ToolCallType, "OBJECT")


@pytest.mark.parametrize(
    "enum_cls,member,value",
    [
        (IntegrationProvider, "GIT_HUB", "github"),
        (IntegrationProvider, "GOOGLE_SA", "google-sa"),
        (IntegrationProvider, "GCP", "gcp"),
        (IntegrationProvider, "MCP", "mcp"),
        (IntegrationAuthType, "O_AUTH", "oauth"),
        (IntegrationAuthType, "API_KEY", "api_key"),
        (IntegrationAuthType, "SERVICE_ACCOUNT", "service_account"),
        (IntegrationAuthType, "WIF", "wif"),
        (IntegrationStatus, "CONNECTED", "connected"),
        (IntegrationStatus, "DISCONNECTED", "disconnected"),
        (IntegrationStatus, "EXPIRED", "expired"),
        (IntegrationStatus, "ERROR", "error"),
    ],
)
def test_integration_enums_preserve_acronym_names(enum_cls, member, value):
    """New integration enums from typegen must stay readable (GIT_HUB not G_I_T_H_U_B)."""
    assert hasattr(enum_cls, member), f"{enum_cls.__name__}.{member} missing"
    assert getattr(enum_cls, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("CREATING", "creating"),
        ("PENDING_PROVIDER", "pending_provider"),
        ("PENDING", "pending"),
        ("ACTIVE", "active"),
        ("ERROR", "error"),
        ("DELETING", "deleting"),
        ("DELETED", "deleted"),
    ],
)
def test_instance_status_lifecycle_values(member, value):
    """Instance provisioning lifecycle enums must include provider/error states."""
    assert hasattr(InstanceStatus, member)
    assert getattr(InstanceStatus, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("UNKNOWN", "unknown"),
        ("JOIN", "join"),
        ("SPLIT", "split"),
        ("EXECUTION", "execution"),
        ("RESOURCE", "resource"),
        ("APPROVAL", "approval"),
        ("CONDITIONAL", "conditional"),
        ("FLOW_NODE", "flow_node"),
        ("TRIGGER", "trigger"),
    ],
)
def test_graph_node_type_workflow_values(member, value):
    """Graph workflow node kinds from typegen must stay stable for API payloads."""
    assert hasattr(GraphNodeType, member)
    assert getattr(GraphNodeType, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("PENDING", "pending"),
        ("READY", "ready"),
        ("RUNNING", "running"),
        ("COMPLETED", "completed"),
        ("FAILED", "failed"),
        ("CANCELLED", "cancelled"),
        ("SKIPPED", "skipped"),
        ("BLOCKED", "blocked"),
    ],
)
def test_graph_node_status_lifecycle_values(member, value):
    """Graph node execution states must match backend workflow semantics."""
    assert hasattr(GraphNodeStatus, member)
    assert getattr(GraphNodeStatus, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("DEPENDENCY", "dependency"),
        ("FLOW", "flow"),
        ("CONDITIONAL", "conditional"),
        ("EXECUTION", "execution"),
        ("PARENT", "parent"),
        ("ANCESTOR", "ancestor"),
        ("DUPLICATE", "duplicate"),
        ("REFERENCES", "references"),
        ("INPUT", "input"),
        ("OUTPUT", "output"),
    ],
)
def test_graph_edge_type_values(member, value):
    """Graph edge kinds must include workflow I/O links from latest typegen regen."""
    assert hasattr(GraphEdgeType, member)
    assert getattr(GraphEdgeType, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("TRIALING", "trialing"),
        ("ACTIVE", "active"),
        ("PAST_DUE", "past_due"),
        ("CANCELED", "canceled"),
        ("PAUSED", "paused"),
    ],
)
def test_subscription_status_billing_lifecycle(member, value):
    """Stripe subscription states must stay stable for billing API payloads."""
    assert hasattr(SubscriptionStatus, member)
    assert getattr(SubscriptionStatus, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("MONTHLY", "monthly"),
        ("YEARLY", "yearly"),
    ],
)
def test_subscription_interval_values(member, value):
    assert hasattr(SubscriptionInterval, member)
    assert getattr(SubscriptionInterval, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("SLACK", "slack"),
        ("DISCORD", "discord"),
        ("TEAMS", "teams"),
        ("TELEGRAM", "telegram"),
    ],
)
def test_integration_type_chat_platform_values(member, value):
    """Chat integration kinds for IntegrationContext must match backend."""
    assert hasattr(IntegrationType, member)
    assert getattr(IntegrationType, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("KNOWLEDGE", "knowledge"),
        ("APP", "app"),
        ("AGENT", "agent"),
    ],
)
def test_resource_type_values(member, value):
    """ResourceRef.type must distinguish knowledge, app, and agent resources."""
    assert hasattr(ResourceType, member)
    assert getattr(ResourceType, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("TEAM", "team"),
        ("INTERNAL", "internal"),
        ("SYSTEM", "system"),
    ],
)
def test_secret_scope_visibility_values(member, value):
    """Secret list filtering depends on stable scope enum values."""
    assert hasattr(SecretScope, member)
    assert getattr(SecretScope, member).value == value


@pytest.mark.parametrize(
    "enum_cls,member,value",
    [
        (MCPServerAuthType, "MCP_SERVER_AUTH_O_AUTH", "oauth"),
        (MCPServerAuthType, "MCP_SERVER_AUTH_API_KEY", "api_key"),
        (MCPServerAuthType, "MCP_SERVER_AUTH_NONE", "none"),
    ],
)
def test_mcp_server_auth_type_acronym_names(enum_cls, member, value):
    """MCP server auth enums must keep readable O_AUTH name from typegen."""
    assert hasattr(enum_cls, member), f"{enum_cls.__name__}.{member} missing"
    assert getattr(enum_cls, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("APP", "app"),
        ("AGENT", "agent"),
        ("SKILL", "skill"),
    ],
)
def test_ref_route_type_values(member, value):
    assert hasattr(RefRouteType, member)
    assert getattr(RefRouteType, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("PENDING", "pending"),
        ("APPROVED", "approved"),
        ("EXPIRED", "expired"),
        ("DENIED", "denied"),
        ("VALID", "valid"),
        ("INVALID", "invalid"),
        ("LOADING", "loading"),
    ],
)
def test_device_auth_status_values(member, value):
    """Device code login polling must recognize all backend status strings."""
    assert hasattr(DeviceAuthStatus, member)
    assert getattr(DeviceAuthStatus, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("SESSION", "session"),
        ("API_KEY", "api_key"),
    ],
)
def test_device_token_kind_values(member, value):
    """Device auth init must distinguish session tokens from legacy API keys."""
    assert hasattr(DeviceTokenKind, member)
    assert getattr(DeviceTokenKind, member).value == value


def test_device_auth_init_request_token_kind():
    """CLIs can request a revocable session token instead of a device API key."""
    from inferencesh.types import DeviceAuthInitRequest

    req: DeviceAuthInitRequest = {"token_kind": DeviceTokenKind.SESSION}
    assert req["token_kind"] == DeviceTokenKind.SESSION


def test_device_auth_poll_response_session_and_api_key():
    """Poll responses return session_token or api_key depending on init token_kind."""
    from inferencesh.types import DeviceAuthPollResponse

    session_resp: DeviceAuthPollResponse = {
        "status": DeviceAuthStatus.VALID,
        "session_token": "sess_cli_abc",
        "team_id": "team_123",
    }
    api_key_resp: DeviceAuthPollResponse = {
        "status": DeviceAuthStatus.VALID,
        "api_key": "inf_key_legacy",
        "team_id": "team_123",
    }

    assert session_resp["session_token"] == "sess_cli_abc"
    assert "api_key" not in session_resp
    assert api_key_resp["api_key"] == "inf_key_legacy"
    assert "session_token" not in api_key_resp


@pytest.mark.parametrize(
    "member,value",
    [
        ("EMAIL", "email"),
        ("SMS", "sms"),
        ("PUSH", "push"),
        ("SLACK", "slack"),
    ],
)
def test_notification_channel_values(member, value):
    assert hasattr(NotificationChannel, member)
    assert getattr(NotificationChannel, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("LOW", "low"),
        ("NORMAL", "normal"),
        ("HIGH", "high"),
        ("CRITICAL", "critical"),
    ],
)
def test_notification_priority_values(member, value):
    assert hasattr(NotificationPriority, member)
    assert getattr(NotificationPriority, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("LOW_BALANCE", "low_balance"),
        ("AUTO_RECHARGE", "auto_recharge"),
        ("PAYMENT_SUCCESS", "payment_success"),
        ("PAYMENT_FAILED", "payment_failed"),
        ("USAGE_SUMMARY", "usage_summary"),
        ("SPENDING_LIMIT", "spending_limit"),
        ("INVOICE", "invoice"),
        ("WELCOME", "welcome"),
        ("WELCOME_AGENTS", "welcome_agents"),
        ("WELCOME_APPS", "welcome_apps"),
        ("WELCOME_FLOWS", "welcome_flows"),
        ("WELCOME_SDK", "welcome_sdk"),
        ("PASSWORD_RESET", "password_reset"),
        ("EMAIL_VERIFY", "email_verify"),
        ("SECURITY_ALERT", "security_alert"),
        ("TASK_COMPLETE", "task_complete"),
        ("TASK_FAILED", "task_failed"),
        ("SYSTEM_ALERT", "system_alert"),
        ("MAINTENANCE", "maintenance"),
        ("TOS_UPDATE", "tos_update"),
        ("SERVICE_NOTICE", "service_notice"),
        ("TEAM_INVITE", "team_invite"),
    ],
)
def test_notification_type_values(member, value):
    """Billing/account/task notification kinds must not drift from backend."""
    assert hasattr(NotificationType, member)
    assert getattr(NotificationType, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("PENDING", "pending"),
        ("PROCESSING", "processing"),
        ("SENT", "sent"),
        ("DELIVERED", "delivered"),
        ("FAILED", "failed"),
        ("BOUNCED", "bounced"),
        ("CANCELLED", "cancelled"),
    ],
)
def test_notification_status_lifecycle_values(member, value):
    assert hasattr(NotificationStatus, member)
    assert getattr(NotificationStatus, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("CONCEPT", "concept"),
        ("SKILL", "skill"),
        ("OBSERVATION", "observation"),
        ("PREFERENCE", "preference"),
        ("REFERENCE", "reference"),
        ("PERSON", "person"),
        ("PROJECT", "project"),
        ("AGENT_CONFIG", "agent-config"),
    ],
)
def test_knowledge_type_values(member, value):
    """Knowledge graph node kinds must stay stable for create/list payloads."""
    assert hasattr(KnowledgeType, member)
    assert getattr(KnowledgeType, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("PERMANENT", "permanent"),
        ("DECAY", "decay"),
    ],
)
def test_knowledge_lifecycle_values(member, value):
    """Knowledge retention policy enums must match backend lifecycle strings."""
    assert hasattr(KnowledgeLifecycle, member)
    assert getattr(KnowledgeLifecycle, member).value == value


def test_instance_type_configuration_gpu_fields():
    """gpu_manufacturer and nvlink support hardware-aware instance selection."""
    from inferencesh.types import InstanceTypeConfiguration

    config: InstanceTypeConfiguration = {
        "gpu_type": "A100",
        "gpu_manufacturer": "nvidia",
        "nvlink": True,
        "num_gpus": 8,
    }
    assert config["gpu_manufacturer"] == "nvidia"
    assert config["nvlink"] is True


def test_instance_type_dto_cloud_logo_url():
    """cloud_logo_url enables provider branding in instance picker UIs."""
    from inferencesh.types import InstanceCloudProvider, InstanceTypeDTO

    dto: InstanceTypeDTO = {
        "cloud": InstanceCloudProvider.CLOUD_AWS,
        "cloud_logo_url": "https://cdn.example.com/aws.svg",
        "region": "us-east-1",
        "shade_instance_type": "gpu.a100.8x",
    }
    assert dto["cloud_logo_url"].endswith("aws.svg")


def test_suggest_types_shape():
    """Suggest endpoint TypedDicts must accept the documented request/response shape."""
    from inferencesh.types import SuggestRequest, SuggestResponse, SuggestResult

    req: SuggestRequest = {
        "query": "flux image",
        "context": "building an image generation pipeline",
        "limit": 5,
        "agent": True,
    }
    result: SuggestResult = {
        "type": "app",
        "name": "flux",
        "description": "Image generation",
        "score": 0.92,
    }
    resp: SuggestResponse = {"query": req["query"], "results": [result]}

    assert req["context"] == "building an image generation pipeline"
    assert resp["results"][0]["name"] == "flux"
    assert resp["results"][0]["score"] == 0.92


def test_device_auth_response_init_shape():
    """Device auth init returns codes and polling URLs for CLI login flows."""
    from inferencesh.types import DeviceAuthResponse

    resp: DeviceAuthResponse = {
        "user_code": "ABCD-1234",
        "device_code": "dev_secret_xyz",
        "poll_url": "https://api.inference.sh/v1/auth/device/poll",
        "approve_url": "https://inference.sh/device?code=ABCD-1234",
        "expires_in": 900,
        "interval": 5,
    }

    assert resp["user_code"] == "ABCD-1234"
    assert resp["expires_in"] == 900
    assert resp["poll_url"].endswith("/poll")


def test_update_integration_scopes_request():
    """OAuth integrations can request additional scopes after initial connect."""
    from inferencesh.types import UpdateIntegrationScopesRequest

    req: UpdateIntegrationScopesRequest = {
        "scopes": [
            "https://www.googleapis.com/auth/drive.readonly",
            "https://www.googleapis.com/auth/calendar.readonly",
        ],
    }

    assert len(req["scopes"]) == 2
    assert req["scopes"][0].endswith("drive.readonly")


def test_integration_dto_google_sa_service_account():
    """Google service-account integrations expose the bound SA email on IntegrationDTO."""
    from inferencesh.types import (
        IntegrationAuthType,
        IntegrationDTO,
        IntegrationProvider,
        IntegrationStatus,
    )

    dto: IntegrationDTO = {
        "provider": IntegrationProvider.GOOGLE_SA,
        "type": IntegrationAuthType.SERVICE_ACCOUNT,
        "auth": IntegrationAuthType.SERVICE_ACCOUNT,
        "status": IntegrationStatus.CONNECTED,
        "display_name": "GCP Production",
        "service_account_email": "sdk-runner@my-project.iam.gserviceaccount.com",
    }

    assert dto["provider"] == IntegrationProvider.GOOGLE_SA
    assert dto["service_account_email"].endswith(".gserviceaccount.com")


@pytest.mark.parametrize(
    "member,value",
    [
        ("SECRET", "secret"),
        ("INTEGRATION", "integration"),
        ("SCOPE", "scope"),
    ],
)
def test_requirement_type_values(member, value):
    """412 requirement errors must distinguish secrets, integrations, and OAuth scopes."""
    assert hasattr(RequirementType, member)
    assert getattr(RequirementType, member).value == value


def test_integration_config_dto_slug():
    """Integration catalog entries are keyed by provider slug (e.g. google-sa)."""
    from inferencesh.types import IntegrationConfigDTO

    config: IntegrationConfigDTO = {
        "slug": "google-sa",
        "provider": IntegrationProvider.GOOGLE_SA,
        "auth": IntegrationAuthType.SERVICE_ACCOUNT,
        "name": "Google Service Account",
        "available": True,
    }
    assert config["slug"] == "google-sa"
    assert config["provider"] == IntegrationProvider.GOOGLE_SA


def test_check_requirements_response_uses_requirement_type():
    """CheckRequirementsResponse errors use RequirementType for structured 412 payloads."""
    from inferencesh.types import CheckRequirementsResponse, RequirementError

    err: RequirementError = {
        "type": RequirementType.SCOPE,
        "key": "drive.readonly",
        "message": "Grant Google Drive read scope",
    }
    resp: CheckRequirementsResponse = {"satisfied": False, "errors": [err]}

    assert resp["errors"][0]["type"] == RequirementType.SCOPE


@pytest.mark.parametrize(
    "member,value",
    [
        ("TEAM", "team"),
        ("PLATFORM", "platform"),
    ],
)
def test_integration_scope_values(member, value):
    """Integration ownership scope must distinguish BYOK team vs platform-managed creds."""
    assert hasattr(IntegrationScope, member)
    assert getattr(IntegrationScope, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("RESOURCE_API_KEYS", "api_keys"),
        ("RESOURCE_CONNECTORS", "connectors"),
        ("RESOURCE_KNOWLEDGE_BASES", "knowledge_bases"),
        ("RESOURCE_STORAGE_MB", "storage_mb"),
        ("RESOURCE_CONCURRENCY", "concurrency"),
        ("RESOURCE_RATE_PER_MIN", "rate_per_min"),
        ("RESOURCE_SEATS", "seats"),
        ("RESOURCE_TRIGGERS", "triggers"),
        ("RESOURCE_RETENTION_DAYS", "retention_days"),
        ("RESOURCE_FEATURE_BYOK", "feature:byok"),
    ],
)
def test_entitlement_resource_values(member, value):
    """Plan entitlement keys must stay stable for billing limit enforcement."""
    assert hasattr(EntitlementResource, member)
    assert getattr(EntitlementResource, member).value == value


def test_integration_requirement_secrets_and_scopes():
    """App manifests declare per-integration secret keys and OAuth scopes."""
    from inferencesh.types import IntegrationRequirement

    req: IntegrationRequirement = {
        "key": "google",
        "description": "Google Workspace",
        "optional": False,
        "secrets": ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"],
        "scopes": ["https://www.googleapis.com/auth/drive.readonly"],
    }

    assert req["key"] == "google"
    assert len(req["secrets"]) == 2
    assert req["scopes"][0].endswith("drive.readonly")


def test_integration_dto_scope_team_vs_platform():
    """IntegrationDTO.scope distinguishes user-owned vs platform-managed connections."""
    from inferencesh.types import IntegrationAuthType, IntegrationDTO, IntegrationStatus

    team: IntegrationDTO = {
        "scope": IntegrationScope.TEAM,
        "provider": IntegrationProvider.GOOGLE,
        "type": IntegrationAuthType.O_AUTH,
        "auth": IntegrationAuthType.O_AUTH,
        "status": IntegrationStatus.CONNECTED,
        "display_name": "My Google",
    }
    platform: IntegrationDTO = {
        "scope": IntegrationScope.PLATFORM,
        "provider": IntegrationProvider.GOOGLE_SA,
        "type": IntegrationAuthType.SERVICE_ACCOUNT,
        "auth": IntegrationAuthType.SERVICE_ACCOUNT,
        "status": IntegrationStatus.CONNECTED,
        "display_name": "Managed GCP",
    }

    assert team["scope"] == IntegrationScope.TEAM
    assert platform["scope"] == IntegrationScope.PLATFORM


def test_plan_dto_limits_use_entitlement_resources():
    """PlanDTO.limits maps EntitlementResource keys to PlanLimit entries."""
    from inferencesh.types import (
        EnforcementMode,
        EntitlementType,
        PlanDTO,
        PlanLimit,
        PlanLimits,
    )

    limits: PlanLimits = {
        EntitlementResource.RESOURCE_TRIGGERS: PlanLimit(
            type=EntitlementType.LIMIT,
            label="Workflow triggers",
            unit="triggers",
            limit=10,
            enforcement=EnforcementMode.ENFORCEMENT_BLOCK,
        ),
        EntitlementResource.RESOURCE_FEATURE_BYOK: PlanLimit(
            type=EntitlementType.BOOLEAN,
            label="Bring your own key",
            enabled=True,
        ),
    }
    plan: PlanDTO = {
        "name": "pro",
        "credits_monthly": 1000,
        "limits": limits,
    }

    assert plan["limits"][EntitlementResource.RESOURCE_TRIGGERS]["limit"] == 10
    assert plan["limits"][EntitlementResource.RESOURCE_FEATURE_BYOK]["enabled"] is True


def test_app_store_listing_dto_concurrency_fields():
    """App store listings expose min/max concurrency limits for worker scaling."""
    from inferencesh.types import AppStoreListingDTO

    listing: AppStoreListingDTO = {
        "id": "listing_flux",
        "allows_private_workers": True,
        "allows_cloud_workers": True,
        "min_concurrency": 1,
        "max_concurrency": 10,
        "max_concurrency_per_team": 5,
        "tags": ["image", "generation"],
    }

    assert listing["min_concurrency"] == 1
    assert listing["max_concurrency"] == 10
    assert listing["max_concurrency_per_team"] == 5


def test_user_metadata_dto_terms_acceptance():
    """User metadata tracks which terms version was accepted and when."""
    from inferencesh.types import UserMetadataDTO

    metadata: UserMetadataDTO = {
        "user_id": "user_abc",
        "completed_onboarding": True,
        "terms_accepted_at": "2026-07-13T12:00:00Z",
        "terms_version": "2026-07-01",
    }

    assert metadata["terms_version"] == "2026-07-01"
    assert metadata["terms_accepted_at"].endswith("Z")


@pytest.mark.parametrize(
    "member,value",
    [
        ("TIER", "tier"),
        ("OVERRIDE", "override"),
        ("WHITELIST", "whitelist"),
        ("TRIAL", "trial"),
    ],
)
def test_entitlement_source_values(member, value):
    """Entitlement source must distinguish plan tier vs override vs trial grants."""
    from inferencesh.types import EntitlementSource

    assert hasattr(EntitlementSource, member)
    assert getattr(EntitlementSource, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("RESERVED", "reserved"),
        ("BUSY", "busy"),
        ("IDLE", "idle"),
        ("INACTIVE", "inactive"),
    ],
)
def test_worker_status_lifecycle_values(member, value):
    """Worker status on EngineDTO/WorkerDTO must stay stable for capacity UIs."""
    from inferencesh.types import WorkerStatus

    assert hasattr(WorkerStatus, member)
    assert getattr(WorkerStatus, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("RUNNING", "running"),
        ("PENDING", "pending"),
        ("DRAINING", "draining"),
        ("DISCONNECTED", "disconnected"),
        ("STOPPING", "stopping"),
        ("STOPPED", "stopped"),
    ],
)
def test_engine_status_lifecycle_values(member, value):
    """EngineStatus values on EngineDTO/EngineSummary must stay stable for dashboard UIs."""
    from inferencesh.types import EngineStatus

    assert hasattr(EngineStatus, member)
    assert getattr(EngineStatus, member).value == value


def test_entitlement_dto_carries_source_and_enforcement():
    """EntitlementDTO ties resource limits to source (tier/override) and enforcement."""
    from inferencesh.types import (
        EntitlementDTO,
        EntitlementSource,
        EntitlementType,
        EnforcementMode,
    )

    ent: EntitlementDTO = {
        "team_id": "team_abc",
        "resource": EntitlementResource.RESOURCE_CONCURRENCY,
        "type": EntitlementType.LIMIT,
        "limit": 5,
        "source": EntitlementSource.TRIAL,
        "enforcement": EnforcementMode.ENFORCEMENT_WARN,
    }

    assert ent["source"] == EntitlementSource.TRIAL
    assert ent["enforcement"] == EnforcementMode.ENFORCEMENT_WARN


@pytest.mark.parametrize(
    "member,value",
    [
        ("ALL", "*"),
        ("AGENTS", "agents"),
        ("APPS", "apps"),
        ("FLOWS_EXECUTE", "flows:execute"),
        ("SECRETS_READ", "secrets:read"),
        ("API_KEYS_WRITE", "apikeys:write"),
        ("SETTINGS_READ", "settings:read"),
    ],
)
def test_scope_permission_values(member, value):
    """API key scopes must stay stable for permission checks and session listings."""
    from inferencesh.types import Scope

    assert hasattr(Scope, member)
    assert getattr(Scope, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("AGENTS", "agents"),
        ("SECRETS", "secrets"),
        ("INTEGRATIONS", "integrations"),
        ("ENGINES", "engines"),
        ("API_KEYS", "apikeys"),
        ("SETTINGS", "settings"),
    ],
)
def test_scope_group_values(member, value):
    """Scope catalog groups must match ScopeDefinition.group values."""
    from inferencesh.types import ScopeGroup

    assert hasattr(ScopeGroup, member)
    assert getattr(ScopeGroup, member).value == value


def test_auth_session_dto_lists_granted_scopes():
    """Auth session listings expose which API key scopes are active on each session."""
    from inferencesh.types import AuthSessionDTO, Scope

    session: AuthSessionDTO = {
        "id": "sess_abc",
        "created_at": "2026-07-13T10:00:00Z",
        "expires_at": "2026-08-13T10:00:00Z",
        "ip": "203.0.113.10",
        "browser": "Chrome",
        "auth_method": "api_key",
        "scopes": [Scope.AGENTS_READ, Scope.FILES_WRITE],
        "current": True,
    }

    assert session["scopes"] == [Scope.AGENTS_READ, Scope.FILES_WRITE]
    assert session["current"] is True


def test_scopes_response_catalog_shape():
    """GET /scopes returns grouped scope definitions and preset bundles."""
    from inferencesh.types import (
        Scope,
        ScopeDefinition,
        ScopeGroup,
        ScopeGroupDefinition,
        ScopePreset,
        ScopesResponse,
    )

    resp: ScopesResponse = {
        "scopes": [
            ScopeDefinition(
                value=Scope.AGENTS_EXECUTE,
                label="Run agents",
                description="Execute agent workflows",
                group=ScopeGroup.AGENTS,
            ),
        ],
        "groups": [
            ScopeGroupDefinition(
                id=ScopeGroup.AGENTS,
                label="Agents",
                description="Agent permissions",
            ),
        ],
        "presets": [
            ScopePreset(
                id="read_run",
                label="Read & run",
                description="Read resources and execute apps/agents",
                scopes=[Scope.APPS_READ, Scope.APPS_EXECUTE],
            ),
        ],
    }

    assert resp["scopes"][0]["value"] == Scope.AGENTS_EXECUTE
    assert resp["groups"][0]["id"] == ScopeGroup.AGENTS
    assert Scope.APPS_EXECUTE in resp["presets"][0]["scopes"]


@pytest.mark.parametrize(
    "member,value",
    [
        ("SETUP_ACTION_ADD_SECRET", "add_secret"),
        ("SETUP_ACTION_CONNECT", "connect"),
        ("SETUP_ACTION_ADD_SCOPES", "add_scopes"),
    ],
)
def test_setup_action_type_values(member, value):
    """412 setup actions must distinguish secrets, connect, and scope expansion."""
    from inferencesh.types import SetupActionType

    assert hasattr(SetupActionType, member)
    assert getattr(SetupActionType, member).value == value


def test_setup_action_typed_dict_shape():
    """SetupAction TypedDict carries provider labels and scope descriptions for UIs."""
    from inferencesh.types import SetupAction, SetupActionType

    action: SetupAction = {
        "type": SetupActionType.SETUP_ACTION_ADD_SCOPES,
        "provider": "google",
        "provider_name": "Google Workspace",
        "scopes": ["https://www.googleapis.com/auth/drive.readonly"],
        "scope_descriptions": {
            "https://www.googleapis.com/auth/drive.readonly": "Read files in Google Drive",
        },
    }

    assert action["type"] == SetupActionType.SETUP_ACTION_ADD_SCOPES
    assert action["provider_name"] == "Google Workspace"
    assert "https://www.googleapis.com/auth/drive.readonly" in action["scope_descriptions"]
