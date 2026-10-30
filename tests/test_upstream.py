"""inferencesh.upstream: the shared client of API-wrapper apps."""

import json
from typing import TYPE_CHECKING

import pytest
if TYPE_CHECKING:
    import httpx
httpx = pytest.importorskip("httpx")
from pydantic import BaseModel, Field

from inferencesh.upstream import Auth, MissingSecret, Operation, UpstreamClient, UpstreamError


class SearchIn(BaseModel):
    query: str
    max_results: int = Field(default=5, alias="maxResults")
    request_id: str = ""
    tag: str | None = None
    verbose: bool | None = None
    nothing: str | None = None

    model_config = {"populate_by_name": True}


SEARCH = Operation(
    name="search",
    method="POST",
    path="/v1/search/{request_id}",
    path_params=("request_id",),
    query_params=("verbose",),
    header_params=("tag",),
)


def test_build_places_each_field_by_the_operation():
    kwargs = SEARCH.build(SearchIn(query="ai", request_id="a/b", tag="t1", verbose=True, max_results=7))
    assert kwargs == {
        "url": "/v1/search/a%2Fb",
        "params": {"verbose": "true"},
        "headers": {"tag": "t1"},
        "json": {"query": "ai", "maxResults": 7},
    }


def test_build_sends_only_what_was_set_by_alias():
    kwargs = SEARCH.build(SearchIn(query="ai", request_id="1", nothing=None))
    assert kwargs["json"] == {"query": "ai"}, "defaults and None stay home"
    assert "params" not in kwargs and "headers" not in kwargs
    assert SEARCH.build(SearchIn.model_validate({"query": "x", "request_id": "1", "maxResults": 5}))["json"] == {"query": "x", "maxResults": 5}


def test_build_requires_path_params():
    with pytest.raises(UpstreamError, match="request_id"):
        SEARCH.build({"query": "ai"})


def test_build_get_without_body():
    op = Operation(name="get", method="GET", path="/items", query_params=("q", "limit"), body="none")
    assert op.build({"q": "x", "limit": 3, "extra": "ignored"}) == {"url": "/items", "params": {"q": "x", "limit": 3}}


def test_build_body_field_and_form():
    op = Operation(name="put", method="PUT", path="/items", body_field="body")
    assert op.build({"body": ["a", "b"]})["json"] == ["a", "b"]
    assert "json" not in op.build({})
    form = Operation(name="f", method="POST", path="/t", body="form")
    assert form.build({"a": 1})["data"] == {"a": 1}


def test_build_sends_an_empty_object_when_nothing_is_set():
    op = Operation(name="logs", method="POST", path="/logs")
    assert op.build({})["json"] == {}, "a bodiless POST is a 422 at vendors that validate the body"
    assert op.build(None)["json"] == {}


class LogsIn(BaseModel):
    model_config = {"extra": "forbid"}


def test_build_sends_empty_json_for_unset_pydantic_input():
    op = Operation(name="logs", method="POST", path="/logs")
    assert op.build(LogsIn())["json"] == {}


async def test_call_sends_json_empty_object_on_post_with_no_input():
    seen = {}

    def handler(request: httpx.Request):
        seen["method"] = request.method
        seen["content"] = request.content
        seen["content_type"] = request.headers.get("content-type")
        return httpx.Response(200, json={"ok": True})

    op = Operation(name="logs", method="POST", path="/logs")
    async with client(handler) as c:
        assert await c.call(op) == {"ok": True}
        assert await c.call(op, {}) == {"ok": True}
        assert await c.call(op, None) == {"ok": True}
    assert seen["method"] == "POST"
    assert seen["content"] == b"{}"
    assert seen["content_type"] == "application/json"


def test_build_strips_output_meta():
    op = Operation(name="post", method="POST", path="/t")
    assert op.build({"a": 1, "output_meta": {"x": 1}})["json"] == {"a": 1}


def client(handler, **kw):
    return UpstreamClient("https://api.example.com", transport=httpx.MockTransport(handler), **kw)


