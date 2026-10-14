"""Calling a vendor's HTTP API from an app.

The shared half of an API-wrapper app (``belt app init --template api`` and
``belt app init --openapi``): auth from the platform's injected secrets,
retries on 429 and 5xx, error mapping and request assembly from an operation
descriptor. The app's generated module describes each operation as an
:class:`Operation`; the app's hand-owned ``inference.py`` builds one
:class:`UpstreamClient` in ``setup`` and calls :meth:`UpstreamClient.call`.

The auth kinds mirror OpenAPI security schemes: ``api_key`` (a value in a
header, query parameter or cookie), ``http`` (``bearer`` or ``basic``) and
``oauth2`` with the ``client_credentials`` flow (a token fetched from the
token endpoint and cached until it expires). Other OAuth flows carry an
access token the platform injects, which is sent as a bearer token.

httpx is imported when the client is built, so importing this module costs
nothing in apps that do not use it.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import os
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, Mapping, Optional, Sequence, Tuple, Type, TypeVar, Union

from pydantic import BaseModel

if TYPE_CHECKING:  # pragma: no cover
    import httpx

M = TypeVar("M", bound=BaseModel)

RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})
DEFAULT_TIMEOUT = 60.0
DEFAULT_MAX_RETRIES = 3
# Bodies in error messages are cut here so a vendor's HTML error page does not
# become the task's error.
ERROR_BODY_LIMIT = 500


class UpstreamError(RuntimeError):
    """The vendor answered with an error, or could not be reached.

    ``status`` is the HTTP status (``None`` when the request never got a
    response), ``body`` the parsed JSON body when there was one, else the
    text, cut to :data:`ERROR_BODY_LIMIT`.
    """

    def __init__(self, message: str, *, status: Optional[int] = None, body: Any = None, method: str = "", path: str = ""):
        super().__init__(message)
        self.status = status
        self.body = body
        self.method = method
        self.path = path


class MissingSecret(UpstreamError):
    """A secret the auth needs is not in the environment: the app is not set up."""


@dataclass(frozen=True)
class Auth:
    """One way to authenticate, bound to the secrets that hold its values.

    ``kind`` is ``api_key``, ``http`` or ``oauth2``. Every secret is the name
    of an environment variable; values are read per request so a rotated
    secret takes effect without a restart.
    """

    kind: str
    # api_key and http bearer, and oauth2 flows other than client_credentials
    # (the platform injects the access token): the secret holding the value.
    secret: str = ""
    # api_key: where the value goes and under which name.
    location: str = "header"
    name: str = "Authorization"
    # api_key: text put before the value, e.g. "Bearer " or "Token ".
    prefix: str = ""
    # http: "bearer" or "basic".
    scheme: str = "bearer"
    # http basic: the secrets holding the two halves.
    username_secret: str = ""
    password_secret: str = ""
    # oauth2: the flow, and for client_credentials the token endpoint, the
    # secrets holding the client id and secret, and the scopes to ask for.
    flow: str = ""
    token_url: str = ""
    client_id_secret: str = ""
    client_secret_secret: str = ""
    scopes: Sequence[str] = ()

    @property
    def secrets(self) -> Tuple[str, ...]:
        """The secret names this auth reads, in a stable order."""
        names = [self.secret, self.username_secret, self.password_secret, self.client_id_secret, self.client_secret_secret]
        return tuple(n for n in names if n)


@dataclass(frozen=True)
class Operation:
    """One upstream operation: how an input model becomes a request.

    Parameter names are wire names (the input model's aliases, when it has
    them). Input fields not named as a path, query or header parameter form
    the body, unless ``body_field`` names a single field that is the whole
    body.
    """

    name: str
    method: str
    path: str
    path_params: Sequence[str] = ()
    query_params: Sequence[str] = ()
    header_params: Sequence[str] = ()
    # "json", "form" (application/x-www-form-urlencoded), "multipart" or
    # "none" (no body is sent, whatever is left over).
    body: str = "json"
    body_field: str = ""
    # The auth to use, by the name given to UpstreamClient; "" is the default.
    auth: str = ""
    # MCP tool hints and the credential declaration for @function.
    annotations: Mapping[str, Any] = field(default_factory=dict)
    credentials: Optional[Mapping[str, Any]] = None
    summary: str = ""

    def build(self, input: Union[BaseModel, Mapping[str, Any], None]) -> Dict[str, Any]:
        """The request as httpx keyword arguments: url, params, headers, json/data."""
        values: Dict[str, Any] = {}
        if isinstance(input, BaseModel):
            # Only what the caller set goes out: the vendor applies its own
            # defaults, and the model's defaults are the spec's description of
            # them, not a request to send them.
            values = input.model_dump(by_alias=True, exclude_unset=True, exclude_none=True, mode="json")
        elif input:
            values = {k: v for k, v in dict(input).items() if v is not None}
        # output_meta is the app's, never the vendor's.
        values.pop("output_meta", None)

        path = self.path
        for name in self.path_params:
            if name not in values:
                raise UpstreamError(f"{self.name}: path parameter {name!r} is required", method=self.method, path=self.path)
            path = path.replace("{" + name + "}", _path_segment(values.pop(name)))
        params = {name: _query_value(values.pop(name)) for name in self.query_params if name in values}
        headers = {name: str(values.pop(name)) for name in self.header_params if name in values}

        kwargs: Dict[str, Any] = {"url": path}
        if params:
            kwargs["params"] = params
        if headers:
            kwargs["headers"] = headers
        if self.body == "none":
            return kwargs
        if self.body_field and self.body_field not in values:
            return kwargs
        body: Any = values[self.body_field] if self.body_field else values
        if self.body == "json":
            # An empty object still goes: vendors reject a bodiless POST.
            kwargs["json"] = body
        elif self.body == "form":
            kwargs["data"] = body
        elif self.body == "multipart":
            files = {k: v for k, v in body.items() if _is_file_part(v)}
            data = {k: v for k, v in body.items() if k not in files}
            kwargs["data"] = data
            if files:
                kwargs["files"] = files
        else:
            raise ValueError(f"{self.name}: unknown body kind {self.body!r}")
        return kwargs


class UpstreamClient:
    """An httpx client for one vendor with auth, retries and error mapping.

    ``auth`` maps names to :class:`Auth`; ``default_auth`` names the one used
    by operations that do not name their own (the first one when omitted).
    """

    def __init__(
        self,
        base_url: str,
        *,
        auth: Union[Auth, Mapping[str, Auth], None] = None,
        default_auth: str = "",
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_statuses: Sequence[int] = tuple(RETRY_STATUSES),
        headers: Optional[Mapping[str, str]] = None,
        logger: Optional[logging.Logger] = None,
        transport: Any = None,
    ):
        import httpx

        if isinstance(auth, Auth):
            auth = {"default": auth}
        self.auth: Dict[str, Auth] = dict(auth or {})
        self.default_auth = default_auth or (next(iter(self.auth)) if self.auth else "")
        if self.default_auth and self.default_auth not in self.auth:
            raise ValueError(f"default_auth {self.default_auth!r} is not one of {sorted(self.auth)}")
        self.base_url = base_url
        self.max_retries = max_retries
        self.retry_statuses = frozenset(retry_statuses)
        self.logger = logger or logging.getLogger(__name__)
        self._tokens: Dict[str, Tuple[str, float]] = {}
        self._token_locks: Dict[str, asyncio.Lock] = {}
        self.http = httpx.AsyncClient(base_url=base_url, timeout=timeout, headers=dict(headers or {}), transport=transport)

    async def aclose(self) -> None:
        await self.http.aclose()

    async def __aenter__(self) -> "UpstreamClient":
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.aclose()

    # -- requests -------------------------------------------------------------

    async def call(self, op: Operation, input: Union[BaseModel, Mapping[str, Any], None] = None) -> Any:
        """Run ``op`` with ``input`` and return the decoded response body.

        JSON bodies decode to Python values; anything else is returned as
        text. Raises :class:`UpstreamError` on a non-2xx answer after retries.
        """
        kwargs = op.build(input)
        response = await self.request(op.method, kwargs.pop("url"), auth=op.auth, **kwargs)
        return decode(response)

    async def call_into(self, op: Operation, input: Any, model: Type[M]) -> M:
        """Like :meth:`call`, validated into ``model``."""
        return model.model_validate(await self.call(op, input))

    async def request(self, method: str, path: str, *, auth: str = "", **kwargs: Any) -> "httpx.Response":
        """One request with auth applied, retried on 429 and 5xx; raises on error."""
        import httpx

        await self._apply_auth(kwargs, auth or self.default_auth)
        method = method.upper()
        response: Optional[httpx.Response] = None
        for attempt in range(self.max_retries + 1):
            try:
                response = await self.http.request(method, path, **kwargs)
            except httpx.HTTPError as exc:
                if attempt == self.max_retries:
                    raise UpstreamError(f"{method} {path}: {exc}", method=method, path=path) from exc
                delay = float(2**attempt)
                self.logger.warning("%s %s: %s, retrying in %.0fs", method, path, exc, delay)
                await asyncio.sleep(delay)
                continue
            if response.status_code not in self.retry_statuses or attempt == self.max_retries:
                break
            delay = _retry_delay(response.headers.get("Retry-After"), attempt)
            self.logger.warning("%s %s: %s, retrying in %.0fs", method, path, response.status_code, delay)
            await asyncio.sleep(delay)
        assert response is not None
        if response.is_error:
            raise error_for(response, method, path)
        return response

    # -- auth -----------------------------------------------------------------

    async def _apply_auth(self, kwargs: Dict[str, Any], name: str) -> None:
        if not name:
            return
        auth = self.auth.get(name)
        if auth is None:
            raise ValueError(f"auth {name!r} is not one of {sorted(self.auth)}")
        headers = kwargs.setdefault("headers", {})
        if auth.kind == "api_key":
            value = auth.prefix + _secret(auth.secret)
            if auth.location == "header":
                headers[auth.name] = value
            elif auth.location == "query":
                kwargs.setdefault("params", {})[auth.name] = value
            elif auth.location == "cookie":
                kwargs.setdefault("cookies", {})[auth.name] = value
            else:
                raise ValueError(f"auth {name!r}: unknown api_key location {auth.location!r}")
        elif auth.kind == "http":
            if auth.scheme == "bearer":
                headers["Authorization"] = (auth.prefix or "Bearer ") + _secret(auth.secret)
            elif auth.scheme == "basic":
                pair = f"{_secret(auth.username_secret)}:{_secret(auth.password_secret)}"
                headers["Authorization"] = "Basic " + base64.b64encode(pair.encode()).decode()
            else:
                raise ValueError(f"auth {name!r}: unknown http scheme {auth.scheme!r}")
        elif auth.kind == "oauth2":
            if auth.flow == "client_credentials":
                headers["Authorization"] = "Bearer " + await self._client_credentials_token(name, auth)
            else:
                headers["Authorization"] = "Bearer " + _secret(auth.secret)
        else:
            raise ValueError(f"auth {name!r}: unknown kind {auth.kind!r}")

    async def _client_credentials_token(self, name: str, auth: Auth) -> str:
        lock = self._token_locks.setdefault(name, asyncio.Lock())
        async with lock:
            cached = self._tokens.get(name)
            if cached and cached[1] > time.monotonic():
                return cached[0]
            client_id = _secret(auth.client_id_secret)
            client_secret = _secret(auth.client_secret_secret)
            form = {"grant_type": "client_credentials"}
            if auth.scopes:
                form["scope"] = " ".join(auth.scopes)
            response = await self.http.post(auth.token_url, data=form, auth=(client_id, client_secret))
            if response.is_error:
                raise error_for(response, "POST", auth.token_url)
            token = response.json()
            access = token.get("access_token")
            if not access:
                raise UpstreamError(f"POST {auth.token_url}: no access_token in the token response", status=response.status_code, body=token, method="POST", path=auth.token_url)
            # Refresh a minute early; a token without expires_in lasts an hour here.
            ttl = float(token.get("expires_in") or 3600)
            self._tokens[name] = (access, time.monotonic() + max(ttl - 60, 1))
            return access


# -- helpers ------------------------------------------------------------------


def decode(response: "httpx.Response") -> Any:
    """A response body as JSON when it is JSON, else text; ``{}`` when empty."""
    if not response.content:
        return {}
    content_type = response.headers.get("content-type", "")
    if "json" in content_type:
        return response.json()
    try:
        return response.json()
    except ValueError:
        return response.text


def error_for(response: "httpx.Response", method: str, path: str) -> UpstreamError:
    """An :class:`UpstreamError` describing an error response."""
    body: Any = response.text[:ERROR_BODY_LIMIT]
    try:
        body = response.json()
    except ValueError:
        pass
    detail = body if isinstance(body, str) else response.text[:ERROR_BODY_LIMIT]
    return UpstreamError(f"{method} {path}: {response.status_code} {detail}".rstrip(), status=response.status_code, body=body, method=method, path=path)


def _secret(name: str) -> str:
    if not name:
        raise MissingSecret("auth needs a secret but none is named")
    value = os.environ.get(name)
    if not value:
        raise MissingSecret(f"{name} is not set: add it as a secret")
    return value


def _retry_delay(retry_after: Optional[str], attempt: int) -> float:
    if retry_after:
        try:
            return max(float(retry_after), 0.0)
        except ValueError:
            pass
    return float(2**attempt)


def _path_segment(value: Any) -> str:
    from urllib.parse import quote

    return quote(str(value), safe="")


def _query_value(value: Any) -> Any:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, tuple)):
        return [_query_value(v) for v in value]
    if isinstance(value, dict):
        import json

        return json.dumps(value)
    return value


def _is_file_part(value: Any) -> bool:
    return isinstance(value, (bytes, bytearray, tuple)) or hasattr(value, "read")


__all__ = ["Auth", "Operation", "UpstreamClient", "UpstreamError", "MissingSecret", "decode", "error_for", "RETRY_STATUSES"]
