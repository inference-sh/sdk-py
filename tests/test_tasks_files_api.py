"""Tasks API: delete, files and delete_files (mocked _request)."""

import asyncio
from typing import Any, Dict, List

from inferencesh import AsyncInference, Inference
from inferencesh.models.response import Response

FILES = [{"id": "file-1", "uri": "https://cloud.test/a.png", "role": "output"}]
DELETED = {"deleted": ["file-1"], "skipped": []}
DELETED_PARTIAL = {
    "deleted": ["file-1"],
    "skipped": [{"id": "file-2", "reason": "referenced_by_other_task"}],
}


def answer(
    calls: List[Dict[str, Any]],
    method: str,
    endpoint: str,
    params: Any,
    *,
    delete_payload: Dict[str, Any] = DELETED,
) -> Response:
    calls.append({"method": method.upper(), "endpoint": endpoint, "params": params})
    if method == "get":
        return Response(FILES)
    return Response(delete_payload if endpoint.endswith("/files") else None)


def sync_client(*, delete_payload: Dict[str, Any] = DELETED):
    client = Inference(api_key="test")
    calls: List[Dict[str, Any]] = []

    def fake(method, endpoint, *, params=None, data=None, headers=None, stream=False, timeout=None):
        return answer(calls, method, endpoint, params, delete_payload=delete_payload)

    client._request = fake  # type: ignore[method-assign]
    return client, calls


def async_client(*, delete_payload: Dict[str, Any] = DELETED):
    client = AsyncInference(api_key="test")
    calls: List[Dict[str, Any]] = []

    async def fake(method, endpoint, *, params=None, data=None, headers=None, timeout=None, expect_stream=False):
        return answer(calls, method, endpoint, params, delete_payload=delete_payload)

    client._request = fake  # type: ignore[method-assign]
    return client, calls


EXPECTED = [
    {"method": "DELETE", "endpoint": "/tasks/task-1", "params": None},
    {"method": "DELETE", "endpoint": "/tasks/task-1", "params": {"files": "true"}},
    {"method": "GET", "endpoint": "/tasks/task-1/files", "params": None},
    {"method": "GET", "endpoint": "/tasks/task-1/files", "params": {"role": "output"}},
    {"method": "DELETE", "endpoint": "/tasks/task-1/files", "params": None},
    {"method": "DELETE", "endpoint": "/tasks/task-1/files", "params": {"role": "input"}},
]


def test_sync_task_files():
    client, calls = sync_client()

    client.tasks.delete("task-1")
    client.tasks.delete("task-1", files=True)
    assert client.tasks.files("task-1").data[0]["id"] == "file-1"
    client.tasks.files("task-1", role="output")
    assert client.tasks.delete_files("task-1").data["deleted"] == ["file-1"]
    client.tasks.delete_files("task-1", role="input")

    assert calls == EXPECTED


def test_delete_files_surfaces_skipped_entries():
    client, _ = sync_client(delete_payload=DELETED_PARTIAL)
    result = client.tasks.delete_files("task-1")
    assert result.data["deleted"] == ["file-1"]
    assert result.data["skipped"] == [
        {"id": "file-2", "reason": "referenced_by_other_task"},
    ]


def test_async_task_files():
    client, calls = async_client()

    async def run():
        await client.tasks.delete("task-1")
        await client.tasks.delete("task-1", files=True)
        assert (await client.tasks.files("task-1")).data[0]["id"] == "file-1"
        await client.tasks.files("task-1", role="output")
        assert (await client.tasks.delete_files("task-1")).data["deleted"] == ["file-1"]
        await client.tasks.delete_files("task-1", role="input")

    asyncio.run(run())
    assert calls == EXPECTED
