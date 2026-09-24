"""Sockets API (mocked _request) and open() dialling a fake WebSocket."""

import asyncio
from typing import Any, Dict, List

import pytest

from inferencesh import AsyncInference, Inference, LiveState, TaskStatus
from inferencesh.api.sockets import AsyncSocketsAPI, SocketsAPI
from inferencesh.models.response import Response

from test_live import FakeWS, tick

ACCESS = {"id": "sock-1", "url": "wss://relay.test/sockets/sock-1", "token": "tok", "expires_at": "2030-01-01T00:00:00Z"}
SOCKET = {"id": "sock-1", "task_id": "task-1"}
TASK = {"id": "task-1", "status": int(TaskStatus.RUNNING)}


def route(calls: List[Dict[str, Any]], answers: Dict[str, Any], method: str, endpoint: str, data: Any) -> Response:
    calls.append({"method": method.upper(), "endpoint": endpoint, "data": data})
    key = f"{method.upper()} {endpoint}"
    answer = answers.get(key, {"detail": "not found"})
    if callable(answer):
        answer = answer()
    return Response(answer)


@pytest.fixture(autouse=True)
def reset_dialed():
    FakeWS.dialed = []
    yield
    FakeWS.dialed = []


def sync_client(answers: Dict[str, Any]):
    client = Inference(api_key="test")
    calls: List[Dict[str, Any]] = []

    def fake(method, endpoint, *, params=None, data=None, headers=None, stream=False, timeout=None):
        return route(calls, answers, method, endpoint, data)

    client._request = fake  # type: ignore[method-assign]
    return client, calls


def async_client(answers: Dict[str, Any]):
    client = AsyncInference(api_key="test")
    calls: List[Dict[str, Any]] = []

    async def fake(method, endpoint, *, params=None, data=None, headers=None, timeout=None, expect_stream=False):
        return route(calls, answers, method, endpoint, data)

    client._request = fake  # type: ignore[method-assign]
    return client, calls


def requests(calls):
    return [f"{c['method']} {c['endpoint']}" for c in calls]


# ------------------------------------------------------------------- sync


def test_sync_sockets_http_methods():
    client, calls = sync_client({
        "GET /sockets/sock-1": SOCKET,
        "POST /sockets/list": {"items": [SOCKET]},
        "POST /sockets/sock-1/access": ACCESS,
        "DELETE /sockets/sock-1": None,
    })
    assert isinstance(client.sockets, SocketsAPI)
    assert client.sockets.get("sock-1")["id"] == "sock-1"
    assert client.sockets.for_task("task-1")["id"] == "sock-1"
    assert client.sockets.access("sock-1")["token"] == "tok"
    client.sockets.delete("sock-1")
    assert requests(calls) == ["GET /sockets/sock-1", "POST /sockets/list", "POST /sockets/sock-1/access", "DELETE /sockets/sock-1"]
    assert calls[1]["data"] == {"limit": 1, "filters": [{"field": "task_id", "operator": "eq", "value": "task-1"}]}


def test_sync_for_task_without_socket_is_none():
    client, _ = sync_client({"POST /sockets/list": {"items": []}})
    assert client.sockets.for_task("task-1") is None


def test_sync_open_points_at_the_async_client():
    client, _ = sync_client({})
    with pytest.raises(NotImplementedError, match="AsyncInference"):
        client.sockets.open(TASK)


# ------------------------------------------------------------------ async


async def test_async_sockets_http_methods():
    client, calls = async_client({
        "GET /sockets/sock-1": SOCKET,
        "POST /sockets/list": {"items": [SOCKET]},
        "POST /sockets/sock-1/access": ACCESS,
        "DELETE /sockets/sock-1": None,
    })
    assert isinstance(client.sockets, AsyncSocketsAPI)
    assert (await client.sockets.get("sock-1"))["id"] == "sock-1"
    assert (await client.sockets.for_task("task-1"))["id"] == "sock-1"
    assert (await client.sockets.access("sock-1"))["token"] == "tok"
    await client.sockets.delete("sock-1")
    assert requests(calls) == ["GET /sockets/sock-1", "POST /sockets/list", "POST /sockets/sock-1/access", "DELETE /sockets/sock-1"]
    assert calls[1]["data"]["filters"] == [{"field": "task_id", "operator": "eq", "value": "task-1"}]


