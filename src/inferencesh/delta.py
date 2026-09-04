"""Generic delta accumulator driven by _field_tags merge strategies."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .llm_types_gen import LLMDelta, LLMOutput, MergeStrategy, StreamDelta


def _get_field_tags(obj: Any) -> dict:
    cls = type(obj) if not isinstance(obj, type) else obj
    tags = cls.__dict__.get('_field_tags')
    if tags is None:
        return {}
    if isinstance(tags, dict):
        return tags
    if hasattr(tags, 'default'):
        return tags.default or {}
    return {}


def _merge_value(current: Any, incoming: Any, strategy: MergeStrategy) -> Any:
    if incoming is None:
        return current
    if strategy is MergeStrategy.CONCAT:
        if current is None:
            return incoming
        if isinstance(current, str) and isinstance(incoming, str):
            return current + incoming
        return incoming
    if strategy is MergeStrategy.REPLACE:
        return incoming
    if strategy is MergeStrategy.INDEXED:
        return _merge_indexed(current, incoming)
    if strategy is MergeStrategy.NESTED:
        # Start from the delta's set fields only; model defaults (e.g. "")
        # must not be recorded as state or they overwrite later real values.
        if current is None:
            return merge_delta({}, incoming)
        return merge_delta(_to_dict(current), incoming)
    return incoming


def _merge_indexed(current: Optional[List], incoming: List) -> List:
    if current is None:
        current = []
    by_index: Dict[int, Any] = {}
    for item in current:
        idx = item.get("index", 0) if isinstance(item, dict) else getattr(item, "index", 0)
        by_index[idx] = _to_dict(item)
    for item in incoming:
        idx = item.get("index", 0) if isinstance(item, dict) else getattr(item, "index", 0)
        existing = by_index.get(idx)
        if existing is None:
            by_index[idx] = _to_delta_dict(item)
        else:
            by_index[idx] = merge_delta(existing, item)
    return [by_index[k] for k in sorted(by_index)]


def _to_dict(obj: Any) -> dict:
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):
        return obj.model_dump(exclude_none=True)
    return dict(obj)


def _to_delta_dict(obj: Any) -> dict:
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):
        return obj.model_dump(exclude_unset=True)
    return dict(obj)


def _strategy_for(tags: dict, field_name: str, value: Any) -> MergeStrategy:
    """Strategy from the type's _field_tags; untagged strings concat, others replace."""
    tag = tags.get(field_name, {}).get("merge")
    if tag:
        return MergeStrategy(tag)
    return MergeStrategy.CONCAT if isinstance(value, str) else MergeStrategy.REPLACE


def merge_delta(current: dict, delta: Any) -> dict:
    """Merge a delta into accumulated state using _field_tags.

    Reads merge strategies from the delta type's _field_tags ClassVar.
    Fields without tags default to concat for strings, replace for others.
    """
    tags = _get_field_tags(delta)
    delta_dict = _to_delta_dict(delta)

    # Recursive strategies (indexed, nested) must receive the raw pydantic
    # value, not its serialized dict, so the child type's _field_tags are
    # still available at the next level.
    raw_delta = delta if not isinstance(delta, dict) else None

    for field_name, value in delta_dict.items():
        if value is None:
            continue
        strategy = _strategy_for(tags, field_name, value)

        if strategy in (MergeStrategy.INDEXED, MergeStrategy.NESTED) and raw_delta is not None:
            value = getattr(raw_delta, field_name, value)
        current[field_name] = _merge_value(current.get(field_name), value, strategy)

    return current


class DeltaAccumulator:
    """Generic accumulator that merges StreamDelta events using _field_tags."""

    def __init__(self) -> None:
        self._state: dict = {}

    def seed(self, output: dict) -> None:
        self._state.update(output)

    def apply(self, delta: StreamDelta) -> None:
        self._state = merge_delta(self._state, delta)

    def to_dict(self) -> dict:
        return dict(self._state)

    def to_output(self) -> LLMOutput:
        return LLMOutput(**self._state)
