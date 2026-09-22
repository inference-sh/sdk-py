"""AsyncLiveSession against a fake WebSocket (no network, no aiohttp)."""

import asyncio
import json
from dataclasses import dataclass
from typing import Any, List, Optional

import pytest

from inferencesh import AsyncLiveSession, LiveEnd, LiveState, binary_live_field, parse_media_type, pcm_format, split_live_schema
from inferencesh.live import WSMsgType


@dataclass
class Msg:
    type: int
    data: Any = None
    extra: str = ""


class FakeWS:
    """An aiohttp-like WebSocket the test drives: every dial is recorded, and
    the test feeds and closes it."""

    dialed: List["FakeWS"] = []

    def __init__(self, url: str) -> None:
        self.url = url
        self.queue: "asyncio.Queue[Msg]" = asyncio.Queue()
        self.sent: List[Any] = []
        self.closed = False
        self.close_code: Optional[int] = None
        self.closed_with: Optional[tuple] = None
        FakeWS.dialed.append(self)

    @classmethod
    async def dial(cls, url: str) -> "FakeWS":
        return cls(url)

    # --- what the session calls
    async def receive(self) -> Msg:
        return await self.queue.get()

    async def send_bytes(self, data: bytes) -> None:
        self.sent.append(data)

    async def send_str(self, data: str) -> None:
        self.sent.append(data)

    async def close(self, code: int = 1000, message: bytes = b"") -> bool:
        self.closed_with = (code, message.decode())
        if self.closed:
            return False
        self.closed = True
        self.close_code = code
        self.queue.put_nowait(Msg(WSMsgType.CLOSING))
        return True

    # --- what the test does
    def message(self, data: Any) -> None:
        kind = WSMsgType.BINARY if isinstance(data, (bytes, bytearray)) else WSMsgType.TEXT
        self.queue.put_nowait(Msg(kind, data))

    def server_close(self, code: int, reason: str = "") -> None:
        if self.closed:
            return
        self.closed = True
        self.close_code = code
        self.queue.put_nowait(Msg(WSMsgType.CLOSE, code, reason))


def access(n: int = 1) -> dict:
    return {"id": "sock-1", "url": "wss://relay.test/sockets/sock-1", "token": f"tok-{n}", "expires_at": "2030-01-01T00:00:00Z"}


async def tick(n: int = 4) -> None:
    for _ in range(n):
        await asyncio.sleep(0)


@pytest.fixture(autouse=True)
def reset_dialed():
    FakeWS.dialed = []
    yield
    FakeWS.dialed = []


class Started:
    def __init__(self, session: AsyncLiveSession) -> None:
        self.session = session
        self.states: List[tuple] = []
        self.patches: List[dict] = []
        self.binaries: List[bytes] = []

    @property
    def ws(self) -> FakeWS:
        return FakeWS.dialed[-1]


async def start(*, callbacks: bool = True, **options: Any) -> Started:
    holder: Started
    handlers = {}
    if callbacks:
        handlers = {
            "on_state": lambda state, end: holder.states.append((state, end)),
            "on_patch": lambda patch: holder.patches.append(patch),
            "on_binary": lambda data: holder.binaries.append(data),
        }
    session = AsyncLiveSession(access(), ws_connect=FakeWS.dial, **handlers, **options)
    holder = Started(session)
    await session.connect()
    return holder


# ------------------------------------------------------------------ session


async def test_credential_in_query_then_waiting_then_live_on_first_frame():
    s = await start()
    assert s.ws.url == "wss://relay.test/sockets/sock-1?access_token=tok-1"
    assert s.session.state == LiveState.WAITING
    assert s.session.state == "waiting"
    assert s.session.is_open

    s.ws.message(json.dumps({"effect": "robot"}))
    await tick()
    assert s.session.state == LiveState.LIVE
    assert s.patches == [{"effect": "robot"}]

    pcm = bytes(8)
    s.ws.message(pcm)
    s.ws.message("not json")
    await tick()
    assert s.binaries == [pcm]
    assert s.patches[1] == {"text": "not json"}
    assert [st for st, _ in s.states] == [LiveState.CONNECTING, LiveState.WAITING, LiveState.LIVE]


