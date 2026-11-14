"""Sandbox limits, snapshots, ports, and start/create options (6f8f533 / INF-1251).

GET /sandboxes/limits returns plan caps and size ranges; teams expose snapshot
entitlements via ``ResourceUsage``. Stopped sandboxes support disk snapshots,
forking, optional image upgrade on start, creating from a snapshot, and
HTTPS port exposure on the box.
"""

import json
from typing import List, Optional, get_type_hints

from inferencesh.types import (
    CreateSandboxRequest,
    CreateSandboxSnapshotRequest,
    EngineCapability,
    EnforcementMode,
    EntitlementResource,
    EntitlementType,
    ForkSandboxRequest,
    ForkSandboxResponse,
    ResourceUsage,
    SandboxDTO,
    SandboxLimitsDTO,
    SandboxPortDTO,
    SandboxPortList,
    SandboxPortRequest,
    SandboxRange,
    SandboxSnapshotDTO,
    SandboxSnapshotStatus,
    StartSandboxRequest,
)


def test_resource_usage_contract_for_entitlement_usage_rows():
    hints = get_type_hints(ResourceUsage)
    assert set(hints) == {
        "resource",
        "label",
        "unit",
        "type",
        "usage",
        "limit",
        "unlimited",
        "enabled",
        "mode",
    }
    assert hints["resource"] is EntitlementResource
    assert hints["mode"] == EnforcementMode

    row: ResourceUsage = {
        "resource": EntitlementResource.RESOURCE_SANDBOX_SNAPSHOTS,
        "label": "Sandbox snapshots",
        "unit": "snapshots",
        "type": EntitlementType.LIMIT,
        "usage": 2,
        "limit": 5,
        "unlimited": False,
        "enabled": True,
        "mode": EnforcementMode.ENFORCEMENT_WARN,
    }
    assert row["mode"] is EnforcementMode.ENFORCEMENT_WARN


def test_sandbox_limits_dto_contract_and_round_trip():
    hints = get_type_hints(SandboxLimitsDTO)
    assert hints["limits"] == List[ResourceUsage]
    assert hints["vcpus_per_sandbox"] is SandboxRange
    assert hints["disk_kept_for"] is int

    limits: SandboxLimitsDTO = {
        "limits": [
            {
                "resource": EntitlementResource.RESOURCE_SANDBOXES,
                "usage": 1,
                "limit": 3,
                "mode": EnforcementMode.ENFORCEMENT_BLOCK,
            }
        ],
        "vcpus_per_sandbox": {"default": 2, "max": 8},
        "memory_mib": {"default": 4096, "max": 16384},
        "disk_mib": {"default": 20480, "max": 102400},
        "idle_timeout_default": 900,
        "idle_timeout_min": 60,
        "idle_timeout_max": 2_592_000,
        "disk_kept_for": 604_800,
    }
    wire = json.loads(json.dumps(limits, default=lambda o: o.value if hasattr(o, "value") else o))
    assert wire["vcpus_per_sandbox"]["max"] == 8
    assert wire["limits"][0]["resource"] == "sandboxes"
    assert wire["limits"][0]["mode"] == "block"
    assert wire["disk_kept_for"] == 604_800


def test_start_and_create_request_snapshot_and_image_options():
    start_hints = get_type_hints(StartSandboxRequest)
    create_hints = get_type_hints(CreateSandboxRequest)
    assert "upgrade_image" in start_hints
    assert start_hints["upgrade_image"] is bool
    assert "fresh_disk" in start_hints
    assert "from_snapshot_id" in create_hints
    assert create_hints["from_snapshot_id"] is str

    restart: StartSandboxRequest = {"fresh_disk": False, "upgrade_image": True}
    assert restart["upgrade_image"] is True

    from_snap: CreateSandboxRequest = {
        "name": "repro",
        "from_snapshot_id": "snap_abc",
    }
    assert from_snap["from_snapshot_id"] == "snap_abc"