async def test_call_decodes_json_and_applies_bearer(monkeypatch):
    monkeypatch.setenv("EX_API_KEY", "k-1")
    seen = {}

    def handler(request: httpx.Request):
        seen["auth"] = request.headers["authorization"]
        seen["body"] = json.loads(request.content)
        seen["url"] = str(request.url)
        return httpx.Response(200, json={"ok": True})

    async with client(handler, auth=Auth(kind="http", scheme="bearer", secret="EX_API_KEY")) as c:
        out = await c.call(SEARCH, SearchIn(query="ai", request_id="7", verbose=True))
    assert out == {"ok": True}
    assert seen["auth"] == "Bearer k-1"
    assert seen["body"] == {"query": "ai"}
    assert seen["url"] == "https://api.example.com/v1/search/7?verbose=true"


async def test_api_key_in_query_and_header(monkeypatch):
    monkeypatch.setenv("EX_KEY", "q-1")
    seen = {}

    def handler(request: httpx.Request):
        seen["url"] = str(request.url)
        seen["hdr"] = request.headers.get("x-api-key")
        return httpx.Response(200, text="plain")

    auth = {
        "q": Auth(kind="api_key", location="query", name="api_key", secret="EX_KEY"),
        "h": Auth(kind="api_key", location="header", name="X-Api-Key", prefix="Token ", secret="EX_KEY"),
    }
    op_q = Operation(name="g", method="GET", path="/a", body="none", auth="q")
    op_h = Operation(name="g", method="GET", path="/a", body="none", auth="h")
    async with client(handler, auth=auth) as c:
        assert await c.call(op_q) == "plain"
        assert seen["url"] == "https://api.example.com/a?api_key=q-1"
        await c.call(op_h)
        assert seen["hdr"] == "Token q-1"


async def test_basic_auth(monkeypatch):
    monkeypatch.setenv("U", "me")
    monkeypatch.setenv("P", "pw")
    seen = {}

    def handler(request):
        seen["auth"] = request.headers["authorization"]
        return httpx.Response(204)

    async with client(handler, auth=Auth(kind="http", scheme="basic", username_secret="U", password_secret="P")) as c:
        assert await c.call(Operation(name="d", method="DELETE", path="/x", body="none")) == {}
    assert seen["auth"] == "Basic bWU6cHc="


async def test_missing_secret_is_a_setup_error(monkeypatch):
    monkeypatch.delenv("EX_API_KEY", raising=False)
    async with client(lambda r: httpx.Response(200), auth=Auth(kind="api_key", secret="EX_API_KEY")) as c:
        with pytest.raises(MissingSecret, match="EX_API_KEY is not set"):
            await c.call(Operation(name="g", method="GET", path="/a", body="none"))


async def test_retries_then_raises_with_body(monkeypatch):
    calls = []

    def handler(request):
        calls.append(1)
        if len(calls) < 3:
            return httpx.Response(503, headers={"Retry-After": "0"})
        return httpx.Response(400, json={"detail": {"error": "bad query"}})

    async with client(handler, max_retries=3) as c:
        with pytest.raises(UpstreamError) as exc:
            await c.call(Operation(name="p", method="POST", path="/s"), {"q": 1})
    assert len(calls) == 3
    assert exc.value.status == 400
    assert exc.value.body == {"detail": {"error": "bad query"}}
    assert "POST /s: 400" in str(exc.value)


async def test_retry_budget_is_exhausted():
    calls = []

    def handler(request):
        calls.append(1)
        return httpx.Response(429, headers={"Retry-After": "0"}, text="slow down")

    async with client(handler, max_retries=2) as c:
        with pytest.raises(UpstreamError, match="429 slow down") as exc:
            await c.request("GET", "/x")
    assert len(calls) == 3
    assert exc.value.body == "slow down"


