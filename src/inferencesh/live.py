"""The caller's end of a stream task's socket, and the live fields of its schemas.

A stream function keeps a socket open with its caller for the life of the
task. The run response carries where to dial and a short-lived credential
(``task["socket"]``, a SocketAccess). The relay pairs this connection with the
worker's. Until the app's first frame arrives nobody may be on the other end
yet (the worker can still be pulling an image), so the session is ``waiting``,
not ``live``.

Frames follow the function's schemas (see ``split_live_schema``): a binary
frame is one item of the binary live field, a text frame is a JSON object
keyed by field name. The app side of the same convention is
``inferencesh.models.stream``.

Requires the ``async`` extra (``pip install inferencesh[async]``): the session
is built on ``aiohttp``, imported when the first socket is dialled.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Union,
)
from urllib.parse import quote

from .models.stream import CLEAR_KEY, ERROR_KEY, REDIAL_CODES, STREAM_FORMAT
from .types import SocketAccess

# --------------------------------------------------------------------------
# Live schema helpers
# --------------------------------------------------------------------------

JsonSchema = Dict[str, Any]


def is_live_field(schema: Optional[Mapping[str, Any]]) -> bool:
    """A property whose values travel over the socket: ``{"format": "stream"}``."""
    return bool(schema) and schema.get("format") == STREAM_FORMAT  # type: ignore[union-attr]


@dataclass(frozen=True)
class MediaType:
    type: str
    """e.g. ``"audio/pcm"``"""
    params: Dict[str, str] = field(default_factory=dict)
    """e.g. ``{"format": "s16le", "rate": "16000", "channels": "1"}``"""


def parse_media_type(value: Optional[str]) -> Optional[MediaType]:
    """Splits ``"audio/pcm;format=s16le;rate=16000"`` into its type and parameters."""
    if not value:
        return None
    parts = [part.strip() for part in value.split(";")]
    media_type = parts[0]
    if not media_type:
        return None
    params: Dict[str, str] = {}
    for part in parts[1:]:
        eq = part.find("=")
        if eq > 0:
            params[part[:eq].strip().lower()] = part[eq + 1:].strip()
    return MediaType(type=media_type.lower(), params=params)


@dataclass(frozen=True)
class PCMFormat:
    sample_rate: int
    channels: int


def pcm_format(media: Optional[MediaType]) -> Optional[PCMFormat]:
    """The PCM format of a media type, or None when it is not 16-bit PCM audio."""
    if media is None or media.type != "audio/pcm":
        return None
    fmt = media.params.get("format")
    if fmt and fmt != "s16le":
        return None
    try:
        sample_rate = int(media.params.get("rate", 16000))
        channels = int(media.params.get("channels", 1))
    except (TypeError, ValueError):
        return None
    if sample_rate <= 0 or channels <= 0:
        return None
    return PCMFormat(sample_rate=sample_rate, channels=channels)


@dataclass
class LiveField:
    key: str
    title: str
    description: Optional[str] = None
    binary: bool = False
    """Items are binary frames."""
    media: Optional[MediaType] = None
    """Set when binary."""
    alternatives: List[JsonSchema] = field(default_factory=list)
    """What one item can be, references resolved: the alternatives of an anyOf,
    or the single item schema. Empty for a binary field."""
    discriminator: Optional[str] = None
    """The property that tells the alternatives apart, when the schema names
    one (pydantic's ``discriminator.propertyName``)."""


def _deref(schema: JsonSchema, root: JsonSchema) -> JsonSchema:
    """Resolves a ``#/$defs/`` reference against the root, recursively. The
    result carries no top-level ``$ref`` (a validator ignores a ``$ref``'s
    siblings)."""
    ref = schema.get("$ref")
    defs = root.get("$defs")
    if not ref or not defs:
        return schema
    target = defs.get(ref.replace("#/$defs/", ""))
    if target is None:
        return schema
    # The reference's own fields (title, description) win over the target's.
    own = {key: value for key, value in schema.items() if key != "$ref"}
    return {**_deref(target, root), **own}


def _item_alternatives(items: JsonSchema, root: JsonSchema) -> List[JsonSchema]:
    resolved = _deref(items, root)
    options = resolved.get("anyOf") or resolved.get("oneOf")
    alternatives = [_deref(option, root) for option in options] if options else [resolved]
    # Each alternative must stand on its own (a form validates it without the
    # root), and nested references (an enum field, a nested model) still point
    # into the root's $defs, so they travel with it.
    defs = root.get("$defs")
    return [{**alt, "$defs": defs} for alt in alternatives] if defs else alternatives


class SplitLiveSchema(NamedTuple):
    ordinary: Optional[JsonSchema]
    """The schema of the ordinary properties: the request body."""
    live: List[LiveField]
    """What the socket carries."""


def split_live_schema(schema: Optional[JsonSchema]) -> SplitLiveSchema:
    """Splits a function schema into what a form renders (the ordinary
    properties) and what the socket carries (the live ones)."""
    if not schema or not schema.get("properties"):
        return SplitLiveSchema(schema or None, [])

    ordinary: Dict[str, JsonSchema] = {}
    live: List[LiveField] = []
    for key, prop in schema["properties"].items():
        if not is_live_field(prop):
            ordinary[key] = prop
            continue
        items = prop.get("items") or {}
        if isinstance(items, list):
            items = items[0] if items else {}
        resolved_items = _deref(items, schema)
        binary = resolved_items.get("format") == "binary"
        live.append(
            LiveField(
                key=key,
                title=prop.get("title") or key,
                description=prop.get("description"),
                binary=binary,
                media=parse_media_type(resolved_items.get("contentMediaType")) if binary else None,
                alternatives=[] if binary else _item_alternatives(items, schema),
                discriminator=None if binary else (resolved_items.get("discriminator") or {}).get("propertyName"),
            )
        )
    out = {**schema, "properties": ordinary}
    if "required" in schema:
        out["required"] = [key for key in schema["required"] if key in ordinary]
    return SplitLiveSchema(out, live)


def binary_live_field(live: List[LiveField]) -> Optional[LiveField]:
    """The schema's one binary live field. A binary frame carries no field name."""
    return next((f for f in live if f.binary), None)


def alternative_tag(schema: JsonSchema, discriminator: Optional[str] = None) -> Optional[str]:
    """The property whose constant names this alternative: the schema's
    discriminator, else ``type``, else the first property with a constant."""
    props = schema.get("properties") or {}
    constants = [key for key, prop in props.items() if isinstance(prop, dict) and "const" in prop]
    for key in ([discriminator] if discriminator else []) + ["type"] + constants:
        if key in constants:
            return key
    return None


def alternative_label(schema: JsonSchema, index: int, discriminator: Optional[str] = None) -> str:
    """A label for one alternative of a JSON live field: the constant that
    tags it (see ``alternative_tag``), else its title."""
    tag = alternative_tag(schema, discriminator)
    value = (schema.get("properties") or {}).get(tag, {}).get("const") if tag else None
    if isinstance(value, str):
        return value
    return schema.get("title") or f"option {index + 1}"


# --------------------------------------------------------------------------
# The session
# --------------------------------------------------------------------------


class LiveState(str, Enum):
    CONNECTING = "connecting"
    WAITING = "waiting"
    LIVE = "live"
    ENDED = "ended"


@dataclass(frozen=True)
class LiveEnd:
    code: int
    """The WebSocket close code, or 1006 when the session ended without one."""
    reason: str
    by_caller: bool
    """The caller asked for it."""
    task_ended: bool
    """The task ended before the app connected, so the session gave up waiting."""


class WSMsgType(IntEnum):
    """The values of ``aiohttp.WSMsgType`` the session reads, so a fake socket
    needs no aiohttp."""

    TEXT = 0x1
    BINARY = 0x2
    CLOSE = 0x8
    CLOSING = 0x100
    CLOSED = 0x101
    ERROR = 0x102


MAX_REDIALS = 5

class LiveUpdate(NamedTuple):
    """One thing the app sent, mapped to its output field: an item of a live
    field (bytes for the binary one) or a new value of an ordinary field."""

    field: str
    value: Any


Frame = Union[bytes, str, Dict[str, Any], LiveUpdate]
OnState = Callable[[LiveState, Optional[LiveEnd]], None]
OnBinary = Callable[[bytes], None]
OnPatch = Callable[[Dict[str, Any]], None]
OnClear = Callable[[str], None]
OnError = Callable[[Optional[str], str], None]
OnText = Callable[[str], None]
OnUpdate = Callable[[LiveUpdate], None]
Renew = Callable[[], Awaitable[SocketAccess]]
WsConnect = Callable[[str], Awaitable[Any]]

_DONE = object()


def access_url(access: Mapping[str, Any]) -> str:
    """Where to dial: the credential rides in the query, as the relay documents
    (a browser cannot set headers on a WebSocket, and the relay accepts either)."""
    url = access["url"]
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}access_token={quote(access['token'], safe='')}"


