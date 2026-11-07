"""Regression tests for TaskCancelled / TaskFailed (commit d4762d6).

Several client tests still use ``pytest.raises(RuntimeError)`` on FAILED paths.
That passes because the new exceptions subclass ``RuntimeError``, but it would not
catch a regression to bare ``RuntimeError`` without a ``.task`` payload. These
tests pin the concrete types, public exports, and ``_strip_task`` error retention.
"""

import pytest

from inferencesh import AsyncInference, Inference, TaskCancelled, TaskFailed, TaskStatus
from inferencesh.client import _strip_task
from inferencesh.models.errors import TaskCancelled as TaskCancelledModel
from inferencesh.models.errors import TaskFailed as TaskFailedModel
from inferencesh.models.response import Response

pytest_plugins = ["tests.test_client"]


class TestTaskTerminalErrorTypes:
    def test_task_failed_subclasses_runtime_error_and_carries_task(self):
        task = {"id": "t1", "status": TaskStatus.FAILED, "error": "boom"}
        exc = TaskFailedModel(task)
        assert isinstance(exc, RuntimeError)
        assert str(exc) == "boom"
        assert exc.task is task
        assert "t1" in repr(exc)

    def test_task_failed_default_message_without_error(self):
        exc = TaskFailedModel({"id": "t1"})
        assert str(exc) == "Task failed"

    def test_task_cancelled_subclasses_runtime_error_and_carries_output(self):
        task = {"id": "t1", "status": TaskStatus.CANCELLED, "output": {"x": 1}}
        exc = TaskCancelledModel(task)
        assert isinstance(exc, RuntimeError)
        assert exc.task["output"] == {"x": 1}
        assert "t1" in repr(exc)

    def test_strip_task_keeps_error_for_failed_tasks(self):
        stripped = _strip_task({
            "id": "t1",
            "status": TaskStatus.FAILED,
            "error": "reason",
            "worker_id": "w",
        })
        assert stripped["error"] == "reason"
        assert "worker_id" not in stripped

    def test_exported_from_package_root(self):
        assert TaskCancelled is TaskCancelledModel
        assert TaskFailed is TaskFailedModel
        import inferencesh

        assert "TaskCancelled" in inferencesh.__all__
        assert "TaskFailed" in inferencesh.__all__


def test_sync_stream_reconcile_failed_raises_task_failed_with_task(monkeypatch):
    """TaskStream GET reconciliation must raise TaskFailed (not bare RuntimeError)."""
    client = Inference(api_key="test")

    def fake_stream_updates(task_id, task):
        yield {"id": task_id, "status": TaskStatus.RUNNING}

    monkeypatch.setattr(client, "_stream_updates", fake_stream_updates)
    monkeypatch.setattr(
        client,
        "get_task",
        lambda tid: Response({
            "id": tid,
            "status": TaskStatus.FAILED,
            "error": "GPU OOM",
        }),
    )

    with pytest.raises(TaskFailed, match="GPU OOM") as exc_info:
        with client.run(
            {"app": "some/app", "input": {}}, stream=True, auto_reconnect=False,
        ) as stream:
            list(stream)

    assert exc_info.value.task["id"] == "task_123"
    assert exc_info.value.task["error"] == "GPU OOM"
    assert exc_info.value.task["status"] == TaskStatus.FAILED


def test_sync_wait_for_completion_failed_stream_event_raises_task_failed(monkeypatch):
    """wait_for_completion stream path must raise TaskFailed carrying the task."""
    client = Inference(api_key="test")

    def fake_stream_updates(task_id, task):
        yield {"id": task_id, "status": TaskStatus.FAILED, "error": "worker died"}

    monkeypatch.setattr(client, "_stream_updates", fake_stream_updates)

    with pytest.raises(TaskFailed, match="worker died") as exc_info:
        client.wait_for_completion("task_123")

    assert exc_info.value.task["id"] == "task_123"
    assert exc_info.value.task["error"] == "worker died"


@pytest.mark.asyncio
async def test_async_stream_reconcile_failed_raises_task_failed_with_task(
    monkeypatch, patch_aiohttp,
):
    """AsyncTaskStream GET reconciliation must raise TaskFailed with .task populated."""
    client = AsyncInference(api_key="test")

    async def fake_stream_updates(task_id, task):
        yield {"id": task_id, "status": TaskStatus.RUNNING}

    async def fake_get_task(tid):
        return Response({
            "id": tid,
            "status": TaskStatus.FAILED,
            "error": "GPU OOM",
        })

    monkeypatch.setattr(client, "_stream_updates", fake_stream_updates)
    monkeypatch.setattr(client, "get_task", fake_get_task)

    with pytest.raises(TaskFailed, match="GPU OOM") as exc_info:
        async with await client.run(
            {"app": "some/app", "input": {}}, stream=True, auto_reconnect=False,
        ) as stream:
            async for _ in stream:
                pass

    assert exc_info.value.task["error"] == "GPU OOM"
    assert exc_info.value.task["status"] == TaskStatus.FAILED
