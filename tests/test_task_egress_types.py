"""TaskEgress on TaskDTO (309909b / models v0.8.123).

Engines report sandbox internet traffic through the egress gateway when a task
ends. Clients read byte counters from GET /tasks/{id}; tasks without the
gateway omit ``egress``. Guards against typegen drift on wire keys and shapes.
"""

from typing import Optional, get_type_hints

from inferencesh.types import TaskDTO, TaskEgress, TaskResultDTO, TaskStatus


def test_task_egress_counters_use_snake_case_wire_keys():
    hints = get_type_hints(TaskEgress)
    assert hints == {"bytes_out": int, "bytes_in": int}


def test_task_egress_allows_partial_counters():
    """total=False mirrors API responses that may only report one direction."""
    egress: TaskEgress = {"bytes_out": 1_048_576}
    assert egress["bytes_out"] == 1_048_576
    assert "bytes_in" not in egress


def test_task_dto_egress_optional_gateway_stats():
    hints = get_type_hints(TaskDTO)
    assert hints["egress"] == Optional[TaskEgress]

    with_gateway: TaskDTO = {
        "id": "task-egress-1",
        "status": TaskStatus.COMPLETED,
        "egress": {"bytes_out": 4096, "bytes_in": 8192},
    }
    assert with_gateway["egress"]["bytes_in"] == 8192

    without_gateway: TaskDTO = {
        "id": "task-no-egress",
        "status": TaskStatus.COMPLETED,
    }
    assert "egress" not in without_gateway


def test_task_result_dto_omits_egress_on_slim_endpoints():
    """Run/result payloads stay slim; full task GET carries egress."""
    hints = get_type_hints(TaskResultDTO)
    assert "egress" not in hints
