"""Sandbox snapshots in object storage (27271b5 / api#2342).

Snapshots may be kept on the source engine only, or uploaded to object storage
so forks and new sandboxes can start on any engine. ``SandboxSnapshotDTO`` exposes
``store_status`` and ``stored_bytes``; engines advertise
``EngineCapability.SANDBOX_SNAPSHOT_STORE`` when they can upload and rebuild
from stored parts.
"""

import json
from typing import get_type_hints

from inferencesh.types import (
    EngineCapability,
    SandboxSnapshotDTO,
    SandboxSnapshotStatus,
    SandboxSnapshotStoreStatus,
)


def _enum_json_default(obj):
    if isinstance(obj, (SandboxSnapshotStatus, SandboxSnapshotStoreStatus)):
        return obj.value
    raise TypeError(type(obj))


def test_sandbox_snapshot_store_status_wire_values():
    assert SandboxSnapshotStoreStatus.SANDBOX_SNAPSHOT_STORE_PENDING.value == "pending"
    assert SandboxSnapshotStoreStatus.SANDBOX_SNAPSHOT_STORE_UPLOADING.value == "uploading"
    assert SandboxSnapshotStoreStatus.SANDBOX_SNAPSHOT_STORE_STORED.value == "stored"
    assert SandboxSnapshotStoreStatus.SANDBOX_SNAPSHOT_STORE_FAILED.value == "failed"

    assert SandboxSnapshotStoreStatus("stored") is SandboxSnapshotStoreStatus.SANDBOX_SNAPSHOT_STORE_STORED


def test_engine_capability_sandbox_snapshot_store_wire():
    assert EngineCapability.SANDBOX_SNAPSHOT_STORE.value == "sandbox_snapshot_store"
    assert EngineCapability.SANDBOX_SNAPSHOTS.value == "sandbox_snapshots"
    assert EngineCapability.SANDBOX_SNAPSHOT_STORE.value != EngineCapability.SANDBOX_SNAPSHOTS.value


def test_sandbox_snapshot_dto_object_storage_fields():
    hints = get_type_hints(SandboxSnapshotDTO)
    assert hints["store_status"] is SandboxSnapshotStoreStatus
    assert hints["stored_bytes"] is int
    assert hints["status"] is SandboxSnapshotStatus


def test_sandbox_snapshot_dto_stored_copy_json_round_trip():
    snap: SandboxSnapshotDTO = {
        "id": "snap_obj_1",
        "user_id": "usr_1",
        "team_id": "team_1",
        "name": "portable-golden",
        "sandbox_id": "sbx_src",
        "image": "inference/sandbox:2026.11",
        "vcpus": 4,
        "memory_mib": 8192,
        "disk_mib": 51200,
        "bytes": 2_147_483_648,
        "status": SandboxSnapshotStatus.SANDBOX_SNAPSHOT_READY,
        "ready_at": "2026-11-11T06:00:00Z",
        "store_status": SandboxSnapshotStoreStatus.SANDBOX_SNAPSHOT_STORE_STORED,
        "stored_bytes": 412_876_543,
        "for_fork": False,
    }
    wire = json.loads(json.dumps(snap, default=_enum_json_default))
    assert wire["status"] == "ready"
    assert wire["store_status"] == "stored"
    assert wire["stored_bytes"] == 412_876_543


def test_sandbox_snapshot_dto_engine_local_omits_object_storage_fields():
    """Engine-local copies need not send store metadata (total=False)."""
    snap: SandboxSnapshotDTO = {
        "id": "snap_local",
        "status": SandboxSnapshotStatus.SANDBOX_SNAPSHOT_READY,
        "bytes": 1_073_741_824,
        "for_fork": False,
    }
    wire = json.loads(json.dumps(snap, default=_enum_json_default))
    assert "store_status" not in wire
    assert "stored_bytes" not in wire


def test_sandbox_snapshot_dto_upload_in_progress():
    snap: SandboxSnapshotDTO = {
        "id": "snap_up",
        "status": SandboxSnapshotStatus.SANDBOX_SNAPSHOT_READY,
        "store_status": SandboxSnapshotStoreStatus.SANDBOX_SNAPSHOT_STORE_UPLOADING,
        "stored_bytes": 0,
    }
    wire = json.loads(json.dumps(snap, default=_enum_json_default))
    assert wire["store_status"] == "uploading"
    assert wire["stored_bytes"] == 0
