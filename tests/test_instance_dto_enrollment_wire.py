"""Cloud instance API wire (api-v1572 / 0d606f6).

Instance payloads no longer expose ``launch_configuration`` or ``envs``; the
engine enrollment token rides in the instance boot script instead
(``models.ToInstanceDTO``). SDK consumers must not expect those keys on
``InstanceDTO`` or deserialize them from list/detail responses.
"""

from typing import Any, Optional, get_type_hints

from inferencesh.types import (
    EngineDTO,
    EngineStatus,
    EngineSummary,
    InstanceDTO,
    InstanceStatus,
)


def test_instance_dto_drops_launch_configuration_and_envs():
    """api-v1572 removed launch-time env injection from the wire DTO."""
    hints = get_type_hints(InstanceDTO)
    assert "launch_configuration" not in hints
    assert "envs" not in hints


def test_instance_dto_keeps_configuration_and_runtime_fields():
    hints = get_type_hints(InstanceDTO)
    assert hints["configuration"] is Any
    assert set(hints) >= {
        "cloud",
        "name",
        "region",
        "status",
        "template_id",
        "configuration",
        "ssh_key_id",
        "ip",
    }


def test_instance_dto_accepts_status_without_legacy_launch_keys():
    row: InstanceDTO = {
        "name": "worker-1",
        "region": "us-east-1",
        "status": InstanceStatus.ACTIVE,
        "configuration": {"image": "ubuntu-22.04"},
        "ip": "203.0.113.10",
    }
    assert row["status"] is InstanceStatus.ACTIVE
    assert row["configuration"]["image"] == "ubuntu-22.04"
    assert "launch_configuration" not in row
    assert "envs" not in row


def test_engine_responses_still_embed_instance_without_launch_fields():
    for dto in (EngineDTO, EngineSummary):
        hints = get_type_hints(dto)
        assert hints["instance"] == Optional[InstanceDTO]

    summary: EngineSummary = {
        "name": "edge",
        "status": EngineStatus.RUNNING,
        "instance": {
            "name": "edge-box",
            "configuration": {"role": "engine"},
        },
    }
    assert summary["instance"]["name"] == "edge-box"
    assert "envs" not in summary["instance"]