async def test_open_dials_the_run_response_access_without_asking_for_anything():
    client, calls = async_client({})
    session = await client.sockets.open({**TASK, "socket": ACCESS}, ws_connect=FakeWS.dial, watch_task=False)
    assert calls == []
    assert FakeWS.dialed[0].url == "wss://relay.test/sockets/sock-1?access_token=tok"
    assert session.state == LiveState.WAITING
    await session.close()


async def test_open_finds_the_socket_of_a_task_id_and_issues_a_credential():
    client, calls = async_client({
        "GET /tasks/task-1": TASK,
        "POST /sockets/list": {"items": [SOCKET]},
        "POST /sockets/sock-1/access": ACCESS,
    })
    session = await client.sockets.open("task-1", ws_connect=FakeWS.dial, watch_task=False)
    assert requests(calls) == ["POST /sockets/list", "POST /sockets/sock-1/access"]  # the id is all it needs of the task
    assert len(FakeWS.dialed) == 1
    await session.close()


async def test_open_refuses_a_task_without_a_socket():
    client, _ = async_client({"POST /sockets/list": {"items": []}})
    with pytest.raises(ValueError, match="has no socket"):
        await client.sockets.open(TASK, ws_connect=FakeWS.dial)
    assert FakeWS.dialed == []


async def test_redial_renews_the_credential_through_the_api():
    client, calls = async_client({"POST /sockets/sock-1/access": {**ACCESS, "token": "tok-2"}})
    session = await client.sockets.open({**TASK, "socket": ACCESS}, ws_connect=FakeWS.dial, watch_task=False)
    FakeWS.dialed[0].server_close(1012, "restarting")
    await tick()
    assert requests(calls) == ["POST /sockets/sock-1/access"]
    assert FakeWS.dialed[1].url.endswith("access_token=tok-2")
    assert session.state == LiveState.WAITING
    await session.close()


async def test_open_follows_the_task_while_waiting_and_ends_when_it_fails():
    client, _ = async_client({})
    waited = []

    async def wait_for_completion(task_id, **kwargs):
        waited.append(task_id)
        raise RuntimeError("no module named x")

    client.wait_for_completion = wait_for_completion  # the client's own watch: SSE, reconciled by GET
    session = await client.sockets.open({**TASK, "socket": ACCESS}, ws_connect=FakeWS.dial)
    end = await asyncio.wait_for(session.ended, 1)
    assert waited == ["task-1"]
    assert end.task_ended is True
    assert end.reason == "no module named x"
    assert FakeWS.dialed[0].closed_with == (1000, "task ended")


async def test_open_stops_following_the_task_once_live():
    client, _ = async_client({})
    watch = {}

    async def wait_for_completion(task_id, **kwargs):
        try:
            await asyncio.sleep(3600)
        except asyncio.CancelledError:
            watch["cancelled"] = True
            raise

    client.wait_for_completion = wait_for_completion
    session = await client.sockets.open({**TASK, "socket": ACCESS}, ws_connect=FakeWS.dial)
    await tick()
    FakeWS.dialed[0].message("{}")
    await tick()
    assert session.state == LiveState.LIVE
    assert watch.get("cancelled") is True
    await session.close()


async def test_live_runs_the_task_and_opens_its_socket():
    client, calls = async_client({"POST /apps/run": {**TASK, "socket": ACCESS, "input": {"effect": "robot"}}})
    task, session = await client.live(
        {"app": "infsh/voice-loop", "function": "stream", "input": {"effect": "robot"}},
        ws_connect=FakeWS.dial,
        watch_task=False,
    )
    assert requests(calls) == ["POST /apps/run"]
    assert calls[0]["data"]["function"] == "stream"
    assert task["id"] == "task-1" and task["socket"] == ACCESS
    assert session.state == LiveState.WAITING
    assert FakeWS.dialed[0].url.endswith("access_token=tok")
    await session.close()
    assert session.end.by_caller is True
