"""Live fields: input and output that flow over a stream function's socket.

A stream function's input is still its input model. Some of its fields are
live: their values arrive over the socket while the task runs, instead of in
the request body. The output model works the same way in the other direction::

    class TalkInput(BaseAppInput):
        voice: Voice = "ara"                        # ordinary: set at the start
        audio: Stream[PCM16(16000)]                 # live media
        events: Stream[Union[Interrupt, UserText]]  # live typed messages

    class TalkOutput(BaseAppOutput):
        audio: Stream[PCM16(24000)]
        seconds: float = 0

In the JSON schema a live field is an array delivered over time, marked
``"format": "stream"`` the way a file field is marked ``"format": "file"``::

    "audio": {"type": "array", "format": "stream",
              "items": {"type": "string", "format": "binary",
                        "contentMediaType": "audio/pcm;format=s16le;rate=16000;channels=1"}}

Live fields are never required, so the request body is the ordinary fields
only. ``File`` and ``Stream`` are siblings: the same media, by reference or
live.

On the wire:

* a binary frame is one item of the model's binary live field (a model has at
  most one per direction, because a binary frame carries no field name);
* a JSON text frame is a partial object of the model keyed by field name:
  ``{"events": {"type": "interrupt"}}`` is one item of a live field, and
  ``{"voice": "eve"}`` changes an ordinary field while the task runs.

``Live`` applies that mapping to a socket, with the models as the contract.
"""

from __future__ import annotations

import json
from typing import Any, AsyncIterator, Dict, Generic, NamedTuple, Optional, Type, TypeVar, get_args, get_origin

from pydantic import BaseModel, Field, GetCoreSchemaHandler, GetJsonSchemaHandler, TypeAdapter, ValidationError
from pydantic_core import core_schema
from typing_extensions import Annotated

T = TypeVar("T")

STREAM_FORMAT = "stream"


