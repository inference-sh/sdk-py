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
    RefRouteMode,
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
        ("SUPERSEDES", "supersedes"),
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


def test_subscription_dto_shape():
    """SubscriptionDTO exposes billing fields without Stripe-internal IDs (d7aa6cb)."""
    from inferencesh.types import SubscriptionDTO

    dto: SubscriptionDTO = {
        "team_id": "team_abc",
        "plan_id": "plan_pro",
        "interval": SubscriptionInterval.MONTHLY,
        "status": SubscriptionStatus.ACTIVE,
        "current_period_start": "2026-01-01T00:00:00Z",
        "current_period_end": "2026-02-01T00:00:00Z",
        "trial_end": None,
        "cancel_at_period_end": False,
        "credits_per_period": 1000,
    }

    assert dto["team_id"] == "team_abc"
    assert dto["status"] == SubscriptionStatus.ACTIVE
    assert dto["credits_per_period"] == 1000
    assert "stripe_subscription_id" not in SubscriptionDTO.__annotations__


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
        ("REWRITE", "rewrite"),
        ("REDIRECT", "redirect"),
    ],
)
def test_ref_route_mode_values(member, value):
    """Ref route mode must distinguish internal rewrite vs external redirect routing."""
    assert hasattr(RefRouteMode, member)
    assert getattr(RefRouteMode, member).value == value


def test_ref_route_dto_mode_field():
    """RefRouteDTO.mode controls whether alias refs rewrite in-place or redirect."""
    from inferencesh.types import RefRouteDTO

    rewrite: RefRouteDTO = {
        "type": RefRouteType.APP,
        "alias_ref": "flux",
        "target_ref": "black-forest-labs/flux-dev",
        "primary": True,
        "mode": RefRouteMode.REWRITE,
        "enabled": True,
    }
    redirect: RefRouteDTO = {
        "type": RefRouteType.AGENT,
        "alias_ref": "support",
        "target_ref": "acme/support-agent",
        "mode": RefRouteMode.REDIRECT,
        "enabled": True,
    }

    assert rewrite["mode"] == RefRouteMode.REWRITE
    assert redirect["mode"] == RefRouteMode.REDIRECT


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


def test_device_auth_init_request_pkce_fields():
    """Device auth init accepts PKCE code_challenge for secure public clients (8e90e52)."""
    from inferencesh.types import DeviceAuthInitRequest

    req: DeviceAuthInitRequest = {
        "token_kind": DeviceTokenKind.SESSION,
        "code_challenge": "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw",
        "code_challenge_method": "S256",
    }

    assert req["code_challenge_method"] == "S256"
    assert len(req["code_challenge"]) > 20


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
        ("DATA_EXPORT", "data_export"),
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
    """Suggest endpoint TypedDicts must accept tag/command on results (fb75385 regen)."""
    from inferencesh.types import SuggestRequest, SuggestResponse, SuggestResult

    req: SuggestRequest = {
        "query": "flux image",
        "context": "building an image generation pipeline",
        "scope": ["team", "public"],
        "limit": 5,
        "agent": True,
    }
    result: SuggestResult = {
        "type": "app",
        "tag": "image-generation",
        "name": "flux",
        "description": "Image generation",
        "command": "inference run flux",
        "score": 0.92,
    }
    resp: SuggestResponse = {"query": req["query"], "results": [result]}

    assert req["context"] == "building an image generation pipeline"
    assert resp["results"][0]["tag"] == "image-generation"
    assert req["scope"] == ["team", "public"]
    assert resp["results"][0]["name"] == "flux"
    assert resp["results"][0]["command"] == "inference run flux"
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
        ("RESOURCE_FEATURE_SEEDANCE", "feature:seedance"),
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
        PlanType,
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
        "plan_type": PlanType.BASE,
        "credits_monthly": 1000,
        "limits": limits,
    }

    assert plan["plan_type"] == PlanType.BASE
    assert plan["limits"][EntitlementResource.RESOURCE_TRIGGERS]["limit"] == 10
    assert plan["limits"][EntitlementResource.RESOURCE_FEATURE_BYOK]["enabled"] is True


def test_plan_dto_required_plan_ids_prerequisite_chain():
    """Add-on plans declare prerequisite base plan IDs for upgrade eligibility checks."""
    from inferencesh.types import PlanDTO

    base: PlanDTO = {
        "name": "pro",
        "credits_monthly": 1000,
        "required_plan_ids": [],
    }
    addon: PlanDTO = {
        "name": "extra_concurrency",
        "credits_monthly": 0,
        "required_plan_ids": ["plan_pro", "plan_team"],
    }

    assert base["required_plan_ids"] == []
    assert addon["required_plan_ids"] == ["plan_pro", "plan_team"]


def test_entitlement_error_meta_limit_exceeded_shape():
    """Entitlement 402/403 errors expose usage, limits, and add-on upgrade hints."""
    from inferencesh.types import EntitlementErrorMeta

    meta: EntitlementErrorMeta = {
        "resource": EntitlementResource.RESOURCE_CONCURRENCY,
        "resource_label": "Concurrent runs",
        "limit": 5,
        "current": 5,
        "upgrade_available": True,
        "addon_plan_id": "plan_extra_concurrency",
        "addon_plan_name": "Extra Concurrency",
        "addon_plan_price": 2900,
    }

    assert meta["resource"] == EntitlementResource.RESOURCE_CONCURRENCY
    assert meta["limit"] == meta["current"] == 5
    assert meta["upgrade_available"] is True
    assert meta["addon_plan_price"] == 2900