async def test_iteration_yields_bytes_and_dicts_and_ends_with_the_session():
    s = await start(callbacks=False)
    s.ws.message(b"\x01\x02")
    s.ws.message('{"transcript": {"text": "hi"}}')
    s.ws.message("[1, 2]")  # a JSON frame that is not an object is dropped

    async def collect():
        return [item async for item in s.session]

    collector = asyncio.ensure_future(collect())
    await tick()
    s.ws.server_close(1000, "app returned")
    items = await asyncio.wait_for(collector, 1)
    assert items == [b"\x01\x02", {"transcript": {"text": "hi"}}]
    assert s.session.state == LiveState.ENDED
    end = await asyncio.wait_for(s.session.ended, 1)
    assert end == LiveEnd(code=1000, reason="app returned", by_caller=False, task_ended=False)
    assert s.session.end == end
    # A later iteration ends immediately too.
    assert [item async for item in s.session] == []


async def test_send_routes_bytes_to_binary_and_dicts_to_json_frames():
    s = await start()
    await s.session.send(b"\x01\x02\x03")
    await s.session.send({"voice": "eve"})
    await s.session.send_binary(bytearray(b"\x04"))
    await s.session.send_patch({"gain": 2})
    assert s.ws.sent == [b"\x01\x02\x03", '{"voice": "eve"}', b"\x04", '{"gain": 2}']
    with pytest.raises(TypeError):
        await s.session.send("text")  # type: ignore[arg-type]

    s.ws.server_close(1000)
    await tick()
    await s.session.send(b"late")  # dropped: nothing is open
    assert s.ws.sent[-1] == '{"gain": 2}'


async def test_redials_with_a_fresh_credential_when_dropped_before_the_app_came():
    renews = []

    async def renew():
        renews.append(1)
        return access(2)

    s = await start(renew=renew)
    s.ws.server_close(1012, "restarting")
    await tick()
    assert len(renews) == 1
    assert len(FakeWS.dialed) == 2
    assert "access_token=tok-2" in s.ws.url
    assert s.session.state == LiveState.WAITING

    s.ws.message("{}")
    await tick()
    assert s.session.state == LiveState.LIVE
    assert not [st for st, _ in s.states if st == LiveState.ENDED]


async def test_no_redial_once_frames_have_flowed():
    async def renew():
        raise AssertionError("must not renew once live")

    s = await start(renew=renew)
    s.ws.message("{}")
    await tick()
    s.ws.server_close(1012, "restarting")
    await tick()
    assert len(FakeWS.dialed) == 1
    assert s.session.state == LiveState.ENDED
    assert s.states[-1][1] == LiveEnd(code=1012, reason="restarting", by_caller=False, task_ended=False)
    assert (await s.session.ended).code == 1012


async def test_gives_up_after_five_redials():
    async def renew():
        return access()

    s = await start(renew=renew)
    for i in range(6):
        FakeWS.dialed[i].server_close(1013, "peer did not come")
        await tick()
    assert len(FakeWS.dialed) == 6
    assert s.session.state == LiveState.ENDED
    assert s.session.end.code == 1013


async def test_ends_when_the_caller_closes_and_reports_it_as_such():
    s = await start()
    await s.session.close()
    assert s.ws.closed_with == (1000, "done")
    assert s.session.state == LiveState.ENDED
    end = s.states[-1][1]
    assert end.by_caller is True and end.code == 1000
    await tick()
    assert len([st for st, _ in s.states if st == LiveState.ENDED]) == 1


async def test_caller_close_does_not_redial():
    async def renew():
        raise AssertionError("must not renew after a caller close")

    s = await start(renew=renew)
    await s.session.close()
    await tick()
    assert s.session.state == LiveState.ENDED
    assert len(FakeWS.dialed) == 1


async def test_close_from_inside_a_callback():
    holder = {}

    def on_patch(patch):
        holder["task"] = asyncio.ensure_future(holder["session"].close())

    session = AsyncLiveSession(access(), ws_connect=FakeWS.dial, on_patch=on_patch)
    holder["session"] = session
    await session.connect()
    FakeWS.dialed[-1].message("{}")
    await tick()
    await asyncio.wait_for(holder["task"], 1)
    assert session.state == LiveState.ENDED
    assert session.end.by_caller is True


async def test_gives_up_waiting_when_the_task_fails_before_the_app_connected():
    fail: "asyncio.Future[Any]" = asyncio.get_running_loop().create_future()
    s = await start(task_watch=fail)
    fail.set_exception(RuntimeError('function "stream" failed: no module named x'))
    await tick()
    assert s.session.state == LiveState.ENDED
    assert s.states[-1][1] == LiveEnd(code=1000, reason='function "stream" failed: no module named x', by_caller=False, task_ended=True)
    assert s.ws.closed_with == (1000, "task ended")
    # The socket's own close report must not end the session a second time.
    await tick()
    assert len([st for st, _ in s.states if st == LiveState.ENDED]) == 1