class AsyncLiveSession:
    """One end of a stream task's socket, as the caller holds it.

    States: ``connecting`` → ``waiting`` (the relay accepted the connection)
    → ``live`` (the app's first frame) → ``ended``.

    Frames the app sends come out of ``async for item in session``: ``bytes``
    for a binary frame, a ``dict`` for a JSON object (a partial output object
    keyed by field name), a ``str`` for any other text. A frame goes to
    ``on_binary`` / ``on_patch`` / ``on_text`` instead when that callback is
    set, so a caller using callbacks does not have to drain the iterator.

    Given the function's schemas, the session maps frames to fields the way the
    app's ``Live`` does: pass ``output_schema`` and frames arrive as
    ``LiveUpdate(field, value)`` (to ``on_update``, or from the iterator);
    pass ``input_schema`` and ``send_field(field, value)`` sends a binary frame
    or a JSON one as the field requires.

    Control frames (reserved keys start with ``$``) have their own callbacks:
    ``{"$clear": field}`` goes to ``on_clear`` (drop what you buffered of that
    field: the user talked over the answer), ``{"$error": {...}}`` to
    ``on_error(field, message)``. Apps on SDKs before 0.10.1 send the error as
    ``{"error": {...}}``; it is treated the same unless the output has an
    ``error`` field. Without the callback a control frame stays in its patch.

    ``send(data)`` sends ``bytes`` as a binary frame and a ``dict`` as a JSON
    text frame. ``close()`` ends the stream: the function returns and the task
    completes. ``ended`` settles with a LiveEnd, however the session ended.

    Args:
        access: Where to dial and the credential (``task["socket"]``).
        renew: Issues a fresh credential for a redial (``POST /sockets/{id}/access``).
        task_watch: A coroutine or Future that finishes when the task ends
            (raising when it failed or was cancelled). While the session is
            still waiting for the app, the task ending ends the session; once
            live it is cancelled, since the task's fate then shows on the socket.
        on_state, on_binary, on_patch, on_text, on_update, on_clear, on_error:
            Callbacks; see above.
        input_schema, output_schema: The function's schemas, to map frames
            to fields; see above.
        ws_connect: ``async (url) -> ws`` to dial with, for tests or another
            transport. Defaults to ``aiohttp.ClientSession().ws_connect``.
    """

    def __init__(
        self,
        access: SocketAccess,
        *,
        renew: Optional[Renew] = None,
        task_watch: Optional[Union[Awaitable[Any], "asyncio.Future[Any]"]] = None,
        on_state: Optional[OnState] = None,
        on_binary: Optional[OnBinary] = None,
        on_patch: Optional[OnPatch] = None,
        on_clear: Optional[OnClear] = None,
        on_error: Optional[OnError] = None,
        on_text: Optional[OnText] = None,
        on_update: Optional[OnUpdate] = None,
        input_schema: Optional[JsonSchema] = None,
        output_schema: Optional[JsonSchema] = None,
        ws_connect: Optional[WsConnect] = None,
    ) -> None:
        self._access = access
        self._renew = renew
        self._task_watch_src = task_watch
        self._task_watch: Optional["asyncio.Future[Any]"] = None
        self._watcher: Optional["asyncio.Task[None]"] = None
        self._on_state = on_state
        self._on_binary = on_binary
        self._on_patch = on_patch
        self._on_clear = on_clear
        self._on_error = on_error
        self._on_text = on_text
        self._on_update = on_update
        self._mapped = output_schema is not None
        out_live = split_live_schema(output_schema).live
        self._out_binary = next((f.key for f in out_live if f.binary), None)
        self._out_fields = set((output_schema or {}).get("properties") or {})
        self._in_binary = next((f.key for f in split_live_schema(input_schema).live if f.binary), None)
        self._in_known = input_schema is not None
        self._ws_connect = ws_connect or self._dial_aiohttp

        self._state = LiveState.CONNECTING
        self._ws: Any = None
        self._reader: Optional["asyncio.Task[None]"] = None
        self._http: Any = None  # the aiohttp session behind the current socket
        self._closed_by_caller = False
        self._redials = 0
        self._end: Optional[LiveEnd] = None
        self._ended: Optional["asyncio.Future[LiveEnd]"] = None
        self._frames: "asyncio.Queue[Any]" = asyncio.Queue()

    # ------------------------------------------------------------- state

    @property
    def state(self) -> LiveState:
        return self._state

    @property
    def is_open(self) -> bool:
        return self._ws is not None and not getattr(self._ws, "closed", False)

    @property
    def end(self) -> Optional[LiveEnd]:
        """How the session ended, once it has."""
        return self._end

    @property
    def ended(self) -> "asyncio.Future[LiveEnd]":
        """Settles when the session has ended, however it ended."""
        return self._ended_future()

    def _ended_future(self) -> "asyncio.Future[LiveEnd]":
        if self._ended is None:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.get_event_loop()
            self._ended = loop.create_future()
            if self._end is not None:
                self._ended.set_result(self._end)
        return self._ended

    def _set_state(self, state: LiveState, end: Optional[LiveEnd] = None) -> None:
        self._state = state
        if self._on_state:
            self._on_state(state, end)

    # ----------------------------------------------------------- dialling

    async def _dial_aiohttp(self, url: str) -> Any:
        from .client import _require_aiohttp

        aiohttp = await _require_aiohttp()
        http = aiohttp.ClientSession()
        try:
            ws = await http.ws_connect(url)
        except BaseException:
            await http.close()
            raise
        self._http = http
        return ws

    async def _close_http(self) -> None:
        http, self._http = self._http, None
        if http is not None:
            try:
                await http.close()
            except Exception:
                pass

    async def connect(self) -> None:
        """Dials the relay. Returns once the relay accepted the connection
        (``waiting``); the app's first frame makes it ``live``."""
        self._set_state(LiveState.CONNECTING)
        self._watch_task()
        try:
            ws = await self._ws_connect(access_url(self._access))
        except Exception as exc:
            await self._finish(LiveEnd(code=1006, reason=str(exc) or "could not connect", by_caller=False, task_ended=False))
            raise
        if self._state == LiveState.ENDED or self._closed_by_caller:
            # The task ended, or the caller closed, while we were dialling.
            await self._close_ws(ws, 1000, "done")
            return
        self._ws = ws
        self._set_state(LiveState.WAITING)
        self._reader = asyncio.ensure_future(self._read(ws))

    async def _read(self, ws: Any) -> None:
        code = 1006
        reason = ""
        try:
            while True:
                try:
                    msg = await ws.receive()
                except Exception as exc:
                    reason = str(exc)
                    break
                mtype = msg.type
                if mtype == WSMsgType.TEXT:
                    self._deliver_text(msg.data)
                elif mtype == WSMsgType.BINARY:
                    self._deliver_binary(bytes(msg.data))
                elif mtype == WSMsgType.CLOSE:
                    code = int(msg.data) if msg.data is not None else 1005
                    reason = getattr(msg, "extra", None) or ""
                    break
                elif mtype in (WSMsgType.CLOSING, WSMsgType.CLOSED, WSMsgType.ERROR):
                    code = getattr(ws, "close_code", None) or 1006
                    if mtype == WSMsgType.ERROR:
                        reason = str(msg.data) if msg.data is not None else ""
                    break
                # ping/pong/continuation: nothing to do
        except asyncio.CancelledError:
            return
        await self._on_close(ws, code, reason)

    def _went_live(self) -> None:
        if self._state != LiveState.LIVE:
            self._set_state(LiveState.LIVE)
            self._stop_watch()  # the app is there; the task's fate now shows on the socket

    def _deliver_text(self, data: Any) -> None:
        self._went_live()
        text = data.decode() if isinstance(data, (bytes, bytearray)) else str(data)
        try:
            patch = json.loads(text)
        except ValueError:
            patch = None
        if not isinstance(patch, dict):
            # Not a patch: text the app sent as text (a raw Socket can).
            if self._on_text:
                self._on_text(text)
            else:
                self._frames.put_nowait(text)
            return
        arrived_empty = not patch
        if self._on_clear and isinstance(patch.get(CLEAR_KEY), str):
            self._on_clear(patch.pop(CLEAR_KEY))
        if self._on_error:
            key = ERROR_KEY if ERROR_KEY in patch else "error" if self._legacy_error(patch) else None
            if key is not None:
                err = patch.pop(key)
                err = err if isinstance(err, dict) else {"message": str(err)}
                self._on_error(err.get("field"), str(err.get("message") or json.dumps(err)))
        if not patch and not arrived_empty:
            return  # it was only control frames
        if self._on_patch:
            self._on_patch(patch)
        elif self._mapped:
            for key, value in patch.items():
                self._deliver_update(LiveUpdate(key, value))
        else:
            self._frames.put_nowait(patch)

    def _legacy_error(self, patch: Dict[str, Any]) -> bool:
        """``{"error": {"message": ...}}`` from an app on an SDK before 0.10.1,
        unless the output really has an ``error`` field."""
        err = patch.get("error")
        return isinstance(err, dict) and "message" in err and "error" not in self._out_fields

    def _deliver_update(self, update: LiveUpdate) -> None:
        if self._on_update:
            self._on_update(update)
        else:
            self._frames.put_nowait(update)

    def _deliver_binary(self, data: bytes) -> None:
        self._went_live()
        if self._on_binary:
            self._on_binary(data)
        elif self._mapped and self._out_binary:
            self._deliver_update(LiveUpdate(self._out_binary, data))
        else:
            self._frames.put_nowait(data)

    async def _on_close(self, ws: Any, code: int, reason: str) -> None:
        if self._ws is not ws:
            return  # detached by _close_socket: its close must not end the session a second time
        self._ws = None
        await self._close_http()
        waiting = self._state != LiveState.LIVE
        if not self._closed_by_caller and waiting and code in REDIAL_CODES and self._redials < MAX_REDIALS:
            self._redials += 1
            await self._redial()
            return
        await self._finish(LiveEnd(code=code, reason=reason, by_caller=self._closed_by_caller, task_ended=False))

    async def _redial(self) -> None:
        try:
            if self._renew:
                self._access = await self._renew()
            if self._state != LiveState.ENDED and not self._closed_by_caller:
                await self.connect()
        except Exception as exc:
            await self._finish(LiveEnd(code=1006, reason=str(exc) or "could not redial", by_caller=False, task_ended=False))

    # --------------------------------------------------------- task watch

    def _watch_task(self) -> None:
        if self._task_watch_src is None or self._task_watch is not None:
            return
        self._task_watch = asyncio.ensure_future(self._task_watch_src)
        self._watcher = asyncio.ensure_future(self._follow_task(self._task_watch))

    async def _follow_task(self, watch: "asyncio.Future[Any]") -> None:
        try:
            await watch
        except asyncio.CancelledError:
            return
        except Exception as exc:
            reason = str(exc) or "task failed"
        else:
            reason = "the task ended before the app connected"
        if self._state in (LiveState.ENDED, LiveState.LIVE):
            return
        await self._close_socket(1000, "task ended")
        await self._finish(LiveEnd(code=1000, reason=reason, by_caller=False, task_ended=True))

    def _stop_watch(self) -> None:
        if self._task_watch is not None and not self._task_watch.done():
            self._task_watch.cancel()

    # ------------------------------------------------------------ ending

    async def _finish(self, end: LiveEnd) -> None:
        if self._state == LiveState.ENDED:
            return
        self._end = end
        self._stop_watch()
        self._set_state(LiveState.ENDED, end)
        fut = self._ended_future()
        if not fut.done():
            fut.set_result(end)
        self._frames.put_nowait(_DONE)
        await self._close_http()

    async def _close_ws(self, ws: Any, code: int, reason: str) -> None:
        try:
            await ws.close(code=code, message=reason.encode())
        except Exception:
            pass

    async def _close_socket(self, code: int, reason: str) -> None:
        ws, self._ws = self._ws, None  # its close must not end the session a second time
        if ws is None:
            return
        await self._close_ws(ws, code, reason)
        reader = self._reader
        if reader is not None and not reader.done() and reader is not asyncio.current_task():
            reader.cancel()
            try:
                await reader
            except (asyncio.CancelledError, Exception):
                pass
        await self._close_http()

    async def close(self) -> None:
        """Ends the stream; the function returns and the task completes."""
        self._closed_by_caller = True
        await self._close_socket(1000, "done")
        await self._finish(LiveEnd(code=1000, reason="done", by_caller=True, task_ended=False))

    # ----------------------------------------------------------- sending

    async def send(self, data: Union[bytes, bytearray, memoryview, Mapping[str, Any]]) -> None:
        """``bytes`` → one item of the input's binary live field; a mapping →
        a JSON text frame: a partial input object keyed by field name."""
        if isinstance(data, (bytes, bytearray, memoryview)):
            await self.send_binary(data)
        elif isinstance(data, Mapping):
            await self.send_patch(data)
        else:
            raise TypeError(f"send() takes bytes or a dict, not {type(data).__name__}")

    async def send_binary(self, data: Union[bytes, bytearray, memoryview]) -> None:
        """One item of the input's binary live field."""
        if self.is_open:
            await self._ws.send_bytes(data)

    async def send_field(self, field: str, value: Any) -> None:
        """One item of an input live field, or a new value of an ordinary one:
        a binary frame for the binary live field, a JSON frame otherwise.
        Needs ``input_schema``."""
        if not self._in_known:
            raise ValueError("send_field needs the function's input_schema")
        if field == self._in_binary:
            await self.send_binary(value)
        else:
            await self.send_patch({field: value})

    async def send_patch(self, patch: Mapping[str, Any]) -> None:
        """A partial input object keyed by field name."""
        if self.is_open:
            await self._ws.send_str(json.dumps(dict(patch)))

    # --------------------------------------------------------- iteration

    def __aiter__(self) -> "AsyncLiveSession":
        return self

    async def __anext__(self) -> Frame:
        item = await self._frames.get()
        if item is _DONE:
            self._frames.put_nowait(_DONE)  # a later iteration ends too
            raise StopAsyncIteration
        return item

    async def __aenter__(self) -> "AsyncLiveSession":
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if self._state != LiveState.ENDED:
            await self.close()


__all__ = [
    "STREAM_FORMAT",
    "JsonSchema",
    "MediaType",
    "PCMFormat",
    "LiveField",
    "SplitLiveSchema",
    "is_live_field",
    "parse_media_type",
    "pcm_format",
    "split_live_schema",
    "binary_live_field",
    "alternative_label",
    "alternative_tag",
    "LiveState",
    "LiveUpdate",
    "LiveEnd",
    "AsyncLiveSession",
    "REDIAL_CODES",
    "MAX_REDIALS",
    "WSMsgType",
    "access_url",
]
