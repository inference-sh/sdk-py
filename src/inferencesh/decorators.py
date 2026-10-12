"""Per-function metadata for app functions.

``@function`` declares what one app function needs and how it behaves:

    from inferencesh import BaseApp, function

    class App(BaseApp):
        @function(
            credentials={"google": {"capabilities": ["google.calendar.events"]}},
            annotations={"readOnlyHint": False, "destructiveHint": False},
        )
        async def create_event(self, input_data: CreateEventInput) -> CreateEventOutput: ...

The engine's function discovery reads the metadata at deploy time and writes it
to the function's entry in ``functions_schema.json``.

- ``credentials``: the credentials this function needs at run time, keyed by
  credential slug the way ``inf.yml`` ``credentials:`` is. Each must be covered
  by the app-wide list there. A function without ``credentials`` gets the whole
  app-wide list. Accepted forms:

  - a dict keyed by slug: ``{"slack": {"capabilities": ["slack.channels.write"]}}``
  - a list of entries: ``[{"slug": "slack", "capabilities": [...]}]``
  - a list of bare slugs: ``["aikido-mcp"]``; a dotted string is a capability
    (``"slack.channels.write"`` → slug ``slack``)
  - the older entry keys ``provider`` (a string), ``key`` (a capability),
    ``name`` and ``website``, which are read into ``slug``, ``capabilities``
    and ``provider`` (the company block)

- ``annotations``: MCP tool hints (``title``, ``readOnlyHint``,
  ``destructiveHint``, ``idempotentHint``, ``openWorldHint``).

The decorator returns the function itself; it only sets
``__inferencesh_function__`` on it, with the credentials in their normalised
form.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, TypeVar, Union

from .types import CredentialRequirement, ToolAnnotations

F = TypeVar("F", bound=Callable[..., Any])

FUNCTION_META_ATTR = "__inferencesh_function__"

# The entry as written to functions_schema.json, in this key order.
CREDENTIAL_KEYS = ("slug", "capabilities", "description", "optional", "secrets", "scopes", "provider", "auth")
PROVIDER_SEED_KEYS = ("slug", "name", "description", "website", "logo_uri", "docs_uri", "tos_uri", "policy_uri")
# Older spellings, read and folded into the keys above.
_LEGACY_CREDENTIAL_KEYS = ("key", "name", "website")
_CREDENTIAL_STR_KEYS = ("slug", "description")
_CREDENTIAL_LIST_KEYS = ("capabilities", "secrets", "scopes")
_ANNOTATION_HINT_KEYS = ("readOnlyHint", "destructiveHint", "idempotentHint", "openWorldHint")
_ANNOTATION_KEYS = ("title",) + _ANNOTATION_HINT_KEYS

CredentialsArg = Union[
    Mapping[str, Optional[CredentialRequirement]],
    Sequence[Union[str, CredentialRequirement]],
]


def _unknown(keys: Any, allowed: tuple) -> List[str]:
    return sorted(str(k) for k in keys if k not in allowed)


def _str_list(where: str, k: str, v: Any) -> List[str]:
    if not isinstance(v, (list, tuple)) or not all(isinstance(s, str) for s in v):
        raise TypeError(f"{where}.{k}: expected a list of strings")
    return list(v)


def _entry_from_ref(ref: str) -> Dict[str, Any]:
    """A bare string: a credential slug, or a capability when dotted."""
    return {"key": ref} if "." in ref else {"slug": ref}


def _check_provider_seed(where: str, seed: Any) -> Dict[str, Any]:
    if not isinstance(seed, dict):
        raise TypeError(f"{where}: expected a dict, got {type(seed).__name__}")
    unknown = _unknown(seed, PROVIDER_SEED_KEYS)
    if unknown:
        raise ValueError(f"{where}: unknown keys {unknown}; allowed: {list(PROVIDER_SEED_KEYS)}")
    for k, v in seed.items():
        if not isinstance(v, str):
            raise TypeError(f"{where}.{k}: expected a string, got {type(v).__name__}")
    return {k: seed[k] for k in PROVIDER_SEED_KEYS if seed.get(k)}


def _check_credential(where: str, entry: Any, slug_from_key: str = "") -> Dict[str, Any]:
    """One entry, in any accepted spelling, as the normalised dict."""
    if isinstance(entry, str):
        entry = _entry_from_ref(entry)
    if not isinstance(entry, dict):
        raise TypeError(f"{where}: expected a dict or a slug, got {type(entry).__name__}")
    unknown = _unknown(entry, CREDENTIAL_KEYS + _LEGACY_CREDENTIAL_KEYS)
    if unknown:
        raise ValueError(f"{where}: unknown keys {unknown}; allowed: {list(CREDENTIAL_KEYS)}")
    for k in _CREDENTIAL_STR_KEYS + _LEGACY_CREDENTIAL_KEYS:
        if k in entry and not isinstance(entry[k], str):
            raise TypeError(f"{where}.{k}: expected a string, got {type(entry[k]).__name__}")
    if "optional" in entry and not isinstance(entry["optional"], bool):
        raise TypeError(f"{where}.optional: expected a bool, got {type(entry['optional']).__name__}")

    slug = entry.get("slug") or ""
    seed: Dict[str, Any] = {}
    provider = entry.get("provider")
    if isinstance(provider, str):
        # The older form: provider was the credential slug.
        if slug and provider != slug:
            raise ValueError(f"{where}: slug {slug!r} and provider {provider!r} disagree")
        slug = provider
    elif provider is not None:
        seed = _check_provider_seed(f"{where}.provider", provider)
    for k in ("name", "website"):
        if entry.get(k):
            seed.setdefault(k, entry[k])

    capabilities = _str_list(where, "capabilities", entry["capabilities"]) if "capabilities" in entry else []
    key = entry.get("key")
    if key:
        if key not in capabilities and "." in key:
            capabilities.append(key)
        owner = key.split(".", 1)[0]
        if not slug:
            slug = owner
    if slug_from_key:
        if slug and slug != slug_from_key:
            raise ValueError(f"{where}: entry says slug {slug!r} but is keyed as {slug_from_key!r}")
        slug = slug_from_key
    if not slug:
        raise ValueError(
            f"{where}: set 'slug' (the credential slug, like 'slack') or a capability under 'capabilities'"
        )
    for capability in capabilities:
        if "." not in capability:
            raise ValueError(f"{where}: capability {capability!r} is not <slug>.<name>")

    auth = entry.get("auth")
    if auth is not None and not isinstance(auth, dict):
        raise TypeError(f"{where}.auth: expected a dict, got {type(auth).__name__}")

    out: Dict[str, Any] = {"slug": slug}
    if capabilities:
        out["capabilities"] = capabilities
    if entry.get("description"):
        out["description"] = entry["description"]
    if "optional" in entry:
        out["optional"] = entry["optional"]
    for k in ("secrets", "scopes"):
        if k in entry:
            v = _str_list(where, k, entry[k])
            if v:
                out[k] = v
    if seed:
        out["provider"] = seed
    if auth:
        out["auth"] = dict(auth)
    return out


def normalize_credentials(credentials: Any, where: str = "@function credentials") -> List[Dict[str, Any]]:
    """Every accepted form of a credentials declaration as the list the
    engine writes: entries in canonical key order, legacy keys folded in."""
    if isinstance(credentials, Mapping):
        if not credentials:
            raise ValueError(f"{where}: empty; omit credentials to use the app-wide list from inf.yml")
        out = []
        for slug, entry in credentials.items():
            if not isinstance(slug, str) or not slug:
                raise TypeError(f"{where}: keys must be credential slugs")
            if entry is not None and not isinstance(entry, dict):
                raise TypeError(f"{where}[{slug!r}]: expected a dict, got {type(entry).__name__}")
            out.append(_check_credential(f"{where}[{slug!r}]", {} if entry is None else entry, slug_from_key=slug))
        return out
    if isinstance(credentials, (str, bytes)) or not isinstance(credentials, Sequence):
        raise TypeError(
            f"{where}: expected a dict keyed by slug or a list of entries, got {type(credentials).__name__}"
        )
    if not credentials:
        raise ValueError(f"{where}: empty list; omit credentials to use the app-wide list from inf.yml")
    return [_check_credential(f"{where}[{i}]", c) for i, c in enumerate(credentials)]


def _check_annotations(annotations: Any) -> Dict[str, Any]:
    if not isinstance(annotations, dict):
        raise TypeError(f"@function annotations: expected a dict, got {type(annotations).__name__}")
    unknown = _unknown(annotations, _ANNOTATION_KEYS)
    if unknown:
        raise ValueError(f"@function annotations: unknown keys {unknown}; allowed: {list(_ANNOTATION_KEYS)}")
    if "title" in annotations and not isinstance(annotations["title"], str):
        raise TypeError("@function annotations.title: expected a string")
    for k in _ANNOTATION_HINT_KEYS:
        v = annotations.get(k)
        if v is not None and not isinstance(v, bool):
            raise TypeError(f"@function annotations.{k}: expected a bool, got {type(v).__name__}")
    # None means "not declared": dropped so the schema omits the hint.
    return {k: v for k, v in annotations.items() if v is not None}


def function(
    *,
    credentials: Optional[CredentialsArg] = None,
    annotations: Optional[ToolAnnotations] = None,
) -> Callable[[F], F]:
    """Declare per-function credentials and MCP tool annotations.

    Args:
        credentials: Credentials this function needs, keyed by credential slug
            like ``inf.yml`` ``credentials:`` (``{"slack": {"capabilities":
            [...]}}``), or as a list of entries or bare slugs. Omit it to give
            the function the app-wide list.
        annotations: MCP tool hints: ``title``, ``readOnlyHint``,
            ``destructiveHint``, ``idempotentHint``, ``openWorldHint``.

    Raises:
        TypeError, ValueError: on a malformed declaration, at decoration time.
    """
    meta: Dict[str, Any] = {}

    if credentials is not None:
        meta["credentials"] = normalize_credentials(credentials)

    if annotations is not None:
        checked = _check_annotations(annotations)
        if checked:
            meta["annotations"] = checked

    def decorate(fn: F) -> F:
        if not callable(fn):
            raise TypeError(f"@function decorates a method, got {type(fn).__name__}")
        setattr(fn, FUNCTION_META_ATTR, meta)
        return fn

    return decorate


__all__ = ["function", "normalize_credentials", "FUNCTION_META_ATTR", "CREDENTIAL_KEYS", "PROVIDER_SEED_KEYS"]