async def test_task_completing_before_the_app_connected_ends_the_session():
    async def watch():
        await asyncio.sleep(0)
        return {"status": "completed"}

    s = await start(task_watch=watch())
    await tick()
    end = await asyncio.wait_for(s.session.ended, 1)
    assert end.task_ended is True and end.code == 1000


async def test_stops_following_the_task_once_the_app_is_there():
    complete: "asyncio.Future[Any]" = asyncio.get_running_loop().create_future()
    s = await start(task_watch=complete)
    s.ws.message("{}")
    await tick()
    assert complete.cancelled()  # the watch was stopped
    assert s.session.state == LiveState.LIVE


async def test_task_watch_is_cancelled_when_the_session_ends():
    watch: "asyncio.Future[Any]" = asyncio.get_running_loop().create_future()
    s = await start(task_watch=watch)
    s.ws.server_close(1000, "gone")
    await tick()
    assert s.session.state == LiveState.ENDED
    assert watch.cancelled()


async def test_connect_failure_ends_the_session_and_raises():
    async def refuse(url):
        raise OSError("connection refused")

    session = AsyncLiveSession(access(), ws_connect=refuse)
    with pytest.raises(OSError):
        await session.connect()
    assert session.state == LiveState.ENDED
    assert session.end == LiveEnd(code=1006, reason="connection refused", by_caller=False, task_ended=False)


async def test_async_with_closes_the_session():
    async with AsyncLiveSession(access(), ws_connect=FakeWS.dial) as session:
        await session.connect()
        assert session.state == LiveState.WAITING
    assert session.state == LiveState.ENDED
    assert session.end.by_caller is True


# ------------------------------------------------------------ schema helpers


TALK_INPUT = {
    "$defs": {
        "Interrupt": {"title": "Interrupt", "type": "object", "properties": {"type": {"const": "interrupt", "type": "string"}}},
        "UserText": {"title": "UserText", "type": "object", "properties": {"type": {"const": "text"}, "text": {"type": "string"}}},
    },
    "type": "object",
    "properties": {
        "voice": {"type": "string", "default": "ara"},
        "gain": {"type": "number", "default": 1.0},
        "audio": {
            "type": "array",
            "format": "stream",
            "title": "Audio",
            "items": {"type": "string", "format": "binary", "contentMediaType": "audio/pcm;format=s16le;rate=16000;channels=1"},
        },
        "events": {
            "type": "array",
            "format": "stream",
            "items": {"anyOf": [{"$ref": "#/$defs/Interrupt"}, {"$ref": "#/$defs/UserText", "title": "Text"}]},
        },
    },
    "required": ["voice", "audio"],
}


def test_split_live_schema_separates_ordinary_from_live():
    ordinary, live = split_live_schema(TALK_INPUT)
    assert set(ordinary["properties"]) == {"voice", "gain"}
    assert ordinary["required"] == ["voice"]
    assert [f.key for f in live] == ["audio", "events"]

    audio = binary_live_field(live)
    assert audio is not None and audio.key == "audio" and audio.title == "Audio"
    assert audio.media.type == "audio/pcm"
    assert pcm_format(audio.media).sample_rate == 16000
    assert audio.alternatives == []

    events = live[1]
    assert events.binary is False and events.media is None
    assert [alt["title"] for alt in events.alternatives] == ["Interrupt", "Text"]  # the reference's title wins
    assert events.alternatives[1]["properties"]["text"] == {"type": "string"}


def test_split_live_schema_without_properties_passes_through():
    assert split_live_schema(None) == (None, [])
    assert split_live_schema({"type": "string"}) == ({"type": "string"}, [])
    assert binary_live_field([]) is None


def test_parse_media_type_and_pcm_format():
    media = parse_media_type("Audio/PCM; Rate=24000 ; channels=2")
    assert media.type == "audio/pcm"
    assert media.params == {"rate": "24000", "channels": "2"}
    assert pcm_format(media) == pcm_format(parse_media_type("audio/pcm;rate=24000;channels=2"))
    assert pcm_format(media).channels == 2
    assert pcm_format(parse_media_type("audio/pcm")).sample_rate == 16000
    assert pcm_format(parse_media_type("audio/pcm;format=f32le")) is None
    assert pcm_format(parse_media_type("audio/pcm;rate=abc")) is None
    assert pcm_format(parse_media_type("audio/wav")) is None
    assert parse_media_type("") is None
    assert parse_media_type(None) is None
    assert pcm_format(None) is None