def test_entitlement_error_meta_feature_gate_shape():
    """Feature-gate entitlement errors may omit numeric limits but still suggest upgrades."""
    from inferencesh.types import EntitlementErrorMeta

    meta: EntitlementErrorMeta = {
        "resource": EntitlementResource.RESOURCE_FEATURE_SEEDANCE,
        "resource_label": "Seedance video",
        "upgrade_available": True,
        "addon_plan_id": "plan_pro",
        "addon_plan_name": "Pro",
    }

    assert meta["resource"] == EntitlementResource.RESOURCE_FEATURE_SEEDANCE
    assert meta["upgrade_available"] is True
    assert "limit" not in meta


def test_plan_dto_required_plan_names_prerequisite_chain():
    """Add-on plans expose human-readable prerequisite plan names for upgrade UIs."""
    from inferencesh.types import PlanDTO

    base: PlanDTO = {
        "name": "pro",
        "credits_monthly": 1000,
        "required_plan_names": [],
    }
    addon: PlanDTO = {
        "name": "extra_concurrency",
        "credits_monthly": 0,
        "required_plan_ids": ["plan_pro", "plan_team"],
        "required_plan_names": ["Pro", "Team"],
    }

    assert base["required_plan_names"] == []
    assert addon["required_plan_names"] == ["Pro", "Team"]


def test_plan_dto_stackable_flag():
    """PlanDTO.stackable distinguishes base tiers from add-ons purchasable alongside them."""
    from inferencesh.types import PlanDTO

    base: PlanDTO = {
        "name": "pro",
        "credits_monthly": 1000,
        "stackable": False,
        "required_plan_ids": [],
    }
    addon: PlanDTO = {
        "name": "extra_concurrency",
        "credits_monthly": 0,
        "stackable": True,
        "required_plan_ids": ["plan_pro"],
    }

    assert base["stackable"] is False
    assert addon["stackable"] is True


def test_plan_dto_active_version_shape():
    """Plan catalog entries embed active pricing via PlanVersionDTO (06ecea2/eceba3c regen)."""
    from inferencesh.types import PlanDTO, PlanType, PlanVersionDTO

    active_version: PlanVersionDTO = {
        "plan_id": "plan_pro",
        "amount_monthly": 2900,
        "amount_yearly": 29000,
        "provider_price_id_monthly": "price_monthly_abc",
        "provider_price_id_yearly": "price_yearly_abc",
        "credits_monthly": 1000,
        "limits": {},
        "active": True,
    }
    plan: PlanDTO = {
        "name": "pro",
        "plan_type": PlanType.BASE,
        "credits_monthly": 1000,
        "active_version": active_version,
    }

    assert plan["active_version"]["amount_monthly"] == 2900
    assert plan["active_version"]["provider_price_id_yearly"] == "price_yearly_abc"


def test_plan_dto_dropped_flat_pricing_fields():
    """PlanDTO no longer carries top-level monthly/yearly prices after PlanVersionDTO migration."""
    from inferencesh.types import PlanDTO

    annotations = PlanDTO.__annotations__
    assert "active_version" in annotations
    assert "price_monthly" not in annotations
    assert "price_yearly" not in annotations
    assert "provider_price_id_monthly" not in annotations
    assert "prices" not in annotations


def test_plan_version_dto_monthly_yearly_amounts():
    """PlanVersionDTO exposes separate monthly/yearly amounts and provider price IDs."""
    from inferencesh.types import PlanVersionDTO

    version: PlanVersionDTO = {
        "plan_id": "plan_team",
        "amount_monthly": 9900,
        "amount_yearly": 99000,
        "provider_price_id_monthly": "price_m",
        "provider_price_id_yearly": "price_y",
        "credits_monthly": 5000,
        "limits": {},
        "active": True,
    }

    assert version["amount_monthly"] == 9900
    assert version["amount_yearly"] == 99000


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
        "required_feature": "gpu_workers",
        "tags": ["image", "generation"],
    }

    assert listing["required_feature"] == "gpu_workers"
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
        ("ADDON", "addon"),
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
        "source": EntitlementSource.ADDON,
        "enforcement": EnforcementMode.ENFORCEMENT_WARN,
        "team_plan_id": "plan_addon_extra_concurrency",
    }

    assert ent["source"] == EntitlementSource.ADDON
    assert ent["team_plan_id"] == "plan_addon_extra_concurrency"
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
                id="read_only",
                label="Read only",
                description="Read resources without write or execute access",
                scopes=[Scope.APPS_READ, Scope.AGENTS_READ],
                summary=["View apps and agents"],
                hidden=False,
            ),
            ScopePreset(
                id="standard",
                label="Standard",
                description="Read and execute apps/agents; secrets excluded",
                scopes=[Scope.APPS_READ, Scope.APPS_EXECUTE, Scope.AGENTS_EXECUTE],
                summary=["Read & run apps", "Read & run agents"],
                hidden=False,
            ),
            ScopePreset(
                id="admin_full",
                label="Full access",
                description="All scopes including admin-only permissions",
                scopes=[Scope.API_KEYS_WRITE, Scope.SECRETS_WRITE],
                summary=["Full platform access"],
                hidden=True,
            ),
        ],
    }

    assert resp["scopes"][0]["value"] == Scope.AGENTS_EXECUTE
    assert resp["groups"][0]["id"] == ScopeGroup.AGENTS
    assert Scope.APPS_READ in resp["presets"][0]["scopes"]
    assert resp["presets"][0]["summary"] == ["View apps and agents"]
    assert resp["presets"][0]["hidden"] is False
    assert resp["presets"][1]["id"] == "standard"
    assert Scope.SECRETS_READ not in resp["presets"][1]["scopes"]
    assert resp["presets"][2]["hidden"] is True


def test_estimate_cost_request_shape():
    """POST /store/apps/{appId}/estimate accepts task input and optional function."""
    from inferencesh.types import EstimateCostRequest

    req: EstimateCostRequest = {
        "input": {"prompt": "a sunset over mountains", "steps": 30},
        "function": "generate",
    }

    assert req["function"] == "generate"
    assert req["input"]["steps"] == 30