async def test_client_credentials_token_is_fetched_once(monkeypatch):
    monkeypatch.setenv("CID", "id")
    monkeypatch.setenv("CSEC", "sec")
    token_calls = []

    def handler(request: httpx.Request):
        if request.url.path == "/oauth/token":
            token_calls.append(dict(httpx.QueryParams(request.content.decode())))
            assert request.headers["authorization"].startswith("Basic ")
            return httpx.Response(200, json={"access_token": "tok", "expires_in": 3600})
        assert request.headers["authorization"] == "Bearer tok"
        return httpx.Response(200, json={"n": len(token_calls)})

    auth = Auth(kind="oauth2", flow="client_credentials", token_url="https://api.example.com/oauth/token", client_id_secret="CID", client_secret_secret="CSEC", scopes=("read", "write"))
    op = Operation(name="g", method="GET", path="/a", body="none")
    async with client(handler, auth=auth) as c:
        await c.call(op)
        await c.call(op)
    assert token_calls == [{"grant_type": "client_credentials", "scope": "read write"}]


async def test_call_into_validates():
    class Out(BaseModel):
        ok: bool

    async with client(lambda r: httpx.Response(200, json={"ok": True, "extra": 1})) as c:
        out = await c.call_into(Operation(name="g", method="GET", path="/a", body="none"), None, Out)
    assert out == Out(ok=True)


def test_auth_secrets_lists_what_it_reads():
    assert Auth(kind="http", scheme="basic", username_secret="U", password_secret="P").secrets == ("U", "P")
    assert Auth(kind="api_key", secret="K").secrets == ("K",)


def test_unknown_default_auth_is_refused():
    with pytest.raises(ValueError, match="default_auth"):
        UpstreamClient("https://x", auth={"a": Auth(kind="api_key", secret="K")}, default_auth="b")


def test_build_multipart_splits_files_and_fields():
    op = Operation(name="upload", method="POST", path="/upload", body="multipart")

    class FileLike:
        def read(self):
            return b"bin"

    thumb = FileLike()
    kwargs = op.build({"name": "doc", "file": b"raw", "thumb": thumb, "note": "text"})
    assert kwargs["data"] == {"name": "doc", "note": "text"}
    assert kwargs["files"] == {"file": b"raw", "thumb": thumb}


def test_build_query_serializes_bools_lists_and_dicts():
    op = Operation(name="list", method="GET", path="/items", query_params=("on", "ids", "filter"), body="none")
    kwargs = op.build({"on": False, "ids": [1, 2], "filter": {"a": 1}})
    assert kwargs["params"] == {"on": "false", "ids": [1, 2], "filter": '{"a": 1}'}


def test_build_unknown_body_kind():
    op = Operation(name="x", method="POST", path="/t", body="xml")
    with pytest.raises(ValueError, match="unknown body kind"):
        op.build({"a": 1})


@pytest.mark.filterwarnings("error::DeprecationWarning")
async def test_api_key_in_cookie(monkeypatch):
    monkeypatch.setenv("CK", "v")
    seen = {}

    def handler(request: httpx.Request):
        seen["cookie"] = request.headers.get("cookie")
        return httpx.Response(200, json={})

    auth = Auth(kind="api_key", location="cookie", name="session", secret="CK")
    async with client(handler, auth=auth) as c:
        await c.call(Operation(name="g", method="GET", path="/a", body="none"))
    assert seen["cookie"] == "session=v"


@pytest.mark.filterwarnings("error::DeprecationWarning")
async def test_api_key_cookie_keeps_caller_cookie_header(monkeypatch):
    monkeypatch.setenv("CK", "v")
    seen = {}

    def handler(request: httpx.Request):
        seen["cookie"] = request.headers.get("cookie")
        return httpx.Response(200, json={})

    auth = Auth(kind="api_key", location="cookie", name="session", secret="CK")
    async with client(handler, auth=auth) as c:
        await c.request("GET", "/a", headers={"cookie": "theme=dark"})
    assert seen["cookie"] == "theme=dark; session=v"


