"""Agent protocol v0.20+ and deploy warning contracts (d014eb0 / INF-1053).

Typegen can shadow enums or drop wire fields; these tests fail fast when
clients would mis-route agent events or mis-read deploy/version payloads.
"""

import ast
from pathlib import Path
from typing import List, get_type_hints

import inferencesh.types as types_mod

from inferencesh.types import (
    AgentEventType,
    AppFunction,
    AppVersionDTO,
    ContentDeltaPayload,
    CredentialRequirement,
    DeployWarning,
    ToolAnnotations,
    TurnUsageStatus,
    UsageUpdatedPayload,
)


def test_agent_event_type_is_defined_once_in_types_module():
    """A duplicate class shadowed subagent.* members until merged into one enum."""
    source = Path(types_mod.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    class_defs = [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == "AgentEventType"
    ]
    assert class_defs == ["AgentEventType"]


def test_agent_event_type_includes_lifecycle_and_subagent_wire_values():
    values = {m.value for m in AgentEventType}
    assert "run.started" in values
    assert "usage.updated" in values
    assert "context.updated" in values
    assert "limits.updated" in values
    assert "account.updated" in values
    assert "subagent.started" in values
    assert "subagent.updated" in values
    assert "subagent.completed" in values
    assert AgentEventType.AGENT_EVENT_USAGE_UPDATED.value == "usage.updated"
    assert AgentEventType.AGENT_EVENT_SUBAGENT_STARTED.value == "subagent.started"


def test_usage_updated_payload_token_breakdown_and_status():
    hints = get_type_hints(UsageUpdatedPayload)
    assert hints["prompt_tokens"] is int
    assert hints["cached_input_tokens"] is int
    assert hints["cache_creation_tokens"] is int
    assert hints["reasoning_tokens"] is int
    assert hints["cost_usd"] is float
    assert hints["status"] is TurnUsageStatus

    usage: UsageUpdatedPayload = {
        "prompt_tokens": 100,
        "completion_tokens": 20,
        "total_tokens": 120,
        "cached_input_tokens": 40,
        "cache_creation_tokens": 10,
        "reasoning_tokens": 5,
        "cost_usd": 0.01,
        "status": TurnUsageStatus.TURN_USAGE_PARTIAL,
    }
    assert usage["status"] is TurnUsageStatus.TURN_USAGE_PARTIAL


def test_content_delta_payload_optional_subagent_id():
    hints = get_type_hints(ContentDeltaPayload)
    assert hints["subagent_id"] is str

    payload: ContentDeltaPayload = {"kind": "text", "delta": "hi", "subagent_id": "sub-1"}
    assert payload["subagent_id"] == "sub-1"


def test_deploy_warning_and_app_version_warnings_list():
    warn_hints = get_type_hints(DeployWarning)
    assert warn_hints["code"] is str
    assert warn_hints["function"] is str
    assert warn_hints["message"] is str

    version_hints = get_type_hints(AppVersionDTO)
    assert version_hints["warnings"] == List[DeployWarning]

    warning: DeployWarning = {
        "code": "missing_annotations",
        "function": "create_event",
        "message": "declare MCP hints",
    }
    version: AppVersionDTO = {"id": "ver_1", "warnings": [warning]}
    assert version["warnings"][0]["code"] == "missing_annotations"


def test_app_function_schema_carries_per_function_credentials_and_annotations():
    fn_hints = get_type_hints(AppFunction)
    assert fn_hints["credentials"] == List[CredentialRequirement]
    assert fn_hints["annotations"] == ToolAnnotations | None

    fn: AppFunction = {
        "name": "create_event",
        "credentials": [{"key": "google.calendar.events"}],
        "annotations": {"readOnlyHint": False, "title": "Create event"},
    }
    assert fn["credentials"][0]["key"] == "google.calendar.events"
    assert fn["annotations"]["readOnlyHint"] is False