@pytest.mark.parametrize(
    "confidence,fields",
    [
        (
            "exact",
            {"microcents": 250000, "pricing_description": "$0.25 per run"},
        ),
        (
            "range",
            {
                "min": 100000,
                "max": 500000,
                "pricing_description": "$0.10–$0.50 depending on output size",
            },
        ),
        (
            "unknown",
            {
                "depends_on": ["output_tokens", "duration_seconds"],
                "pricing_description": "Cost depends on model output",
            },
        ),
    ],
)
def test_estimate_cost_response_confidence_shapes(confidence, fields):
    """Estimate responses vary by confidence: exact microcents, range bounds, or unknown."""
    from inferencesh.types import EstimateCostResponse

    resp: EstimateCostResponse = {"confidence": confidence, **fields}

    assert resp["confidence"] == confidence
    assert resp["pricing_description"]
    if confidence == "exact":
        assert resp["microcents"] == 250000
        assert "min" not in resp
    elif confidence == "range":
        assert resp["min"] == 100000
        assert resp["max"] == 500000
    else:
        assert resp["depends_on"] == ["output_tokens", "duration_seconds"]


def test_app_pricing_estimate_fields():
    """AppPricing.estimate enables pre-execution cost estimation; estimable flags input-only fees."""
    from inferencesh.types import AppPricing

    estimable: AppPricing = {
        "prices": {"gpu_seconds": 1000},
        "total_expression": "task_inputs.steps * prices.gpu_seconds",
        "estimable": True,
        "description": "Per-step GPU pricing",
        "description_rendered": "$0.001 per step",
    }
    with_estimate: AppPricing = {
        "prices": {"base": 50000},
        "total_expression": "output_tokens * prices.base",
        "estimate": '{"min": prices.base, "max": prices.base * 10}',
        "estimable": False,
        "description": "Output-dependent token pricing",
        "description_rendered": "From $0.05 depending on output size",
    }

    assert estimable["estimable"] is True
    assert estimable["description_rendered"] == "$0.001 per step"
    assert "estimate" not in estimable
    assert with_estimate["estimable"] is False
    assert with_estimate["description_rendered"].startswith("From $0.05")
    assert "min" in with_estimate["estimate"]


def test_estimate_cost_response_estimate_error_field():
    """Estimate responses surface CEL failures when an estimate expression cannot evaluate."""
    from inferencesh.types import EstimateCostResponse

    resp: EstimateCostResponse = {
        "confidence": "unknown",
        "estimate_error": "CEL evaluation failed: undefined variable 'output_tokens'",
        "depends_on": ["output_tokens"],
        "pricing_description": "Cost depends on model output",
    }

    assert resp["estimate_error"].startswith("CEL evaluation failed")
    assert "output_tokens" in resp["depends_on"]


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


