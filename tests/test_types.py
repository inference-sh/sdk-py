"""Tests for generated enum constants (gotypegen acronym preservation)."""

from typing import get_type_hints

import pytest

from inferencesh.types import (
    DeviceAuthStatus,
    GPUType,
    GraphEdgeType,
    GraphNodeStatus,
    GraphNodeType,
    InstanceCloudProvider,
    InstanceStatus,
    InstanceTypeConfiguration,
    InstanceTypeDeploymentType,
    InstanceTypeDTO,
    IntegrationAuthType,
    IntegrationProvider,
    IntegrationStatus,
    IntegrationType,
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
    SuggestRequest,
    SuggestResponse,
    SuggestResult,
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
        (IntegrationProvider, "GCP", "gcp"),
        (IntegrationProvider, "MCP", "mcp"),
        (IntegrationAuthType, "O_AUTH", "oauth"),
        (IntegrationAuthType, "API_KEY", "api_key"),
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
    ],
)
def test_graph_edge_type_values(member, value):
    """Graph edge kinds must include REFERENCES from latest typegen regen."""
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
    """GPU hardware metadata from typegen must include manufacturer and nvlink."""
    hints = get_type_hints(InstanceTypeConfiguration)
    assert hints["gpu_manufacturer"] is str
    assert hints["nvlink"] is bool
    assert hints["gpu_type"] is str
    assert hints["num_gpus"] is int


def test_instance_type_dto_cloud_logo_url_field():
    """Instance catalog responses must expose cloud_logo_url for UI branding."""
    hints = get_type_hints(InstanceTypeDTO)
    assert "cloud_logo_url" in hints
    assert hints["cloud_logo_url"] is str
    assert "configuration" in hints


@pytest.mark.parametrize(
    "typedict_cls,field,expected_type",
    [
        (SuggestRequest, "query", str),
        (SuggestRequest, "limit", int),
        (SuggestRequest, "category", str),
        (SuggestRequest, "agent", bool),
        (SuggestResult, "type", str),
        (SuggestResult, "name", str),
        (SuggestResult, "description", str),
        (SuggestResult, "command", str),
        (SuggestResult, "score", float),
        (SuggestResponse, "query", str),
    ],
)
def test_suggest_typedict_field_annotations(typedict_cls, field, expected_type):
    """Suggest endpoint TypedDicts must keep stable field names and types."""
    hints = get_type_hints(typedict_cls)
    assert field in hints, f"{typedict_cls.__name__}.{field} missing"
    assert hints[field] is expected_type


def test_suggest_response_results_list_annotation():
    """SuggestResponse.results must be a list of SuggestResult items."""
    hints = get_type_hints(SuggestResponse)
    results_hint = hints["results"]
    assert results_hint.__origin__ is list
    assert results_hint.__args__[0] is SuggestResult


def test_suggest_payload_roundtrip():
    """Representative suggest API payload must satisfy TypedDict field names."""
    result: SuggestResult = {
        "type": "app",
        "name": "okaris/flux",
        "description": "Image generation",
        "command": "inference run okaris/flux@abc1",
        "score": 0.92,
    }
    response: SuggestResponse = {
        "query": "image generation",
        "results": [result],
    }
    request: SuggestRequest = {
        "query": "image generation",
        "limit": 5,
        "category": "apps",
        "agent": False,
    }
    assert response["results"][0]["score"] == 0.92
    assert request["limit"] == 5
