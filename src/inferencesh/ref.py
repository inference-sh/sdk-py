"""Reference parsing utilities.

Mirrors apitypes.Ref.Parse in Go — the single source of truth for the
[type/]namespace/name[@version][:function] format.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

_REF_TYPES = frozenset({"knowledge", "skill", "app", "agent"})


@dataclass
class Ref:
    """Parsed reference in format ``[type/]namespace/name@version_id:function``."""

    type: str = ""
    namespace: str = ""
    name: str = ""
    version_id: str = ""
    function: str = ""

    # ------------------------------------------------------------------
    # Constructors
    # ------------------------------------------------------------------

    @staticmethod
    def parse(s: str) -> "Ref":
        """Parse a reference string.

        ``@latest`` is treated as unversioned (version_id = "").
        """
        ref = Ref()
        full = s

        # Extract function (after last : that follows @)
        colon_idx = full.rfind(":")
        if colon_idx != -1:
            at_idx = full.rfind("@")
            if at_idx == -1 or colon_idx > at_idx:
                ref.function = full[colon_idx + 1 :]
                full = full[:colon_idx]

        # Extract version
        full_name = full
        at_idx = full.rfind("@")
        if at_idx != -1:
            full_name = full[:at_idx]
            ver = full[at_idx + 1 :]
            if ver != "latest":
                ref.version_id = ver

        # Extract type, namespace, and name
        parts = full_name.split("/", 2)
        if len(parts) >= 3 and parts[0] in _REF_TYPES:
            ref.type = parts[0]
            ref.namespace = parts[1]
            ref.name = parts[2]
        elif len(parts) == 2:
            ref.namespace = parts[0]
            ref.name = parts[1]
        else:
            ref.name = full_name

        return ref

    @staticmethod
    def try_parse(s: str) -> Tuple["Ref", bool]:
        """Parse *s* as a namespaced ref.  Returns ``(ref, True)`` when a namespace is present."""
        ref = Ref.parse(s)
        return ref, bool(ref.namespace)

    # ------------------------------------------------------------------
    # Formatting
    # ------------------------------------------------------------------

    def full_name(self) -> str:
        """Return ``namespace/name``."""
        if self.namespace:
            return f"{self.namespace}/{self.name}"
        return self.name

    def qualified_name(self) -> str:
        """Return ``type/namespace/name`` when type is set, otherwise ``namespace/name``."""
        if self.type:
            return f"{self.type}/{self.full_name()}"
        return self.full_name()

    def is_typed(self) -> bool:
        return bool(self.type)

    def __str__(self) -> str:
        s = self.qualified_name()
        if self.version_id:
            s += f"@{self.version_id}"
        if self.function:
            s += f":{self.function}"
        return s