@pytest.mark.parametrize(
    "member,value",
    [
        ("IMAGE", "image"),
        ("VIDEO", "video"),
        ("AUDIO", "audio"),
        ("TEXT", "text"),
        ("CHAT", "chat"),
        ("_3D", "3d"),
        ("OTHER", "other"),
        ("FLOW", "flow"),
    ],
)
def test_app_category_values(member, value):
    """App store categories must stay stable; _3D guards gotypegen digit-prefix naming."""
    from inferencesh.types import AppCategory

    assert hasattr(AppCategory, member)
    assert getattr(AppCategory, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("PRIVATE", "private"),
        ("PUBLIC", "public"),
        ("UNLISTED", "unlisted"),
    ],
)
def test_visibility_values(member, value):
    """Visibility controls public/private app and resource access."""
    from inferencesh.types import Visibility

    assert hasattr(Visibility, member)
    assert getattr(Visibility, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("BUSY", "busy"),
        ("IDLE", "idle"),
        ("AWAITING_INPUT", "awaiting_input"),
        ("COMPLETED", "completed"),
    ],
)
def test_chat_status_lifecycle_values(member, value):
    """ChatDTO.status drives agent chat UI state and stream handling."""
    from inferencesh.types import ChatStatus

    assert hasattr(ChatStatus, member)
    assert getattr(ChatStatus, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("SYSTEM", "system"),
        ("USER", "user"),
        ("ASSISTANT", "assistant"),
        ("TOOL", "tool"),
    ],
)
def test_chat_message_role_values(member, value):
    """Chat message roles must match OpenAI-compatible message builders."""
    from inferencesh.types import ChatMessageRole

    assert hasattr(ChatMessageRole, member)
    assert getattr(ChatMessageRole, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("PENDING", "pending"),
        ("READY", "ready"),
        ("FAILED", "failed"),
        ("CANCELLED", "cancelled"),
    ],
)
def test_chat_message_status_lifecycle_values(member, value):
    """Message readiness checks depend on stable ChatMessageStatus values."""
    from inferencesh.types import ChatMessageStatus

    assert hasattr(ChatMessageStatus, member)
    assert getattr(ChatMessageStatus, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("TEXT", "text"),
        ("REASONING", "reasoning"),
        ("IMAGE", "image"),
        ("FILE", "file"),
        ("TOOL", "tool"),
    ],
)
def test_chat_message_content_type_values(member, value):
    """Multimodal chat payloads use content-type discriminators."""
    from inferencesh.types import ChatMessageContentType

    assert hasattr(ChatMessageContentType, member)
    assert getattr(ChatMessageContentType, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("PENDING", "pending"),
        ("IN_PROGRESS", "in_progress"),
        ("COMPLETED", "completed"),
        ("CANCELLED", "cancelled"),
    ],
)
def test_plan_step_status_lifecycle_values(member, value):
    """Agent plan steps expose lifecycle status for progress UIs."""
    from inferencesh.types import PlanStepStatus

    assert hasattr(PlanStepStatus, member)
    assert getattr(PlanStepStatus, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("ANY", "any"),
        ("NONE", "none"),
        ("INTEL", "intel"),
        ("NVIDIA", "nvidia"),
        ("AMD", "amd"),
        ("APPLE", "apple"),
    ],
)
def test_gpu_type_values(member, value):
    """Worker GPU config and instance types reference stable GPUType tokens."""
    from inferencesh.types import GPUType

    assert hasattr(GPUType, member)
    assert getattr(GPUType, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("UNKNOWN", 0),
        ("PENDING", 1),
        ("RUNNING", 2),
        ("COMPLETED", 3),
        ("FAILED", 4),
        ("CANCELLED", 5),
    ],
)
def test_flow_run_status_lifecycle_values(member, value):
    """FlowRunDTO.status is an IntEnum; values must not shift across API versions."""
    from inferencesh.types import FlowRunStatus

    assert hasattr(FlowRunStatus, member)
    assert getattr(FlowRunStatus, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("UNKNOWN", 0),
        ("DRAFT", 1),
        ("PUBLISHED", 2),
        ("ARCHIVED", 3),
    ],
)
def test_page_status_lifecycle_values(member, value):
    """PageDTO.status is an IntEnum; CMS publish workflow depends on stable values."""
    from inferencesh.types import PageStatus

    assert hasattr(PageStatus, member)
    assert getattr(PageStatus, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("DOC", "doc"),
        ("BLOG", "blog"),
        ("PAGE", "page"),
    ],
)
def test_page_type_values(member, value):
    """Page listings discriminate doc/blog/page content kinds."""
    from inferencesh.types import PageType

    assert hasattr(PageType, member)
    assert getattr(PageType, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("AGENT", "agent"),
        ("APP", "app"),
        ("FLOW", "flow"),
        ("OTHER", "other"),
    ],
)
def test_project_type_values(member, value):
    """ProjectDTO.type groups agents, apps, and flows in the workspace UI."""
    from inferencesh.types import ProjectType

    assert hasattr(ProjectType, member)
    assert getattr(ProjectType, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("PENDING", "pending"),
        ("IN_PROGRESS", "in_progress"),
        ("AWAITING_INPUT", "awaiting_input"),
        ("AWAITING_APPROVAL", "awaiting_approval"),
        ("COMPLETED", "completed"),
        ("FAILED", "failed"),
        ("CANCELLED", "cancelled"),
    ],
)
def test_tool_invocation_status_lifecycle_values(member, value):
    """Agent client-tool loops gate on ToolInvocationStatus.AWAITING_INPUT."""
    from inferencesh.types import ToolInvocationStatus

    assert hasattr(ToolInvocationStatus, member)
    assert getattr(ToolInvocationStatus, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("PENDING", "pending"),
        ("ACCEPTED", "accepted"),
        ("DECLINED", "declined"),
        ("EXPIRED", "expired"),
        ("REVOKED", "revoked"),
    ],
)
def test_team_invite_status_lifecycle_values(member, value):
    """Team invite acceptance flows gate on TeamInviteStatus."""
    from inferencesh.types import TeamInviteStatus

    assert hasattr(TeamInviteStatus, member)
    assert getattr(TeamInviteStatus, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("OWNER", "owner"),
        ("ADMIN", "admin"),
        ("MEMBER", "member"),
    ],
)
def test_team_role_values(member, value):
    """TeamInviteDTO.role and membership APIs use TeamRole tokens."""
    from inferencesh.types import TeamRole

    assert hasattr(TeamRole, member)
    assert getattr(TeamRole, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("PERSONAL", "personal"),
        ("TEAM", "team"),
        ("SYSTEM", "system"),
    ],
)
def test_team_type_values(member, value):
    """TeamRelationDTO distinguishes personal vs shared workspaces."""
    from inferencesh.types import TeamType

    assert hasattr(TeamType, member)
    assert getattr(TeamType, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("ACTIVE", "active"),
        ("ENDED", "ended"),
        ("EXPIRED", "expired"),
    ],
)
def test_app_session_status_lifecycle_values(member, value):
    """AppSessionDTO.status tracks warm worker session lifecycle."""
    from inferencesh.types import AppSessionStatus

    assert hasattr(AppSessionStatus, member)
    assert getattr(AppSessionStatus, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("ACTIVE", "active"),
        ("SUSPENDED", "suspended"),
        ("TERMINATED", "terminated"),
    ],
)
def test_team_status_lifecycle_values(member, value):
    """Suspended teams must not shift status tokens across API versions."""
    from inferencesh.types import TeamStatus

    assert hasattr(TeamStatus, member)
    assert getattr(TeamStatus, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("OP_EQUAL", "eq"),
        ("OP_NOT_EQUAL", "neq"),
        ("OP_IN", "in"),
        ("OP_NOT_IN", "not_in"),
        ("OP_GREATER", "gt"),
        ("OP_GREATER_EQUAL", "gte"),
        ("OP_LESS", "lt"),
        ("OP_LESS_EQUAL", "lte"),
        ("OP_LIKE", "like"),
        ("OP_I_LIKE", "ilike"),
        ("OP_CONTAINS", "contains"),
        ("OP_NOT_CONTAINS", "not_contains"),
        ("OP_IS_NULL", "is_null"),
        ("OP_IS_NOT_NULL", "is_not_null"),
        ("OP_IS_EMPTY", "is_empty"),
        ("OP_IS_NOT_EMPTY", "is_not_empty"),
    ],
)
def test_filter_operator_values(member, value):
    """Cursor list filters serialize operator tokens that must stay stable."""
    from inferencesh.types import FilterOperator

    assert hasattr(FilterOperator, member)
    assert getattr(FilterOperator, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("CONTENT_SAFE", "safe"),
        ("CONTENT_SEXUAL_SUGGESTIVE", "sexual_suggestive"),
        ("CONTENT_SEXUAL_EXPLICIT", "sexual_explicit"),
        ("CONTENT_VIOLENCE_NON_GRAPHIC", "violence_non_graphic"),
        ("CONTENT_VIOLENCE_GRAPHIC", "violence_graphic"),
        ("CONTENT_GORE", "gore"),
        ("CONTENT_UNRATED", "unrated"),
    ],
)
def test_content_rating_values(member, value):
    """FileDTO.rating uses ContentRating; CONTENT_ prefix guards gotypegen naming."""
    from inferencesh.types import ContentRating

    assert hasattr(ContentRating, member)
    assert getattr(ContentRating, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("PRIVATE", "private"),
        ("CLOUD", "cloud"),
    ],
)
def test_usage_event_resource_tier_values(member, value):
    """Usage billing events discriminate private vs cloud resource tiers."""
    from inferencesh.types import UsageEventResourceTier

    assert hasattr(UsageEventResourceTier, member)
    assert getattr(UsageEventResourceTier, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("PRIVATE", "private"),
        ("CLOUD", "cloud"),
        ("PRIVATE_FIRST", "private_first"),
    ],
)
def test_infra_values(member, value):
    """Task routing uses Infra to prefer private workers vs cloud."""
    from inferencesh.types import Infra

    assert hasattr(Infra, member)
    assert getattr(Infra, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("BUILD", 0),
        ("RUN", 1),
        ("SERVE", 2),
        ("SETUP", 3),
        ("TASK", 4),
    ],
)
def test_task_log_type_values(member, value):
    """Task log streams use TaskLogType IntEnum discriminators."""
    from inferencesh.types import TaskLogType

    assert hasattr(TaskLogType, member)
    assert getattr(TaskLogType, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("GUEST", "guest"),
        ("USER", "user"),
        ("ADMIN", "admin"),
        ("SYSTEM", "system"),
    ],
)
def test_role_values(member, value):
    """Permission checks reference stable Role tokens."""
    from inferencesh.types import Role

    assert hasattr(Role, member)
    assert getattr(Role, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("BOOLEAN", "boolean"),
        ("LIMIT", "limit"),
    ],
)
def test_entitlement_type_values(member, value):
    """Plan limits vs feature gates use EntitlementType discriminators."""
    from inferencesh.types import EntitlementType

    assert hasattr(EntitlementType, member)
    assert getattr(EntitlementType, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("ENFORCEMENT_BLOCK", "block"),
        ("ENFORCEMENT_WARN", "warn"),
    ],
)
def test_enforcement_mode_values(member, value):
    """Entitlement enforcement mode controls block vs warn behavior."""
    from inferencesh.types import EnforcementMode

    assert hasattr(EnforcementMode, member)
    assert getattr(EnforcementMode, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("APP", "app"),
        ("AGENT", "agent"),
        ("HOOK", "hook"),
        ("HTTP", "http"),
        ("CALL", "call"),
        ("MCP", "mcp"),
        ("CLIENT", "client"),
        ("INTERNAL", "internal"),
    ],
)
def test_tool_type_lifecycle_values(member, value):
    """Tool builders and DTOs discriminate all ToolType kinds."""
    from inferencesh.types import ToolType

    assert hasattr(ToolType, member)
    assert getattr(ToolType, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("TEXT", "text"),
        ("IMAGE", "image"),
        ("VIDEO", "video"),
        ("AUDIO", "audio"),
        ("RAW", "raw"),
    ],
)
def test_meta_item_type_values(member, value):
    """Output metadata discriminates media kinds via MetaItemType."""
    from inferencesh.types import MetaItemType

    assert hasattr(MetaItemType, member)
    assert getattr(MetaItemType, member).value == value


