"""stream_generate (llama.cpp path): delta yielding and LLMInput param mapping."""

from typing import Any, Dict, List

import pytest

from inferencesh.llm_types_gen import (
    LLMDelta,
    ResponseFormat,
    ResponseFormatType,
    ToolChoice,
    ToolChoiceMode,
)
from inferencesh.models.llm import (
    LLMOutput,
    ResponseTransformer,
    llamacpp_response_format,
    openai_response_format,
    openai_tool_choice,
    stream_generate,
)


class FakeLlama:
    """Records create_chat_completion kwargs and replays OpenAI-style chunks."""

    def __init__(self, pieces: List[str]):
        self.pieces = pieces
        self.kwargs: Dict[str, Any] = {}

    def create_chat_completion(self, **kwargs):
        self.kwargs = kwargs
        for i, piece in enumerate(self.pieces):
            last = i == len(self.pieces) - 1
            yield {
                "choices": [{"delta": {"content": piece}, "finish_reason": "stop" if last else None}],
                "usage": {"prompt_tokens": 3, "completion_tokens": i + 1, "total_tokens": 4 + i} if last else None,
            }


def run(model, **kw):
    return list(stream_generate(model=model, messages=[{"role": "user", "content": "hi"}],
                                transformer=ResponseTransformer(), output_cls=LLMOutput, **kw))


class TestMappers:
    def test_tool_choice(self):
        assert openai_tool_choice(None) == "auto"
        assert openai_tool_choice(ToolChoice(mode=ToolChoiceMode.REQUIRED)) == "required"
        assert openai_tool_choice(ToolChoice(mode=ToolChoiceMode.NONE)) == "none"
        assert openai_tool_choice(ToolChoice(mode=ToolChoiceMode.FUNCTION, name="f")) == {
            "type": "function", "function": {"name": "f"}}

    def test_openai_response_format(self):
        assert openai_response_format(None) is None
        assert openai_response_format(ResponseFormat(type=ResponseFormatType.TEXT)) is None
        assert openai_response_format(ResponseFormat(type=ResponseFormatType.JSON_OBJECT)) == {"type": "json_object"}
        rf = ResponseFormat(type=ResponseFormatType.JSON_SCHEMA, name="a", json_schema={"type": "object"}, strict=True)
        assert openai_response_format(rf) == {"type": "json_schema", "json_schema": {
            "name": "a", "schema": {"type": "object"}, "strict": True}}

    def test_llamacpp_response_format_uses_grammar_spelling(self):
        rf = ResponseFormat(type=ResponseFormatType.JSON_SCHEMA, json_schema={"type": "object"})
        assert llamacpp_response_format(rf) == {"type": "json_object", "schema": {"type": "object"}}
        assert llamacpp_response_format(ResponseFormat(type=ResponseFormatType.JSON_OBJECT)) == {"type": "json_object"}


class TestStreamGenerate:
    def test_cumulative_outputs_by_default(self):
        outs = run(FakeLlama(["Hel", "lo"]))
        assert [o.response for o in outs] == ["Hel", "Hello"]
        assert outs[-1].usage.completion_tokens == 2

    def test_with_deltas_yields_pairs(self):
        pairs = run(FakeLlama(["Hel", "lo", ""]), with_deltas=True)
        outputs = [o for o, _ in pairs]
        deltas = [d for _, d in pairs]
        assert [o.response for o in outputs] == ["Hel", "Hello", "Hello"]
        assert isinstance(deltas[0], LLMDelta) and deltas[0].response == "Hel"
        assert deltas[1].response == "lo"
        assert deltas[2] is None  # usage-only chunk, no text change

    def test_think_tags_become_reasoning_deltas(self):
        pairs = run(FakeLlama(["<think>plan", "</think>", "answer"]), with_deltas=True)
        final = pairs[-1][0]
        assert final.reasoning == "plan" and final.response == "answer"
        reasoning = "".join(d.reasoning for _, d in pairs if d and d.reasoning)
        response = "".join(d.response for _, d in pairs if d and d.response)
        assert reasoning == "plan" and response == "answer"

    def test_llminput_params_translated_for_llamacpp(self):
        model = FakeLlama(["x"])
        run(model,
            tools=[{"type": "function", "function": {"name": "f"}}],
            tool_choice=ToolChoice(mode=ToolChoiceMode.FUNCTION, name="f"),
            response_format=ResponseFormat(type=ResponseFormatType.JSON_SCHEMA, json_schema={"type": "object"}))
        assert model.kwargs["tool_choice"] == {"type": "function", "function": {"name": "f"}}
        assert model.kwargs["response_format"] == {"type": "json_object", "schema": {"type": "object"}}

    def test_preshaped_dicts_pass_through(self):
        model = FakeLlama(["x"])
        run(model, tool_choice="required", response_format={"type": "json_object"})
        assert model.kwargs["tool_choice"] == "required"
        assert model.kwargs["response_format"] == {"type": "json_object"}
