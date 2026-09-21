"""Live fields: schema shape, request-body validation, and the frame mapping."""

import asyncio
import json
from typing import List, Literal, Optional, Union

import pytest
from pydantic import BaseModel

from inferencesh import BaseAppInput, BaseAppOutput, Live, PCM16, Stream, media
from inferencesh.models.stream import binary_field, live_fields


class Interrupt(BaseModel):
    type: Literal["interrupt"] = "interrupt"


class UserText(BaseModel):
    type: Literal["text"] = "text"
    text: str


class TalkInput(BaseAppInput):
    voice: Literal["ara", "eve"] = "ara"
    gain: float = 1.0
    audio: Stream[PCM16(16000)]
    events: Stream[Union[Interrupt, UserText]]


class Word(BaseModel):
    text: str
    final: bool = False


class TalkOutput(BaseAppOutput):
    audio: Stream[PCM16(24000)]
    transcript: Stream[Word]
    voice: str = "ara"
    seconds: float = 0


class FakeSocket:
    def __init__(self, frames: List):
        self._frames = list(frames)
        self.sent: List = []

    def __aiter__(self):
        return self._iter()

    async def _iter(self):
        for f in self._frames:
            yield f

    async def send(self, data):
        self.sent.append(data)


def test_schema_marks_live_fields_like_file_fields():
    schema = TalkInput.model_json_schema()
    props = schema["properties"]

    assert props["audio"] == {
        "type": "array",
        "format": "stream",
        "items": {
            "type": "string",
            "format": "binary",
            "contentMediaType": "audio/pcm;format=s16le;rate=16000;channels=1",
        },
        "title": "Audio",
    }
    assert props["events"]["format"] == "stream"
    assert props["events"]["items"] == {"anyOf": [{"$ref": "#/$defs/Interrupt"}, {"$ref": "#/$defs/UserText"}]}
    assert set(schema["$defs"]) >= {"Interrupt", "UserText"}
    # The request body is the ordinary fields only.
    assert "audio" not in schema.get("required", []) and "events" not in schema.get("required", [])
    # Ordinary fields are untouched.
    assert props["voice"]["enum"] == ["ara", "eve"]


def test_media_helper_carries_any_content_type():
    class CamInput(BaseAppInput):
        frames: Stream[media("image/jpeg")]

    items = CamInput.model_json_schema()["properties"]["frames"]["items"]
    assert items["contentMediaType"] == "image/jpeg" and items["format"] == "binary"


def test_request_body_validates_without_live_fields_and_ignores_them_if_sent():
    assert TalkInput.model_validate({"voice": "eve"}).voice == "eve"
    got = TalkInput.model_validate({"voice": "eve", "audio": ["whatever"], "events": [{"type": "interrupt"}]})
    assert got.audio == Stream()


def test_final_output_serialises_live_fields_as_empty():
    dumped = TalkOutput(seconds=1.5).model_dump(mode="json")
    assert dumped["audio"] == [] and dumped["transcript"] == [] and dumped["seconds"] == 1.5


def test_live_fields_and_the_one_binary_field():
    assert set(live_fields(TalkInput)) == {"audio", "events"}
    assert binary_field(TalkInput) == "audio"

    class TwoBinaries(BaseAppInput):
        mic: Stream[PCM16()]
        cam: Stream[media("image/jpeg")]

    with pytest.raises(TypeError, match="one per direction"):
        binary_field(TwoBinaries)


def test_optional_live_field_is_found():
    class Opt(BaseAppInput):
        audio: Optional[Stream[PCM16()]] = None

    assert binary_field(Opt) == "audio"


def _run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


def test_live_maps_frames_to_fields():
    socket = FakeSocket([
        b"\x01\x02",
        json.dumps({"events": {"type": "text", "text": "hi"}}),
        json.dumps({"voice": "eve", "gain": "2.5"}),
        json.dumps({"events": {"type": "interrupt"}}),
    ])
    data = TalkInput()

    async def collect():
        return [u async for u in Live(socket, data, TalkOutput)]

    updates = _run(collect())
    assert updates[0] == ("audio", b"\x01\x02")
    assert updates[1].field == "events" and updates[1].value == UserText(text="hi")
    assert updates[2] == ("voice", "eve") and updates[3] == ("gain", 2.5)
    assert isinstance(updates[4].value, Interrupt)
    # Ordinary fields are applied to the input model, validated and coerced.
    assert data.voice == "eve" and data.gain == 2.5
    assert socket.sent == []


def test_live_answers_frames_that_do_not_fit_and_goes_on():
    socket = FakeSocket([
        json.dumps({"voice": "nobody"}),
        json.dumps({"nope": 1}),
        "not json",
        json.dumps({"audio": "base64?"}),
        json.dumps({"events": {"type": "text"}}),
        b"\x00",
    ])
    data = TalkInput()

    async def collect():
        return [u async for u in Live(socket, data, TalkOutput)]

    updates = _run(collect())
    assert updates == [("audio", b"\x00")], "the stream goes on after bad frames"
    assert data.voice == "ara", "a refused value is not applied"
    fields = [e["error"]["field"] for e in socket.sent]
    assert fields == ["voice", "nope", None, "audio", "events"]
    assert all(e["error"]["message"] for e in socket.sent)


def test_live_refuses_binary_when_the_input_has_no_binary_field():
    class TextOnly(BaseAppInput):
        events: Stream[UserText]

    socket = FakeSocket([b"\x00"])

    async def collect():
        return [u async for u in Live(socket, TextOnly(), TalkOutput)]

    assert _run(collect()) == []
    assert socket.sent[0]["error"]["message"] == "this function takes no binary frames"


def test_live_send():
    socket = FakeSocket([])
    live = Live(socket, TalkInput(), TalkOutput)

    async def go():
        await live.send(audio=b"\x09\x08")
        await live.send(transcript=Word(text="hello", final=True))
        await live.send(voice="eve", seconds=2)
        with pytest.raises(KeyError):
            await live.send(nonsense=1)

    _run(go())
    assert socket.sent == [
        b"\x09\x08",
        {"transcript": {"text": "hello", "final": True}},
        {"voice": "eve", "seconds": 2.0},
    ]