def test_chat_dto_carries_status():
    """Chat listings expose ChatStatus for stream and UI state."""
    from inferencesh.types import ChatDTO, ChatStatus

    chat: ChatDTO = {
        "id": "chat_abc",
        "status": ChatStatus.AWAITING_INPUT,
        "children": [],
    }

    assert chat["status"] == ChatStatus.AWAITING_INPUT


def test_flow_run_dto_carries_int_status():
    """Flow run records use FlowRunStatus IntEnum values."""
    from inferencesh.types import FlowRunDTO, FlowRunStatus

    run: FlowRunDTO = {
        "flow_id": "flow_abc",
        "status": FlowRunStatus.RUNNING,
        "fail_on_error": True,
        "node_tasks": {},
    }

    assert run["status"] == FlowRunStatus.RUNNING
    assert run["status"].value == 2


@pytest.mark.parametrize(
    "member,value",
    [
        ("ACTIVE", "active"),
        ("MAINTENANCE", "maintenance"),
        ("DEPRECATED", "deprecated"),
        ("RETIRED", "retired"),
    ],
)
def test_app_status_values(member, value):
    """AppStatus lifecycle must stay stable for catalog filtering and deprecation banners."""
    from inferencesh.types import AppStatus

    assert hasattr(AppStatus, member)
    assert getattr(AppStatus, member).value == value


def test_app_dto_carries_status():
    """AppDTO exposes operational status for maintenance/deprecation messaging."""
    from inferencesh.types import AppCategory, AppDTO, AppStatus

    app: AppDTO = {
        "namespace": "acme",
        "name": "flux",
        "description": "Image generation",
        "category": AppCategory.IMAGE,
        "version_id": "ver_abc",
        "status": AppStatus.MAINTENANCE,
        "status_message": "Scheduled maintenance until 18:00 UTC",
        "status_changed_at": "2026-07-26T12:00:00Z",
    }

    assert app["status"] == AppStatus.MAINTENANCE
    assert "maintenance" in app["status_message"].lower()


