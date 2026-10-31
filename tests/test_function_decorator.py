"""@function: per-function credentials and annotations (INF-1053)."""

import inspect
from typing import AsyncGenerator

import pytest
from pydantic import BaseModel

import inferencesh
from inferencesh import BaseApp, CredentialRequirement, Socket, ToolAnnotations, function
from inferencesh.decorators import normalize_credentials


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
        "credentials": [{"slug": "google", "capabilities": ["google.calendar.events"]}],
        "annotations": {"readOnlyHint": False, "destructiveHint": False},
    }


def test_only_declared_parts_are_stored():
    @function(annotations={"readOnlyHint": True})
    async def a(self, input_data: In) -> Out: ...  # type: ignore[empty-body]

    @function(credentials=[{"provider": "acme", "secrets": ["ACME_KEY"]}])
    async def b(self, input_data: In) -> Out: ...  # type: ignore[empty-body]

    @function()
    async def c(self, input_data: In) -> Out: ...  # type: ignore[empty-body]

    assert a.__inferencesh_function__ == {"annotations": {"readOnlyHint": True}}
    assert b.__inferencesh_function__ == {"credentials": [{"slug": "acme", "secrets": ["ACME_KEY"]}]}
    assert c.__inferencesh_function__ == {}


def test_none_hints_are_dropped():
    @function(annotations={"title": "List", "readOnlyHint": True, "destructiveHint": None})
    async def a(self, input_data: In) -> Out: ...  # type: ignore[empty-body]

    assert a.__inferencesh_function__ == {"annotations": {"title": "List", "readOnlyHint": True}}

    @function(annotations={"readOnlyHint": None})
    async def b(self, input_data: In) -> Out: ...  # type: ignore[empty-body]

    assert b.__inferencesh_function__ == {}


def test_declaration_is_copied():
    creds = [{"key": "google.calendar", "scopes": ["calendar"]}]
    ann = {"readOnlyHint": True}

    @function(credentials=creds, annotations=ann)
    async def a(self, input_data: In) -> Out: ...  # type: ignore[empty-body]

    creds[0]["key"] = "changed"
    creds[0]["scopes"].append("x")
    ann["readOnlyHint"] = False
    assert a.__inferencesh_function__ == {
        "credentials": [{"slug": "google", "capabilities": ["google.calendar"], "scopes": ["calendar"]}],
        "annotations": {"readOnlyHint": True},
    }


def test_typed_declarations_accepted():
    cred: CredentialRequirement = {"key": "google.calendar.events", "optional": True}
    ann: ToolAnnotations = {"title": "Create event", "openWorldHint": True}

    @function(credentials=[cred], annotations=ann)
    async def a(self, input_data: In) -> Out: ...  # type: ignore[empty-body]

    assert a.__inferencesh_function__["credentials"] == [
        {"slug": "google", "capabilities": ["google.calendar.events"], "optional": True}
    ]


@pytest.mark.parametrize(
    "credentials, want",
    [
        # keyed by slug, like inf.yml
        ({"slack": {"capabilities": ["slack.channels.write"]}}, [{"slug": "slack", "capabilities": ["slack.channels.write"]}]),
        ({"huggingface": {}}, [{"slug": "huggingface"}]),
        ({"huggingface": None}, [{"slug": "huggingface"}]),
        # a list of entries
        ([{"slug": "aikido-mcp", "scopes": ["issues:read"], "optional": False}],
         [{"slug": "aikido-mcp", "optional": False, "scopes": ["issues:read"]}]),
        # bare slugs; a dotted one is a capability
        (["aikido-mcp", "slack.channels.read"],
         [{"slug": "aikido-mcp"}, {"slug": "slack", "capabilities": ["slack.channels.read"]}]),
        # the company block and an inline auth scheme pass through, in canonical order
        ([{"slug": "aikido-mcp", "provider": {"website": "aikido.dev", "slug": "aikido", "name": "Aikido"},
           "auth": {"kind": "oauth2", "flow": "authorization_code", "token_endpoint": "https://a/t", "authorization_endpoint": "https://a/a"}}],
         [{"slug": "aikido-mcp", "provider": {"slug": "aikido", "name": "Aikido", "website": "aikido.dev"},
           "auth": {"kind": "oauth2", "flow": "authorization_code", "token_endpoint": "https://a/t", "authorization_endpoint": "https://a/a"}}]),
        # legacy spellings fold into the new keys
        ([{"key": "slack.channels.write"}], [{"slug": "slack", "capabilities": ["slack.channels.write"]}]),
        ([{"key": "github"}], [{"slug": "github"}]),
        ([{"provider": "acme", "name": "Acme CRM", "website": "acme.com", "secrets": ["ACME_KEY"], "description": "crm"}],
         [{"slug": "acme", "description": "crm", "secrets": ["ACME_KEY"], "provider": {"name": "Acme CRM", "website": "acme.com"}}]),
        ([{"slug": "google", "key": "google.calendar.events", "capabilities": ["google.calendar"]}],
         [{"slug": "google", "capabilities": ["google.calendar", "google.calendar.events"]}]),
    ],
)
def test_every_form_normalises_to_the_schema_shape(credentials, want):
    assert normalize_credentials(credentials) == want
    for entry in normalize_credentials(credentials):
        keys = list(entry)
        order = ["slug", "capabilities", "description", "optional", "secrets", "scopes", "provider", "auth"]
        assert keys == [k for k in order if k in keys]


def test_decorator_rejects_non_callable_target():
    with pytest.raises(TypeError, match="decorates a method"):
        function()(object())


@pytest.mark.parametrize(
    "kwargs, exc, match",
    [
        ({"credentials": {"key": "google.calendar"}}, TypeError, r"credentials\['key'\]: expected a dict"),
        ({"credentials": "google.calendar"}, TypeError, "dict keyed by slug or a list"),
        ({"credentials": []}, ValueError, "empty list"),
        ({"credentials": {}}, ValueError, "empty"),
        ({"credentials": [1]}, TypeError, r"credentials\[0\]: expected a dict or a slug"),
        ({"credentials": [{"slug": "a", "scope": ["x"]}]}, ValueError, r"unknown keys \['scope'\]"),
        ({"credentials": [{"description": "no slug"}]}, ValueError, "set 'slug'"),
        ({"credentials": [{"key": 1}]}, TypeError, "key: expected a string"),
        ({"credentials": [{"slug": "a", "optional": "yes"}]}, TypeError, "optional: expected a bool"),
        ({"credentials": [{"slug": "acme", "secrets": "KEY"}]}, TypeError, "secrets: expected a list"),
        ({"credentials": [{"slug": "acme", "capabilities": ["nodot"]}]}, ValueError, "not <slug>.<name>"),
        ({"credentials": [{"slug": "a", "provider": "b"}]}, ValueError, "disagree"),
        ({"credentials": {"a": {"slug": "b"}}}, ValueError, "keyed as 'a'"),
        ({"credentials": [{"slug": "a", "provider": {"logo": "x"}}]}, ValueError, r"unknown keys \['logo'\]"),
        ({"credentials": [{"slug": "a", "provider": {"name": 1}}]}, TypeError, "provider.name: expected a string"),
        ({"credentials": [{"slug": "a", "auth": "oauth2"}]}, TypeError, "auth: expected a dict"),
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
        async def a(self, input_data: In) -> Out: ...  # type: ignore[empty-body]


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
    assert App.listen.__inferencesh_function__["credentials"] == [{"slug": "google", "capabilities": ["google.calendar.events"]}]
    assert App().words.__inferencesh_function__ == {"annotations": {"readOnlyHint": True}}
