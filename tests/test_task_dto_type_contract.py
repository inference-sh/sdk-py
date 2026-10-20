"""TaskDTO / TaskResultDTO wire contracts (391655d revert of task.egress).

The API briefly exposed sandbox egress counters on full task payloads; dev reverted
``TaskEgress`` and ``TaskDTO.egress`` until models stabilize. These guards keep the
slim result DTO and the full task shape aligned with the generated contract.
"""

import importlib
from typing import Any, List, Optional, get_type_hints

from inferencesh.types import (
    TaskDTO,
    TaskEvent,
    TaskLog,
    TaskResultDTO,
    TaskStatus,
    UsageEventDTO,
)


def test_task_egress_type_is_not_exported_after_revert():
    types_mod = importlib.import_module("inferencesh.types")
    assert not hasattr(types_mod, "TaskEgress")


def test_task_dto_excludes_egress_field():
    hints = get_type_hints(TaskDTO)
    assert "egress" not in hints
    assert hints["status"] is TaskStatus
    assert hints["events"] == List[TaskEvent]
    assert hints["logs"] == List[TaskLog]
    assert hints["usage_events"] == List[Optional[UsageEventDTO]]


def test_task_result_dto_is_slim_run_payload_without_egress():
    hints = get_type_hints(TaskResultDTO)
    assert "egress" not in hints
    assert hints["status"] is TaskStatus
    assert hints["output"] is Any
    assert hints["error"] == Optional[str]

    row: TaskResultDTO = {
        "id": "task-1",
        "short_id": "t1",
        "status": TaskStatus.COMPLETED,
        "output": {"ok": True},
        "error": None,
    }
    assert row["status"] is TaskStatus.COMPLETED