def test_app_session_dto_carries_status():
    """App session records expose lifecycle status for warm workers."""
    from inferencesh.types import AppSessionDTO, AppSessionStatus

    session: AppSessionDTO = {
        "id": "sess_abc",
        "app_id": "app_xyz",
        "status": AppSessionStatus.ACTIVE,
        "call_count": 3,
    }

    assert session["status"] == AppSessionStatus.ACTIVE


@pytest.mark.parametrize(
    "member,value",
    [
        ("MARKDOWN", "markdown"),
        ("IMAGE", "image"),
        ("BADGE", "badge"),
        ("BUTTON", "button"),
        ("INPUT", "input"),
        ("SELECT", "select"),
        ("CHECKBOX", "checkbox"),
        ("ROW", "row"),
        ("COL", "col"),
        ("BOX", "box"),
        ("SPACER", "spacer"),
        ("DIVIDER", "divider"),
        ("FORM", "form"),
        ("TITLE", "title"),
        ("CAPTION", "caption"),
        ("LABEL", "label"),
        ("TEXTAREA", "textarea"),
        ("RADIO_GROUP", "radio-group"),
        ("DATE_PICKER", "date-picker"),
        ("ICON", "icon"),
        ("CHART", "chart"),
        ("TRANSITION", "transition"),
        ("PLAN_LIST", "plan-list"),
        ("KEY_VALUE", "key-value"),
        ("STATUS_BADGE", "status-badge"),
    ],
)
def test_widget_node_type_values(member, value):
    """Agent widget trees serialize WidgetNodeType discriminators."""
    from inferencesh.types import WidgetNodeType

    assert hasattr(WidgetNodeType, member)
    assert getattr(WidgetNodeType, member).value == value


def test_page_dto_carries_status_and_type():
    """CMS pages expose PageStatus and PageType for publish workflows."""
    from inferencesh.types import PageDTO, PageStatus, PageType

    page: PageDTO = {
        "title": "Getting started",
        "slug": "getting-started",
        "status": PageStatus.PUBLISHED,
        "type": PageType.DOC,
    }

    assert page["status"] == PageStatus.PUBLISHED
    assert page["type"] == PageType.DOC


def test_project_dto_carries_type():
    """Project listings group resources by ProjectType."""
    from inferencesh.types import ProjectDTO, ProjectType

    project: ProjectDTO = {
        "name": "Image pipeline",
        "type": ProjectType.FLOW,
    }

    assert project["type"] == ProjectType.FLOW


def test_team_invite_dto_carries_status_and_role():
    """Team invite records expose status and role for acceptance UIs."""
    from inferencesh.types import TeamInviteDTO, TeamInviteStatus, TeamRole

    invite: TeamInviteDTO = {
        "email": "dev@example.com",
        "role": TeamRole.MEMBER,
        "status": TeamInviteStatus.PENDING,
    }

    assert invite["role"] == TeamRole.MEMBER
    assert invite["status"] == TeamInviteStatus.PENDING


def test_file_dto_carries_content_rating():
    """Uploaded files expose ContentRating for moderation filters."""
    from inferencesh.types import ContentRating, FileDTO

    file_rec: FileDTO = {
        "filename": "output.png",
        "rating": ContentRating.CONTENT_SAFE,
    }

    assert file_rec["rating"] == ContentRating.CONTENT_SAFE


def test_usage_event_dto_carries_tier():
    """Usage events record private vs cloud tier for billing breakdowns."""
    from inferencesh.types import UsageEventDTO, UsageEventResourceTier

    event: UsageEventDTO = {
        "reference_id": "task_abc",
        "tier": UsageEventResourceTier.CLOUD,
        "quantity": 120,
    }

    assert event["tier"] == UsageEventResourceTier.CLOUD


def test_filter_typed_dict_shape():
    """Cursor list filters serialize FilterOperator tokens on Filter entries."""
    from inferencesh.types import Filter, FilterOperator

    filt: Filter = {
        "field": "status",
        "operator": FilterOperator.OP_EQUAL,
        "value": "active",
    }

    assert filt["operator"] == FilterOperator.OP_EQUAL


def test_cursor_list_request_filters_shape():
    """CursorListRequest bundles search, filters, and sort for list APIs."""
    from inferencesh.types import CursorListRequest, Filter, FilterOperator, SearchRequest, SortOrder

    req: CursorListRequest = {
        "limit": 25,
        "search": SearchRequest(term="flux", exact=False),
        "filters": [
            Filter(field="type", operator=FilterOperator.OP_IN, value=["app", "agent"]),
        ],
        "sort": [SortOrder(field="updated_at", dir="desc")],
    }

    assert req["filters"][0]["operator"] == FilterOperator.OP_IN
    assert req["search"]["term"] == "flux"


def test_engine_dto_carries_engine_version():
    """EngineDTO exposes engine_version for dashboard version checks (bd4cfaa regen)."""
    from inferencesh.types import EngineDTO, EngineStatus

    engine: EngineDTO = {
        "name": "worker-pool-1",
        "api_url": "https://engine.example.com",
        "status": EngineStatus.RUNNING,
        "engine_version": "1.2.3",
    }

    assert engine["engine_version"] == "1.2.3"
    assert engine["status"] == EngineStatus.RUNNING


@pytest.mark.parametrize(
    "member,value",
    [
        ("BASE", "base"),
        ("ADDON", "addon"),
    ],
)
def test_plan_type_values(member, value):
    """PlanType must distinguish base subscriptions from purchasable add-on plans."""
    from inferencesh.types import PlanType

    assert hasattr(PlanType, member)
    assert getattr(PlanType, member).value == value


