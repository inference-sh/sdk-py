"""Wire contract for Infra (models v0.8.151: direct/remote scheduling mode removed).

The scheduler no longer accepts infra=remote; the enum documents only the
modes clients may request on runs and tasks.
"""

from typing import Optional, get_type_hints

import pytest

from inferencesh.types import ApiAppRunRequest, FlowNodeData, Infra, TaskDTO


def test_infra_enum_wire_values():
    assert {m.value for m in Infra} == {"private", "cloud", "private_first"}


def test_infra_remote_member_removed():
    """InfraRemote was dropped in v0.8.151; do not reintroduce Infra.REMOTE."""
    assert not hasattr(Infra, "REMOTE")
    with pytest.raises(ValueError, match="remote"):
        Infra("remote")


@pytest.mark.parametrize(
    "infra",
    [Infra.PRIVATE, Infra.CLOUD, Infra.PRIVATE_FIRST],
)
def test_task_dto_accepts_infra_values(infra):
    hints = get_type_hints(TaskDTO)
    assert hints["infra"] is Infra

    task: TaskDTO = {
        "id": "task_1",
        "infra": infra,
        "function": "predict",
        "app_id": "app_1",
        "app_version_id": "ver_1",
    }
    assert task["infra"] is infra
    assert task["infra"].value in {"private", "cloud", "private_first"}


def test_api_app_run_request_infra_optional():
    hints = get_type_hints(ApiAppRunRequest)
    assert hints["infra"] == Optional[Infra]

    without: ApiAppRunRequest = {"app": "my-app", "input": {}}
    assert "infra" not in without

    with_infra: ApiAppRunRequest = {
        "app": "my-app",
        "input": {},
        "infra": Infra.PRIVATE_FIRST,
    }
    assert with_infra["infra"] is Infra.PRIVATE_FIRST


def test_flow_node_data_infra_required_on_typed_dict():
    hints = get_type_hints(FlowNodeData)
    assert hints["infra"] is Infra

    node: FlowNodeData = {
        "function": "run",
        "infra": Infra.CLOUD,
        "workers": [],
    }
    assert node["infra"].value == "cloud"
