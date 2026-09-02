"""Tests for the generic delta accumulator."""

from typing import ClassVar, List, Optional

import pytest
from pydantic import BaseModel

from inferencesh.delta import DeltaAccumulator, merge_delta
from inferencesh.llm_types_gen import (
    LLMDelta,
    StreamDelta,
    ToolCallDelta,
    ToolCallFunctionDelta,
)


# ── Custom delta type to prove genericity ──────────────────────

class CustomDelta(StreamDelta):
    text: str = ""
    score: Optional[float] = None
    metadata: Optional[dict] = None

    _field_tags: ClassVar[dict] = {
        "text": {"merge": "concat"},
        "score": {"merge": "replace"},
        "metadata": {"merge": "nested"},
    }


# ── concat strategy ────────────────────────────────────────────

class TestConcat:
    def test_string_append(self):
        state = merge_delta({}, LLMDelta(response="hello "))
        state = merge_delta(state, LLMDelta(response="world"))
        assert state["response"] == "hello world"

    def test_optional_concat(self):
        state = merge_delta({}, LLMDelta(response="", reasoning="step "))
        state = merge_delta(state, LLMDelta(response="", reasoning="one"))
        assert state["reasoning"] == "step one"

    def test_none_skipped(self):
        state = merge_delta({}, LLMDelta(response="first", reasoning="r"))
        state = merge_delta(state, LLMDelta(response=" second"))
        assert state["response"] == "first second"
        assert state["reasoning"] == "r"

    def test_multiple_deltas(self):
        state: dict = {}
        for word in ["The ", "quick ", "brown ", "fox"]:
            state = merge_delta(state, LLMDelta(response=word))
        assert state["response"] == "The quick brown fox"


# ── replace strategy ───────────────────────────────────────────

class TestReplace:
    def test_overwrite(self):
        state = merge_delta({}, CustomDelta(text="", score=0.5))
        state = merge_delta(state, CustomDelta(text="", score=0.9))
        assert state["score"] == 0.9

    def test_none_preserves_previous(self):
        state = merge_delta({}, CustomDelta(text="x", score=0.5))
        state = merge_delta(state, CustomDelta(text="y"))
        assert state["score"] == 0.5


# ── indexed strategy ──────────────────────────────────────────

class TestIndexed:
    def test_single_tool_call(self):
        d1 = LLMDelta(
            response="",
            tool_calls=[ToolCallDelta(index=0, id="call-1", function=ToolCallFunctionDelta(name="search", arguments='{"q"'))],
        )
        d2 = LLMDelta(
            response="",
            tool_calls=[ToolCallDelta(index=0, function=ToolCallFunctionDelta(arguments=': "hello"}'))],
        )
        state = merge_delta({}, d1)
        state = merge_delta(state, d2)

        tc = state["tool_calls"]
        assert len(tc) == 1
        assert tc[0]["id"] == "call-1"
        assert tc[0]["function"]["name"] == "search"
        assert tc[0]["function"]["arguments"] == '{"q": "hello"}'

    def test_multiple_indices(self):
        d1 = LLMDelta(
            response="",
            tool_calls=[
                ToolCallDelta(index=0, id="a"),
                ToolCallDelta(index=1, id="b"),
            ],
        )
        d2 = LLMDelta(
            response="",
            tool_calls=[ToolCallDelta(index=1, function=ToolCallFunctionDelta(name="fn-b"))],
        )
        state = merge_delta({}, d1)
        state = merge_delta(state, d2)

        assert len(state["tool_calls"]) == 2
        assert state["tool_calls"][0]["id"] == "a"
        assert state["tool_calls"][1]["id"] == "b"
        assert state["tool_calls"][1]["function"]["name"] == "fn-b"


# ── nested strategy ───────────────────────────────────────────

class TestNested:
    def test_recursive_merge(self):
        state = merge_delta({}, CustomDelta(text="", metadata={"model": "gpt-4"}))
        state = merge_delta(state, CustomDelta(text="", metadata={"temp": 0.7}))
        assert state["metadata"]["model"] == "gpt-4"
        assert state["metadata"]["temp"] == 0.7

    def test_tool_call_function_nested(self):
        d1 = LLMDelta(
            response="",
            tool_calls=[ToolCallDelta(index=0, function=ToolCallFunctionDelta(name="calc", arguments='{"a":'))],
        )
        d2 = LLMDelta(
            response="",
            tool_calls=[ToolCallDelta(index=0, function=ToolCallFunctionDelta(arguments=' 1}'))],
        )
        state = merge_delta({}, d1)
        state = merge_delta(state, d2)

        fn = state["tool_calls"][0]["function"]
        assert fn["name"] == "calc"
        assert fn["arguments"] == '{"a": 1}'


# ── DeltaAccumulator class ────────────────────────────────────

class TestDeltaAccumulator:
    def test_apply_and_to_dict(self):
        acc = DeltaAccumulator()
        acc.apply(LLMDelta(response="hello "))
        acc.apply(LLMDelta(response="world"))
        assert acc.to_dict() == {"response": "hello world"}

    def test_to_output(self):
        acc = DeltaAccumulator()
        acc.apply(LLMDelta(response="test"))
        out = acc.to_output()
        assert out.response == "test"

    def test_seed(self):
        acc = DeltaAccumulator()
        acc.seed({"response": "seed"})
        acc.apply(LLMDelta(response=" more"))
        assert acc.to_dict()["response"] == "seed more"

    def test_custom_delta_type(self):
        acc = DeltaAccumulator()
        acc.apply(CustomDelta(text="one "))
        acc.apply(CustomDelta(text="two", score=42.0))
        d = acc.to_dict()
        assert d["text"] == "one two"
        assert d["score"] == 42.0

    def test_no_tags_defaults(self):
        """Delta type without _field_tags: strings concat, others replace."""

        class PlainDelta(StreamDelta):
            content: str = ""
            count: int = 0

        acc = DeltaAccumulator()
        acc.apply(PlainDelta(content="a"))
        acc.apply(PlainDelta(content="b", count=5))
        d = acc.to_dict()
        assert d["content"] == "ab"
        assert d["count"] == 5