def test_plan_dto_addon_plan_type():
    """Add-on plans are self-serve extras layered on top of a base subscription."""
    from inferencesh.types import PlanDTO, PlanType

    addon: PlanDTO = {
        "name": "extra_concurrency",
        "plan_type": PlanType.ADDON,
        "self_serve": True,
        "active": True,
        "credits_monthly": 0,
    }

    assert addon["plan_type"] == PlanType.ADDON
    assert addon["self_serve"] is True


def test_skill_dto_usage_metrics():
    """Skill catalog listings expose uses/installs for popularity sorting."""
    from inferencesh.types import SkillDTO

    skill: SkillDTO = {
        "name": "code-review",
        "uses": 1200,
        "installs": 340,
        "version_id": "ver_xyz",
    }

    assert skill["uses"] >= skill["installs"]


def test_knowledge_dto_usage_metrics():
    """Knowledge catalog listings expose uses/installs for discovery rankings."""
    from inferencesh.types import KnowledgeDTO, KnowledgeLifecycle, KnowledgeType

    knowledge: KnowledgeDTO = {
        "name": "onboarding-docs",
        "type": KnowledgeType.CONCEPT,
        "lifecycle": KnowledgeLifecycle.PERMANENT,
        "uses": 50,
        "installs": 12,
        "version_id": "ver_abc",
    }

    assert knowledge["uses"] == 50
    assert knowledge["installs"] == 12


def test_knowledge_version_scope_fields():
    """Knowledge versions can scope content to team namespaces or shared catalogs."""
    from inferencesh.types import KnowledgeVersionDTO, KnowledgeVersionInput

    version_input: KnowledgeVersionInput = {
        "description": "Team onboarding docs",
        "scope": ["team:acme", "catalog:internal"],
        "tags": ["onboarding"],
    }
    version: KnowledgeVersionDTO = {
        "knowledge_id": "know_abc",
        "description": version_input["description"],
        "scope": version_input["scope"],
        "tags": version_input["tags"],
        "content_hash": "sha256:abc123",
    }

    assert version_input["scope"] == ["team:acme", "catalog:internal"]
    assert version["scope"] == version_input["scope"]


@pytest.mark.parametrize(
    "member,value",
    [
        ("ACCEPT", "accept"),
        ("DECLINE", "decline"),
        ("CANCEL", "cancel"),
    ],
)
def test_elicit_action_values(member, value):
    """MCP elicitation responses must distinguish accept, decline, and cancel."""
    from inferencesh.types import ElicitAction

    assert hasattr(ElicitAction, member)
    assert getattr(ElicitAction, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("COMPLETE", "complete"),
        ("INPUT_REQUIRED", "input_required"),
    ],
)
def test_result_type_values(member, value):
    """ToolCallResponse.resultType must not conflate MRTR input_required with complete."""
    from inferencesh.types import ResultType

    assert hasattr(ResultType, member)
    assert getattr(ResultType, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("PUBLIC", "public"),
        ("PRIVATE", "private"),
    ],
)
def test_cache_scope_values(member, value):
    """ResultMeta.cacheScope controls cross-auth caching semantics."""
    from inferencesh.types import CacheScope

    assert hasattr(CacheScope, member)
    assert getattr(CacheScope, member).value == value


@pytest.mark.parametrize(
    "member,value",
    [
        ("TEXT", "text"),
        ("IMAGE", "image"),
        ("AUDIO", "audio"),
        ("RESOURCE_LINK", "resource_link"),
        ("RESOURCE", "resource"),
    ],
)
def test_tool_content_type_values(member, value):
    """MCP tool content blocks discriminate media and embedded resources."""
    from inferencesh.types import ToolContentType

    assert hasattr(ToolContentType, member)
    assert getattr(ToolContentType, member).value == value


def test_client_capabilities_elicitation_modes():
    """ClientCapabilities.elicitation advertises form and URL elicitation support."""
    from inferencesh.types import ClientCapabilities, ElicitationCapability

    form_only: ElicitationCapability = {"form": {}}
    full: ClientCapabilities = {
        "elicitation": {
            "form": {"required": ["api_key"]},
            "url": {"callback": "https://client.example/callback"},
        },
    }

    assert form_only["form"] == {}
    assert "url" not in form_only
    assert full["elicitation"]["form"]["required"] == ["api_key"]
    assert full["elicitation"]["url"]["callback"].startswith("https://")


def test_elicit_result_action_and_content():
    """ElicitResult carries the user's accept/decline/cancel choice and form payload."""
    from inferencesh.types import ElicitAction, ElicitResult

    accepted: ElicitResult = {
        "action": ElicitAction.ACCEPT,
        "content": {"api_key": "sk-live-abc"},
    }
    declined: ElicitResult = {
        "action": ElicitAction.DECLINE,
        "content": {},
    }

    assert accepted["action"] == ElicitAction.ACCEPT
    assert accepted["content"]["api_key"] == "sk-live-abc"
    assert declined["action"] == ElicitAction.DECLINE


def test_tool_call_response_complete_shape():
    """Complete tool results omit MRTR fields; servers older than 2026-07-28 omit resultType."""
    from inferencesh.types import ResultMeta, ResultType, ToolCallResponse, ToolContent, ToolContentType

    resp: ToolCallResponse = {
        "resultType": ResultType.COMPLETE,
        "content": [
            {"type": ToolContentType.TEXT, "text": "done"},
        ],
        "isError": False,
        "_meta": {
            "io.modelcontextprotocol/serverInfo": {
                "name": "inference-mcp",
                "version": "1.0.0",
            },
            "ttlMs": 60000,
            "cacheScope": "public",
        },
    }

    assert resp["resultType"] == ResultType.COMPLETE
    assert resp["content"][0]["type"] == ToolContentType.TEXT
    assert resp["_meta"]["io.modelcontextprotocol/serverInfo"]["name"] == "inference-mcp"
    assert "inputRequests" not in resp