@pytest.mark.filterwarnings("error::DeprecationWarning")
async def test_api_key_cookie_keeps_cookies_the_upstream_set(monkeypatch):
    monkeypatch.setenv("CK", "v")
    seen = []

    def handler(request: httpx.Request):
        seen.append(request.headers.get("cookie"))
        return httpx.Response(200, json={}, headers={"set-cookie": "sid=abc; Path=/"})

    auth = Auth(kind="api_key", location="cookie", name="session", secret="CK")
    async with client(handler, auth=auth) as c:
        await c.request("GET", "/a")
        await c.request("GET", "/b")
    assert seen == ["session=v", "sid=abc; session=v"]


@pytest.mark.filterwarnings("error::DeprecationWarning")
async def test_api_key_cookie_keeps_client_default_cookie_header(monkeypatch):
    monkeypatch.setenv("CK", "v")
    seen = {}

    def handler(request: httpx.Request):
        seen["cookie"] = request.headers.get("cookie")
        return httpx.Response(200, json={})

    auth = Auth(kind="api_key", location="cookie", name="session", secret="CK")
    async with client(handler, auth=auth, headers={"Cookie": "theme=dark"}) as c:
        await c.request("GET", "/a")
    assert seen["cookie"] == "theme=dark; session=v"


@pytest.mark.filterwarnings("error::DeprecationWarning")
async def test_api_key_cookie_with_header_tuples_and_name_clash(monkeypatch):
    monkeypatch.setenv("CK", "v")
    seen = {}

    def handler(request: httpx.Request):
        seen["cookie"] = request.headers.get("cookie")
        seen["x"] = request.headers.get("x-trace")
        return httpx.Response(200, json={})

    auth = Auth(kind="api_key", location="cookie", name="session", secret="CK")
    async with client(handler, auth=auth) as c:
        await c.request("GET", "/a", headers=[("X-Trace", "1"), ("Cookie", "session=stale; theme=dark")])
    assert seen == {"cookie": "theme=dark; session=v", "x": "1"}


@pytest.mark.filterwarnings("error::DeprecationWarning")
async def test_api_key_cookie_applies_prefix(monkeypatch):
    monkeypatch.setenv("CK", "v")
    seen = {}

    def handler(request: httpx.Request):
        seen["cookie"] = request.headers.get("cookie")
        return httpx.Response(200, json={})

    auth = Auth(kind="api_key", location="cookie", name="session", prefix="sess_", secret="CK")
    async with client(handler, auth=auth) as c:
        await c.request("GET", "/a")
    assert seen["cookie"] == "session=sess_v"


@pytest.mark.filterwarnings("error::DeprecationWarning")
async def test_api_key_cookie_build_request_omits_cookies_kwarg(monkeypatch):
    """Cookie auth must not use httpx's per-request cookies= (jar is merged in send)."""
    monkeypatch.setenv("CK", "v")
    captured = {}

    def handler(request: httpx.Request):
        return httpx.Response(200, json={})

    auth = Auth(kind="api_key", location="cookie", name="session", secret="CK")
    async with client(handler, auth=auth) as c:
        real_build = c.http.build_request

        def spy(method, url, **kwargs):
            captured.update(kwargs)
            return real_build(method, url, **kwargs)

        monkeypatch.setattr(c.http, "build_request", spy)
        await c.request("GET", "/a")
    assert "cookies" not in captured


async def test_oauth2_injected_access_token(monkeypatch):
    monkeypatch.setenv("ACCESS", "inj")
    seen = {}

    def handler(request: httpx.Request):
        seen["auth"] = request.headers["authorization"]
        return httpx.Response(200, json={})

    auth = Auth(kind="oauth2", flow="authorization_code", secret="ACCESS")
    async with client(handler, auth=auth) as c:
        await c.call(Operation(name="g", method="GET", path="/a", body="none"))
    assert seen["auth"] == "Bearer inj"


