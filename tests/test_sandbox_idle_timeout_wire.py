"""Sandbox idle timeout wire (types regen 35aa76f / INF-1209).

Create and PATCH bodies carry ``idle_timeout_seconds``; ``SandboxDTO`` exposes the
effective timeout and ``last_activity_at`` so clients can show auto-stop policy and
refresh timers after API use.
"""

import json
from typing import Optional, get_type_hints

from inferencesh.types import (
    CreateSandboxRequest,
    SandboxDTO,
    SandboxDesiredState,
    SandboxStatus,
    UpdateSandboxRequest,
)


def test_create_sandbox_request_declares_idle_timeout():
    hints = get_type_hints(CreateSandboxRequest)
    assert hints["idle_timeout_seconds"] == Optional[int]


def test_create_sandbox_request_accepts_idle_timeout_wire_values():
    default_policy: CreateSandboxRequest = {
        "name": "idle-box",
        "vcpus": 1,
        "memory_mib": 2048,
        "disk_mib": 10240,
    }
    assert "idle_timeout_seconds" not in default_policy

    thirty_min: CreateSandboxRequest = {**default_policy, "idle_timeout_seconds": 1800}
    assert thirty_min["idle_timeout_seconds"] == 1800

    never_stop: CreateSandboxRequest = {**default_policy, "idle_timeout_seconds": 0}
    assert never_stop["idle_timeout_seconds"] == 0


def test_update_sandbox_request_is_patch_body_with_idle_timeout_only():
    hints = get_type_hints(UpdateSandboxRequest)
    assert set(hints) == {"idle_timeout_seconds"}
    assert hints["idle_timeout_seconds"] == Optional[int]


def test_update_sandbox_request_accepts_patch_idle_timeout():
    clear: UpdateSandboxRequest = {"idle_timeout_seconds": None}
    assert clear["idle_timeout_seconds"] is None

    patch: UpdateSandboxRequest = {"idle_timeout_seconds": 3600}
    assert patch["idle_timeout_seconds"] == 3600


def test_sandbox_dto_exposes_idle_timeout_and_last_activity():
    hints = get_type_hints(SandboxDTO)
    assert hints["idle_timeout_seconds"] is int
    assert hints["last_activity_at"] == Optional[str]


def test_sandbox_dto_running_snapshot_carries_activity_and_timeout():
    row: SandboxDTO = {
        "id": "sbx_idle",
        "name": "dev-box",
        "image": "inference/sandbox:latest",
        "vcpus": 2,
        "memory_mib": 4096,
        "disk_mib": 20480,
        "desired_state": SandboxDesiredState.SANDBOX_DESIRED_RUNNING,
        "status": SandboxStatus.RUNNING,
        "status_reason": "",
        "generation": 4,
        "engine_id": "eng-12",
        "worker_id": "wrk-3",
        "remote_id": "remote-xyz",
        "started_at": "2026-11-08T18:00:00Z",
        "stopped_at": None,
        "disk_kept": True,
        "disk_kept_until": None,
        "idle_timeout_seconds": 1800,
        "last_activity_at": "2026-11-08T18:45:00Z",
    }
    assert row["idle_timeout_seconds"] == 1800
    assert row["last_activity_at"] == "2026-11-08T18:45:00Z"

    wire = json.loads(json.dumps(row, default=lambda o: o.value if hasattr(o, "value") else o))
    assert wire["idle_timeout_seconds"] == 1800
    assert wire["last_activity_at"] == "2026-11-08T18:45:00Z"
    assert wire["status"] == "running"
