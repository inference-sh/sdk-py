"""@function: per-function credentials and annotations (INF-1053)."""

import inspect
from typing import AsyncGenerator

import pytest
from pydantic import BaseModel

import inferencesh
from inferencesh import BaseApp, CredentialRequirement, Socket, ToolAnnotations, function


class In(BaseModel):
    text: str = ""


class Out(BaseModel):
    text: str = ""


def test_exported():
    for name in ("function", "ToolAnnotations", "CredentialRequirement"):
        assert name in inferencesh.__all__
        assert hasattr(inferencesh, name)


def test_stores_metadata_and_returns_same_function():
    async def create_event(self, input_data: In) -> Out:
        return Out()

    decorated = function(
        credentials=[{"key": "google.calendar.events"}],
        annotations={"readOnlyHint": False, "destructiveHint": False},
    )(create_event)

    assert decorated is create_event
    assert create_event.__inferencesh_function__ == {
        "credentials": [{"key": "google.calendar.events"}],
        "annotations": {"readOnlyHint": False, "destructiveHint": False},
    }


def test_only_declared_parts_are_stored():
    @function(annotations={"readOnlyHint": True})
    async def a(self, input_data: In) -> Out: ...

    @function(credentials=[{"provider": "acme", "secrets": ["ACME_KEY"]}])
    async def b(self, input_data: In) -> Out: ...

    @function()
    async def c(self, input_data: In) -> Out: ...

    assert a.__inferencesh_function__ == {"annotations": {"readOnlyHint": True}}
    assert b.__inferencesh_function__ == {"credentials": [{"provider": "acme", "secrets": ["ACME_KEY"]}]}
    assert c.__inferencesh_function__ == {}


def test_none_hints_are_dropped():
    @function(annotations={"title": "List", "readOnlyHint": True, "destructiveHint": None})
    async def a(self, input_data: In) -> Out: ...

    assert a.__inferencesh_function__ == {"annotations": {"title": "List", "readOnlyHint": True}}

    @function(annotations={"readOnlyHint": None})
    async def b(self, input_data: In) -> Out: ...

    assert b.__inferencesh_function__ == {}


def test_declaration_is_copied():
    creds = [{"key": "google.calendar", "scopes": ["calendar"]}]
    ann = {"readOnlyHint": True}

    @function(credentials=creds, annotations=ann)
    async def a(self, input_data: In) -> Out: ...

    creds[0]["key"] = "changed"
    creds[0]["scopes"].append("x")
    ann["readOnlyHint"] = False
    assert a.__inferencesh_function__ == {
        "credentials": [{"key": "google.calendar", "scopes": ["calendar"]}],
        "annotations": {"readOnlyHint": True},
    }


def test_typed_declarations_accepted():
    cred: CredentialRequirement = {"key": "google.calendar.events", "optional": True}
    ann: ToolAnnotations = {"title": "Create event", "openWorldHint": True}

    @function(credentials=[cred], annotations=ann)
    async def a(self, input_data: In) -> Out: ...

    assert a.__inferencesh_function__["credentials"] == [cred]


def test_provider_only_credential_without_key_is_valid():
    @function(credentials=[{"provider": "acme", "secrets": ["ACME_API_KEY"]}])
    async def a(self, input_data: In) -> Out: ...

    assert a.__inferencesh_function__ == {
        "credentials": [{"provider": "acme", "secrets": ["ACME_API_KEY"]}],
    }


def test_decorator_rejects_non_callable_target():
    with pytest.raises(TypeError, match="decorates a method"):
        function()(object())


@pytest.mark.parametrize(
    "kwargs, exc, match",
    [
        ({"credentials": {"key": "google.calendar"}}, TypeError, "list of dicts"),
        ({"credentials": "google.calendar"}, TypeError, "list of dicts"),
        ({"credentials": []}, ValueError, "empty list"),
        ({"credentials": ["google.calendar"]}, TypeError, r"credentials\[0\]: expected a dict"),
        ({"credentials": [{"key": "a", "scope": ["x"]}]}, ValueError, r"unknown keys \['scope'\]"),
        ({"credentials": [{"description": "no key"}]}, ValueError, "set 'key'"),
        ({"credentials": [{"key": 1}]}, TypeError, "key: expected a string"),
        ({"credentials": [{"key": "a", "optional": "yes"}]}, TypeError, "optional: expected a bool"),
        ({"credentials": [{"provider": "acme", "secrets": "KEY"}]}, TypeError, "secrets: expected a list"),
        ({"annotations": [("readOnlyHint", True)]}, TypeError, "expected a dict"),
        ({"annotations": {"readonlyHint": True}}, ValueError, r"unknown keys \['readonlyHint'\]"),
        ({"annotations": {"readOnlyHint": "true"}}, TypeError, "readOnlyHint: expected a bool"),
        ({"annotations": {"title": 3}}, TypeError, "title: expected a string"),
    ],
)
def test_bad_declarations_fail_at_decoration(kwargs, exc, match):
    with pytest.raises(exc, match=match):
        function(**kwargs)


def test_bare_decorator_is_an_error():
    with pytest.raises(TypeError):

        @function  # type: ignore[arg-type]
        async def a(self, input_data: In) -> Out: ...


class App(BaseApp):
    @function(credentials=[{"key": "google.calendar.events"}], annotations={"readOnlyHint": True})
    async def listen(self, input_data: In, socket: Socket) -> Out:
        """Stream function."""
        return Out()

    @function(annotations={"readOnlyHint": True})
    async def words(self, input_data: In) -> AsyncGenerator[Out, None]:
        """Generator function."""
        yield Out()


def test_signature_doc_and_kind_markers_unchanged():
    assert inspect.iscoroutinefunction(App.listen)
    assert list(inspect.signature(App.listen).parameters) == ["self", "input_data", "socket"]
    assert App.listen.__doc__ == "Stream function."
    assert inspect.isasyncgenfunction(App.words)
    assert App.listen.__inferencesh_function__["credentials"] == [{"key": "google.calendar.events"}]
    assert App().words.__inferencesh_function__ == {"annotations": {"readOnlyHint": True}}