class Stream(Generic[T]):
    """A field whose values travel over the socket while the task runs.

    The value on a model instance is an empty placeholder: items are not kept.
    Read and write them with ``Live``.
    """

    def __repr__(self) -> str:
        return "Stream()"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Stream)

    def __hash__(self) -> int:
        return hash(Stream)

    @classmethod
    def __get_pydantic_core_schema__(cls, source: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        args = get_args(source)
        item = handler.generate_schema(args[0]) if args else core_schema.any_schema()
        # The schema is a list of items, which is what the JSON schema should
        # say. Validation never sees items, though: whatever a caller puts in
        # the request body for a live field is dropped (its items come over
        # the socket), and the value on the model is the placeholder.
        items = core_schema.no_info_before_validator_function(lambda _value: [], core_schema.list_schema(item))
        placeholder = core_schema.no_info_after_validator_function(
            lambda _items: cls(),
            items,
            serialization=core_schema.plain_serializer_function_ser_schema(lambda _value: []),
        )
        return core_schema.with_default_schema(placeholder, default_factory=cls)

    @classmethod
    def __get_pydantic_json_schema__(cls, schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler) -> Dict[str, Any]:
        out = handler(schema)
        out["format"] = STREAM_FORMAT
        out.pop("default", None)
        return out


def media(content_type: str, *, description: Optional[str] = None) -> Any:
    """Binary items of a media type, e.g. ``Stream[media("image/jpeg")]``."""
    return Annotated[bytes, Field(description=description, json_schema_extra={"contentMediaType": content_type})]


def PCM16(rate: int = 16000, channels: int = 1) -> Any:  # noqa: N802 - reads as a type
    """Raw 16-bit little-endian PCM audio. One frame is one chunk of samples;
    20 ms (``rate / 50`` samples) is the usual size for live audio."""
    return media(f"audio/pcm;format=s16le;rate={rate};channels={channels}")


class Update(NamedTuple):
    """One thing the caller sent: an item of a live field, or a new value for
    an ordinary field (already applied to the input model)."""

    field: str
    value: Any


def _item_type(annotation: Any) -> Optional[Any]:
    """The T of ``Stream[T]`` (through Optional/Annotated), or None."""
    origin = get_origin(annotation)
    if origin is Stream:
        args = get_args(annotation)
        return args[0] if args else Any
    if annotation is Stream:
        return Any
    for arg in get_args(annotation):
        found = _item_type(arg)
        if found is not None:
            return found
    return None


def _is_binary(item: Any) -> bool:
    if item is bytes:
        return True
    if get_origin(item) is Annotated:
        return _is_binary(get_args(item)[0])
    return False


def live_fields(model: Type[BaseModel]) -> Dict[str, Any]:
    """The model's live fields and their item types."""
    found = {}
    for name, info in model.model_fields.items():
        item = _item_type(info.annotation)
        if item is None and info.metadata:
            item = next((i for i in (_item_type(m) for m in info.metadata) if i is not None), None)
        if item is not None:
            found[name] = item
    return found


def binary_field(model: Type[BaseModel]) -> Optional[str]:
    """The model's binary live field. More than one is an error: a binary
    frame carries no field name."""
    names = [name for name, item in live_fields(model).items() if _is_binary(item)]
    if len(names) > 1:
        raise TypeError(
            f"{model.__name__} has {len(names)} binary live fields ({', '.join(names)}); "
            "a model can have one per direction because a binary frame carries no field name"
        )
    return names[0] if names else None


class Live:
    """A socket read and written through the function's models.

    ::

        async def talk(self, input_data: TalkInput, socket: Socket) -> TalkOutput:
            live = Live(socket, input_data, TalkOutput)
            async for update in live:
                if update.field == "audio":
                    await live.send(audio=process(update.value, input_data.voice))
                elif update.field == "events":
                    ...                      # update.value is an Interrupt or a UserText
                # an ordinary field (voice) is already set on input_data
            return TalkOutput(seconds=...)

    A frame that does not fit the input model is answered with
    ``{"error": {"field": ..., "message": ...}}`` and skipped; the stream
    goes on.

    The function may instead be an async generator (``-> AsyncGenerator[TalkOutput,
    None]``): each yield is a cumulative snapshot of the task's output, sent as a
    task update rather than over the socket, and the last yield (after the loop,
    once the caller closes) is the result.
    """

    def __init__(self, socket: Any, input_data: BaseModel, output_type: Type[BaseModel]):
        self.socket = socket
        self.input = input_data
        self._in_live = live_fields(type(input_data))
        self._in_binary = binary_field(type(input_data))
        self._out_live = live_fields(output_type)
        self._out_binary = binary_field(output_type)
        self._out_fields = output_type.model_fields
        self._adapters: Dict[str, TypeAdapter] = {}
        self._refused_binary = False

    def _adapter(self, key: str, annotation: Any) -> TypeAdapter:
        if key not in self._adapters:
            self._adapters[key] = TypeAdapter(annotation)
        return self._adapters[key]

    def __aiter__(self) -> AsyncIterator[Update]:
        return self._updates()

    async def _updates(self) -> AsyncIterator[Update]:
        async for frame in self.socket:
            for update in await self._read(frame):
                yield update

    async def _read(self, frame: Any) -> list:
        if isinstance(frame, (bytes, bytearray, memoryview)):
            if self._in_binary is None:
                # Once: a caller streaming audio to the wrong function would
                # otherwise get an error frame for every frame it sends.
                if not self._refused_binary:
                    self._refused_binary = True
                    await self._refuse(None, "this function takes no binary frames")
                return []
            return [Update(self._in_binary, bytes(frame))]

        try:
            patch = json.loads(frame)
        except ValueError:
            patch = None
        if not isinstance(patch, dict):
            await self._refuse(None, "a text frame is a JSON object keyed by field name")
            return []

        updates = []
        fields = type(self.input).model_fields
        for key, raw in patch.items():
            try:
                if key in self._in_live:
                    if key == self._in_binary:
                        raise ValueError("send this field's items as binary frames")
                    updates.append(Update(key, self._adapter("in:" + key, self._in_live[key]).validate_python(raw)))
                elif key in fields:
                    # The model's own validation, so the field's constraints
                    # and validators hold mid-stream as they do in the body.
                    type(self.input).__pydantic_validator__.validate_assignment(self.input, key, raw)
                    updates.append(Update(key, getattr(self.input, key)))
                else:
                    raise ValueError("no such field")
            except (ValidationError, ValueError) as err:
                await self._refuse(key, _first_line(err))
        return updates

    async def _refuse(self, field: Optional[str], message: str) -> None:
        await self.socket.send({"error": {"field": field, "message": message}})

    async def send(self, **fields: Any) -> None:
        """Send items of live output fields, or new values of ordinary ones.

        ``await live.send(audio=pcm)`` is a binary frame;
        ``await live.send(transcript=Word(...))`` and
        ``await live.send(effect="echo")`` are JSON frames.
        """
        patch: Dict[str, Any] = {}
        for key, value in fields.items():
            if key not in self._out_fields:
                raise KeyError(f"the output model has no field {key!r}")
            if key == self._out_binary:
                # The kernel copies to bytes on the way out; pass views through.
                await self.socket.send(value if isinstance(value, (bytes, bytearray, memoryview)) else bytes(value))
                continue
            annotation = self._out_live.get(key, self._out_fields[key].annotation)
            patch[key] = self._adapter("out:" + key, annotation).dump_python(value, mode="json")
        if patch:
            await self.socket.send(patch)


def _first_line(err: Exception) -> str:
    if isinstance(err, ValidationError):
        first = err.errors()[0]
        return first.get("msg", str(err))
    return str(err)
