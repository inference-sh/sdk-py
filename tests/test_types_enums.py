"""Regression tests for generated enum member names.

gotypegen must preserve acronyms as single tokens (e.g. MCP, HTTP, AWS), not
split them (M_C_P, H_T_T_P). tools.py references ToolType.MCP and ToolType.HTTP;
a bad regen breaks tool builders at runtime.
"""

import pytest

from inferencesh.types import (
    AppCategory,
    EntitlementResource,
    GPUType,
    InstanceCloudProvider,
    InstanceTypeDeploymentType,
    ToolType,
    VideoResolution,
)


@pytest.mark.parametrize(
    "enum_cls, member, expected_value",
    [
        (ToolType, "MCP", "mcp"),
        (ToolType, "HTTP", "http"),
        (GPUType, "AMD", "amd"),
        (AppCategory, "_3D", "3d"),
        (InstanceCloudProvider, "CLOUD_AWS", "aws"),
        (InstanceTypeDeploymentType, "VM", "vm"),
        (VideoResolution, "VIDEO_RES4K", "4k"),
        (EntitlementResource, "RESOURCE_API_KEYS", "api_keys"),
        (EntitlementResource, "RESOURCE_FEATURE_BYOK", "feature:byok"),
    ],
)
def test_enum_member_name_and_value(enum_cls, member, expected_value):
    """Renamed enum members must exist and keep their wire values."""
    enum_member = getattr(enum_cls, member)
    assert enum_member.value == expected_value