async def test_retries_on_transport_errors():
    calls = []

    def handler(request: httpx.Request):
        calls.append(1)
        if len(calls) < 2:
            raise httpx.ConnectError("connection reset", request=request)
        return httpx.Response(200, json={"recovered": True})

    async with client(handler, max_retries=2) as c:
        out = await c.request("GET", "/x")
    assert out.json() == {"recovered": True}
    assert len(calls) == 2


async def test_invalid_retry_after_falls_back_to_exponential_backoff():
    calls = []

    def handler(request: httpx.Request):
        calls.append(1)
        if len(calls) == 1:
            return httpx.Response(503, headers={"Retry-After": "soon"})
        return httpx.Response(200, text="ok")

    async with client(handler, max_retries=1) as c:
        response = await c.request("GET", "/x")
    assert response.text == "ok"
    assert len(calls) == 2


async def test_unknown_auth_name_is_refused():
    async with client(lambda r: httpx.Response(200)) as c:
        with pytest.raises(ValueError, match="auth 'nope'"):
            await c.request("GET", "/x", auth="nope")


async def test_unknown_api_key_location_is_refused(monkeypatch):
    monkeypatch.setenv("K", "v")
    bad = Auth(kind="api_key", location="body", secret="K")
    async with client(lambda r: httpx.Response(200), auth=bad) as c:
        with pytest.raises(ValueError, match="unknown api_key location"):
            await c.request("GET", "/x")


async def test_unknown_http_scheme_is_refused(monkeypatch):
    monkeypatch.setenv("K", "v")
    bad = Auth(kind="http", scheme="digest", secret="K")
    async with client(lambda r: httpx.Response(200), auth=bad) as c:
        with pytest.raises(ValueError, match="unknown http scheme"):
            await c.request("GET", "/x")


async def test_unknown_auth_kind_is_refused(monkeypatch):
    monkeypatch.setenv("K", "v")
    bad = Auth(kind="mutual_tls", secret="K")
    async with client(lambda r: httpx.Response(200), auth=bad) as c:
        with pytest.raises(ValueError, match="unknown kind"):
            await c.request("GET", "/x")


async def test_client_credentials_token_endpoint_error(monkeypatch):
    monkeypatch.setenv("CID", "id")
    monkeypatch.setenv("CSEC", "sec")

    def handler(request: httpx.Request):
        if request.url.path == "/oauth/token":
            return httpx.Response(401, json={"error": "invalid_client"})
        return httpx.Response(200)

    auth = Auth(
        kind="oauth2",
        flow="client_credentials",
        token_url="https://api.example.com/oauth/token",
        client_id_secret="CID",
        client_secret_secret="CSEC",
    )
    async with client(handler, auth=auth) as c:
        with pytest.raises(UpstreamError) as exc:
            await c.call(Operation(name="g", method="GET", path="/a", body="none"))
    assert exc.value.status == 401
    assert exc.value.body == {"error": "invalid_client"}


async def test_client_credentials_missing_access_token(monkeypatch):
    monkeypatch.setenv("CID", "id")
    monkeypatch.setenv("CSEC", "sec")

    def handler(request: httpx.Request):
        return httpx.Response(200, json={"token_type": "bearer"})

    auth = Auth(
        kind="oauth2",
        flow="client_credentials",
        token_url="https://api.example.com/oauth/token",
        client_id_secret="CID",
        client_secret_secret="CSEC",
    )
    async with client(handler, auth=auth) as c:
        with pytest.raises(UpstreamError, match="no access_token"):
            await c.call(Operation(name="g", method="GET", path="/a", body="none"))


async def test_missing_secret_when_name_is_empty():
    async with client(lambda r: httpx.Response(200), auth=Auth(kind="api_key", secret="")) as c:
        with pytest.raises(MissingSecret, match="none is named"):
            await c.request("GET", "/x")


async def test_transport_errors_exhaust_retry_budget():
    def handler(request: httpx.Request):
        raise httpx.ConnectError("down", request=request)

    async with client(handler, max_retries=1) as c:
        with pytest.raises(UpstreamError, match="down"):
            await c.request("GET", "/x")