def test_sandbox_port_request_list_and_dto_contract():
    req_hints = get_type_hints(SandboxPortRequest)
    dto_hints = get_type_hints(SandboxPortDTO)
    list_hints = get_type_hints(SandboxPortList)
    assert set(req_hints) == {"port", "public"}
    assert set(dto_hints) == {"port", "public", "url", "created_at"}
    assert list_hints["ports"] == List[SandboxPortDTO]

    opened: SandboxPortList = {
        "ports": [
            {
                "port": 8080,
                "public": False,
                "url": "https://8080.sbx.example/tokenized",
                "created_at": "2026-11-10T12:00:00Z",
            },
            {
                "port": 3000,
                "public": True,
                "url": "https://3000.sbx.example",
                "created_at": "2026-11-10T12:01:00Z",
            },
        ]
    }
    wire = json.loads(json.dumps(opened))
    assert wire["ports"][0]["public"] is False
    assert wire["ports"][1]["port"] == 3000

    open_req: SandboxPortRequest = {"port": 5173, "public": True}
    assert open_req["port"] == 5173


def test_snapshot_status_and_dto_contract():
    assert SandboxSnapshotStatus.SANDBOX_SNAPSHOT_PENDING.value == "pending"
    assert SandboxSnapshotStatus.SANDBOX_SNAPSHOT_READY.value == "ready"
    assert SandboxSnapshotStatus.SANDBOX_SNAPSHOT_FAILED.value == "failed"

    hints = get_type_hints(SandboxSnapshotDTO)
    assert hints["status"] is SandboxSnapshotStatus
    assert hints["ready_at"] == Optional[str]
    assert hints["for_fork"] is bool

    snap: SandboxSnapshotDTO = {
        "id": "snap_1",
        "user_id": "usr_1",
        "team_id": "team_1",
        "name": "before-migration",
        "sandbox_id": "sbx_src",
        "image": "inference/sandbox:2026.11",
        "vcpus": 2,
        "memory_mib": 4096,
        "disk_mib": 20480,
        "bytes": 1_073_741_824,
        "status": SandboxSnapshotStatus.SANDBOX_SNAPSHOT_READY,
        "ready_at": "2026-11-10T11:00:00Z",
        "for_fork": False,
    }
    wire = json.loads(
        json.dumps(snap, default=lambda o: o.value if isinstance(o, SandboxSnapshotStatus) else o)
    )
    assert wire["status"] == "ready"
    assert wire["for_fork"] is False


def test_fork_snapshot_request_and_partial_response():
    req_hints = get_type_hints(ForkSandboxRequest)
    resp_hints = get_type_hints(ForkSandboxResponse)
    assert set(req_hints) >= {"name", "count", "idle_timeout_seconds", "keep_snapshot"}
    assert resp_hints["sandboxes"] == List[Optional[SandboxDTO]]
    assert resp_hints["snapshot_id"] is str
    assert resp_hints["error"] is str

    fork_req: ForkSandboxRequest = {
        "name": "experiment",
        "count": 3,
        "idle_timeout_seconds": 1800,
        "keep_snapshot": True,
    }
    fork_resp: ForkSandboxResponse = {
        "sandboxes": [
            {"id": "sbx_a", "name": "experiment-1", "generation": 1},
            None,
        ],
        "snapshot_id": "snap_fork",
        "error": "plan limit: only 1 of 3 sandboxes started",
    }
    assert fork_req["keep_snapshot"] is True
    assert fork_resp["sandboxes"][1] is None
    assert fork_resp["error"]


def test_sandbox_snapshot_entitlement_and_engine_capability_wire():
    assert EntitlementResource.RESOURCE_SANDBOX_SNAPSHOTS.value == "sandbox_snapshots"
    assert EngineCapability.SANDBOX_SNAPSHOTS.value == "sandbox_snapshots"

    caps = {EngineCapability.SANDBOXES.value, EngineCapability.SANDBOX_SNAPSHOTS.value}
    assert caps == {"sandboxes", "sandbox_snapshots"}


def test_create_sandbox_snapshot_request_contract():
    hints = get_type_hints(CreateSandboxSnapshotRequest)
    assert set(hints) == {"name"}
    assert hints["name"] is str

    body: CreateSandboxSnapshotRequest = {"name": "golden-state"}
    assert body["name"] == "golden-state"