def test_tool_call_response_input_required_mrtr_shape():
    """input_required responses carry inputRequests and requestState for MRTR loops."""
    from inferencesh.types import InputRequest, ResultType, ToolCallResponse

    input_req: InputRequest = {
        "method": "elicitation/create",
        "params": {"message": "Enter API key", "requestedSchema": {"type": "object"}},
    }
    resp: ToolCallResponse = {
        "resultType": ResultType.INPUT_REQUIRED,
        "content": [],
        "inputRequests": {"req_1": input_req},
        "requestState": "state_token_xyz",
    }

    assert resp["resultType"] == ResultType.INPUT_REQUIRED
    assert resp["inputRequests"]["req_1"]["method"] == "elicitation/create"
    assert resp["requestState"] == "state_token_xyz"


def test_tool_call_request_mrtr_retry_fields():
    """MRTR retries echo prior inputResponses and requestState on ToolCallRequest."""
    from inferencesh.types import ToolCallRequest

    retry: ToolCallRequest = {
        "name": "deploy",
        "arguments": {"region": "us-east-1"},
        "inputResponses": {
            "req_1": {"action": "accept", "content": {"confirm": True}},
        },
        "requestState": "state_token_xyz",
    }

    assert retry["inputResponses"]["req_1"]["action"] == "accept"
    assert retry["requestState"] == "state_token_xyz"


def test_tool_content_embedded_resource():
    """ToolContent can embed ResourceContent for MCP resource payloads."""
    from inferencesh.types import ResourceContent, ToolContent, ToolContentType

    content: ToolContent = {
        "type": ToolContentType.RESOURCE,
        "resource": {
            "uri": "file:///workspace/README.md",
            "name": "README",
            "mimeType": "text/markdown",
            "text": "# Hello",
        },
    }

    resource: ResourceContent = content["resource"]
    assert content["type"] == ToolContentType.RESOURCE
    assert resource["uri"].startswith("file://")
    assert resource["mimeType"] == "text/markdown"


def test_result_meta_server_info_annotation_key():
    """ResultMeta uses the SEP-2575 serverInfo key; it must not drift from the Go tag."""
    from inferencesh.types import ResultMeta

    annotations = ResultMeta.__annotations__
    assert "io.modelcontextprotocol/serverInfo" in annotations
    assert "ttlMs" in annotations
    assert "cacheScope" in annotations


def test_agent_run_dto_output_field():
    """AgentRunDTO.output carries structured run results separate from chat output."""
    from inferencesh.types import AgentRunDTO, AgentRunState

    run: AgentRunDTO = {
        "agent_id": "agent_abc",
        "chat_id": "chat_xyz",
        "state": AgentRunState.COMPLETED,
        "output": {"artifacts": [{"type": "file", "uri": "file://out.png"}]},
    }

    assert run["state"] == AgentRunState.COMPLETED
    assert run["output"]["artifacts"][0]["uri"].endswith("out.png")
    assert "output" in AgentRunDTO.__annotations__


def test_flow_dto_namespace_field():
    """FlowDTO.namespace scopes flows to team namespaces like AppDTO."""
    from inferencesh.types import FlowDTO

    flow: FlowDTO = {
        "namespace": "acme",
        "name": "image-pipeline",
        "description": "Generate and upscale images",
    }

    assert flow["namespace"] == "acme"
    assert "namespace" in FlowDTO.__annotations__


def test_llm_input_flat_sampling_fields_on_wire_contract():
    """LLMInput wire TypedDict exposes flat sampling params (INF-626)."""
    from inferencesh.types import ChatMessageRole, LLMInput

    inp: LLMInput = {
        "model": "claude-3",
        "temperature": 0.4,
        "top_p": 0.9,
        "top_k": 50,
        "min_p": 0.1,
        "frequency_penalty": 0.2,
        "presence_penalty": 0.3,
        "repetition_penalty": 1.05,
        "seed": 7,
        "stop": ["<|end|>"],
        "max_tokens": 1024,
        "reasoning_effort": "medium",
        "reasoning_max_tokens": 256,
        "system_prompt": "Be concise.",
        "context": [],
        "role": ChatMessageRole.USER,
        "text": "hello",
    }

    annotations = LLMInput.__annotations__
    for field in [
        "top_k", "min_p", "frequency_penalty", "presence_penalty",
        "repetition_penalty", "seed", "stop", "max_tokens",
        "reasoning_effort", "reasoning_max_tokens",
    ]:
        assert field in annotations, f"LLMInput wire contract missing {field}"
    assert inp["top_k"] == 50
    assert inp["stop"] == ["<|end|>"]
    assert inp["reasoning_effort"] == "medium"


def test_model_settings_typed_dict_sampling_fields():
    """ModelSettings TypedDict groups flat sampling params for pass-through APIs."""
    from inferencesh.types import ModelSettings

    settings: ModelSettings = {
        "temperature": 0.6,
        "top_p": 0.95,
        "top_k": 30,
        "min_p": 0.05,
        "frequency_penalty": 0.1,
        "presence_penalty": 0.2,
        "repetition_penalty": 1.0,
        "seed": 42,
        "stop": ["END"],
        "max_tokens": 512,
        "reasoning_effort": "low",
        "reasoning_max_tokens": 128,
    }

    annotations = ModelSettings.__annotations__
    for field in [
        "top_k", "min_p", "frequency_penalty", "presence_penalty",
        "repetition_penalty", "seed", "stop", "max_tokens",
        "reasoning_effort", "reasoning_max_tokens",
    ]:
        assert field in annotations, f"ModelSettings wire contract missing {field}"
    assert settings["top_k"] == 30
    assert settings["reasoning_max_tokens"] == 128
