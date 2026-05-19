"""Tests for generated enum constants (gotypegen acronym preservation)."""

import pytest

from inferencesh.types import (
    GPUType,
    InstanceCloudProvider,
    InstanceStatus,
    InstanceTypeDeploymentType,
    IntegrationAuthType,
    IntegrationProvider,
    IntegrationStatus,
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
