"""Managed sandbox API types (aaa858b / INF-833 typegen).

Sandboxes are team-managed boxes that run a remote on an engine with boxd.
Clients POST ``CreateSandboxRequest``, list ``SandboxDTO`` rows, and gate access
via ``sandboxes:*`` scopes and ``feature:sandboxes`` entitlements. These tests
lock wire values and DTO shapes so SDK regen cannot drop fields or rename enums.
"""

import json
from typing import Optional, get_type_hints

from inferencesh.types import (
    CreateSandboxRequest,
    EngineCapability,
    EntitlementResource,
    SandboxDTO,
    SandboxDesiredState,
    SandboxStatus,
    Scope,
    ScopeGroup,
)


def test_create_sandbox_request_exposes_size_fields():
    hints = get_type_hints(CreateSandboxRequest)
    assert hints["name"] is str
    assert hints["vcpus"] is int
    assert hints["memory_mib"] is int
    assert hints["disk_mib"] is int

    req: CreateSandboxRequest = {
        "name": "dev-box",
        "vcpus": 2,
        "memory_mib": 4096,
        "disk_mib": 20480,
    }
    assert req["name"] == "dev-box"


def test_sandbox_dto_carries_lifecycle_and_placement_fields():
    hints = get_type_hints(SandboxDTO)
    assert hints["name"] is str
    assert hints["image"] is str
    assert hints["vcpus"] is int
    assert hints["memory_mib"] is int
    assert hints["disk_mib"] is int
    assert hints["desired_state"] is SandboxDesiredState
    assert hints["status"] is SandboxStatus
    assert hints["status_reason"] is str
    assert hints["generation"] is int
    assert hints["engine_id"] == Optional[str]
    assert hints["worker_id"] == Optional[str]
    assert hints["remote_id"] == Optional[str]
    assert hints["started_at"] == Optional[str]
    assert hints["stopped_at"] == Optional[str]

    row: SandboxDTO = {
        "id": "sbx_1",
        "name": "dev-box",
        "image": "inference/sandbox:latest",
        "vcpus": 2,
        "memory_mib": 4096,
        "disk_mib": 20480,
        "desired_state": SandboxDesiredState.SANDBOX_DESIRED_RUNNING,
        "status": SandboxStatus.RUNNING,
        "status_reason": "",
        "generation": 3,
        "engine_id": "eng-7",
        "worker_id": "wrk-2",
        "remote_id": "remote-abc",
        "started_at": "2026-10-30T20:00:00Z",
        "stopped_at": None,
    }
    assert row["status"] is SandboxStatus.RUNNING


def test_sandbox_status_wire_values():
    assert {s.value for s in SandboxStatus} == {
        "pending",
        "starting",
        "running",
        "stopping",
        "stopped",
        "failed",
    }
    assert SandboxStatus("running") is SandboxStatus.RUNNING


def test_sandbox_desired_state_wire_values():
    assert SandboxDesiredState.SANDBOX_DESIRED_RUNNING.value == "running"
    assert SandboxDesiredState.SANDBOX_DESIRED_STOPPED.value == "stopped"
    assert SandboxDesiredState.SANDBOX_DESIRED_DELETED.value == "deleted"
    assert len(SandboxDesiredState) == 3


def test_sandbox_scopes_and_scope_group():
    assert Scope.SANDBOXES_READ.value == "sandboxes:read"
    assert Scope.SANDBOXES_WRITE.value == "sandboxes:write"
    assert ScopeGroup.SANDBOXES.value == "sandboxes"


def test_engine_capability_sandboxes():
    assert EngineCapability.SANDBOXES.value == "sandboxes"
    assert EngineCapability.EGRESS_GATEWAY.value == "egress_gateway"


def test_entitlement_resource_feature_sandboxes():
    assert EntitlementResource.RESOURCE_FEATURE_SANDBOXES.value == "feature:sandboxes"


def test_sandbox_dto_enums_round_trip_on_wire():
    row: SandboxDTO = {
        "id": "sbx_1",
        "name": "dev-box",
        "image": "inference/sandbox:latest",
        "vcpus": 1,
        "memory_mib": 2048,
        "disk_mib": 10240,
        "desired_state": SandboxDesiredState.SANDBOX_DESIRED_STOPPED,
        "status": SandboxStatus.STOPPED,
        "status_reason": "user_requested",
        "generation": 1,
        "engine_id": None,
        "worker_id": None,
        "remote_id": "remote-abc",
        "started_at": None,
        "stopped_at": "2026-10-30T21:00:00Z",
    }
    wire = json.loads(json.dumps(row, default=lambda o: o.value if hasattr(o, "value") else o))
    assert wire["status"] == "stopped"
    assert wire["desired_state"] == "stopped"
    assert wire["remote_id"] == "remote-abc"
