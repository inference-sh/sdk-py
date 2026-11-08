"""Sandbox disk retention and fresh start (types regen 47a1832 / INF-1163).

Stopped sandboxes may keep their disk on the engine that last ran them; clients
read ``disk_kept`` / ``disk_kept_until`` on ``SandboxDTO``. POST
``/sandboxes/{id}/start`` accepts ``StartSandboxRequest.fresh_disk`` to drop the
kept disk and boot on a new empty volume instead of reattaching.
"""

from typing import Optional, get_type_hints

from inferencesh.types import SandboxDTO, SandboxDesiredState, SandboxStatus, StartSandboxRequest


def test_start_sandbox_request_declares_fresh_disk_option():
    hints = get_type_hints(StartSandboxRequest)
    assert set(hints) == {"fresh_disk"}
    assert hints["fresh_disk"] is bool


def test_start_sandbox_request_accepts_fresh_disk_wire_key():
    empty: StartSandboxRequest = {}
    assert "fresh_disk" not in empty

    fresh: StartSandboxRequest = {"fresh_disk": True}
    assert fresh["fresh_disk"] is True

    reuse: StartSandboxRequest = {"fresh_disk": False}
    assert reuse["fresh_disk"] is False


def test_sandbox_dto_exposes_disk_retention_fields():
    hints = get_type_hints(SandboxDTO)
    assert hints["disk_kept"] is bool
    assert hints["disk_kept_until"] == Optional[str]


def test_sandbox_dto_accepts_disk_kept_snapshot():
    row: SandboxDTO = {
        "id": "sbx_disk",
        "name": "data-box",
        "image": "inference/sandbox:latest",
        "vcpus": 2,
        "memory_mib": 4096,
        "disk_mib": 20480,
        "desired_state": SandboxDesiredState.SANDBOX_DESIRED_STOPPED,
        "status": SandboxStatus.STOPPED,
        "status_reason": "",
        "generation": 2,
        "engine_id": "eng-9",
        "worker_id": None,
        "remote_id": "remote-xyz",
        "started_at": "2026-11-01T10:00:00Z",
        "stopped_at": "2026-11-08T09:00:00Z",
        "disk_kept": True,
        "disk_kept_until": "2026-11-15T09:00:00Z",
    }
    assert row["disk_kept"] is True
    assert row["disk_kept_until"] == "2026-11-15T09:00:00Z"


def test_sandbox_dto_disk_not_kept_after_engine_drops_volume():
    row: SandboxDTO = {
        "id": "sbx_fresh",
        "name": "ephemeral",
        "image": "inference/sandbox:latest",
        "vcpus": 1,
        "memory_mib": 2048,
        "disk_mib": 10240,
        "desired_state": SandboxDesiredState.SANDBOX_DESIRED_STOPPED,
        "status": SandboxStatus.STOPPED,
        "status_reason": "",
        "generation": 1,
        "engine_id": None,
        "worker_id": None,
        "remote_id": "remote-abc",
        "started_at": None,
        "stopped_at": "2026-11-08T12:00:00Z",
        "disk_kept": False,
        "disk_kept_until": None,
    }
    assert row["disk_kept"] is False
    assert row["disk_kept_until"] is None
