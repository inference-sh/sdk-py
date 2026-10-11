"""Per-function metadata for app functions.

``@function`` declares what one app function needs and how it behaves:

    from inferencesh import BaseApp, function

    class App(BaseApp):
        @function(
            credentials=[{"key": "google.calendar.events"}],
            annotations={"readOnlyHint": False, "destructiveHint": False},
        )
        async def create_event(self, input_data: CreateEventInput) -> CreateEventOutput: ...

The engine's function discovery reads the metadata at deploy time and writes it
to the function's entry in ``functions_schema.json``.

- ``credentials``: the credentials this function needs at run time. Each entry
  has the shape of an ``inf.yml`` ``credentials:`` entry and must be covered by
  the app-wide list there. A function without ``credentials`` gets the whole
  app-wide list.
- ``annotations``: MCP tool hints (``title``, ``readOnlyHint``,
  ``destructiveHint``, ``idempotentHint``, ``openWorldHint``).

The decorator returns the function itself; it only sets
``__inferencesh_function__`` on it.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, TypeVar

from .types import CredentialRequirement, ToolAnnotations

F = TypeVar("F", bound=Callable[..., Any])

FUNCTION_META_ATTR = "__inferencesh_function__"

_CREDENTIAL_STR_KEYS = ("provider", "name", "website", "key", "description")
_CREDENTIAL_LIST_KEYS = ("secrets", "scopes")
_CREDENTIAL_KEYS = _CREDENTIAL_STR_KEYS + ("optional",) + _CREDENTIAL_LIST_KEYS
_ANNOTATION_HINT_KEYS = ("readOnlyHint", "destructiveHint", "idempotentHint", "openWorldHint")
_ANNOTATION_KEYS = ("title",) + _ANNOTATION_HINT_KEYS


def _unknown(keys: Any, allowed: tuple) -> List[str]:
    return sorted(str(k) for k in keys if k not in allowed)


def _check_credential(i: int, entry: Any) -> Dict[str, Any]:
    where = f"@function credentials[{i}]"
    if not isinstance(entry, dict):
        raise TypeError(f"{where}: expected a dict, got {type(entry).__name__}")
    unknown = _unknown(entry, _CREDENTIAL_KEYS)
    if unknown:
        raise ValueError(f"{where}: unknown keys {unknown}; allowed: {list(_CREDENTIAL_KEYS)}")
    for k in _CREDENTIAL_STR_KEYS:
        if k in entry and not isinstance(entry[k], str):
            raise TypeError(f"{where}.{k}: expected a string, got {type(entry[k]).__name__}")
    if "optional" in entry and not isinstance(entry["optional"], bool):
        raise TypeError(f"{where}.optional: expected a bool, got {type(entry['optional']).__name__}")
    for k in _CREDENTIAL_LIST_KEYS:
        if k in entry:
            v = entry[k]
            if not isinstance(v, (list, tuple)) or not all(isinstance(s, str) for s in v):
                raise TypeError(f"{where}.{k}: expected a list of strings")
    if not entry.get("key") and not entry.get("provider"):
        raise ValueError(f"{where}: set 'key' (a capability like 'google.calendar.events') or 'provider'")
    return {k: (list(v) if k in _CREDENTIAL_LIST_KEYS else v) for k, v in entry.items()}


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
    credentials: Optional[List[CredentialRequirement]] = None,
    annotations: Optional[ToolAnnotations] = None,
) -> Callable[[F], F]:
    """Declare per-function credentials and MCP tool annotations.

    Args:
        credentials: Credentials this function needs, each shaped like an
            ``inf.yml`` ``credentials:`` entry (``key`` for a capability such as
            ``"google.calendar.events"``, or ``provider`` with ``secrets`` /
            ``scopes``). Omit it to give the function the app-wide list.
        annotations: MCP tool hints: ``title``, ``readOnlyHint``,
            ``destructiveHint``, ``idempotentHint``, ``openWorldHint``.

    Raises:
        TypeError, ValueError: on a malformed declaration, at decoration time.
    """
    meta: Dict[str, Any] = {}

    if credentials is not None:
        if isinstance(credentials, (str, bytes, dict)) or not isinstance(credentials, (list, tuple)):
            raise TypeError(f"@function credentials: expected a list of dicts, got {type(credentials).__name__}")
        if not credentials:
            raise ValueError(
                "@function credentials: empty list; omit credentials to use the app-wide list from inf.yml"
            )
        meta["credentials"] = [_check_credential(i, c) for i, c in enumerate(credentials)]

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


__all__ = ["function", "FUNCTION_META_ATTR"]
