"""Tests for the OpenAI Chat Completions adapter."""

import json
from typing import AsyncGenerator, Union

import pytest
from pydantic import Field

from inferencesh import BaseApp, BaseAppOutput
from inferencesh.delta import DeltaAccumulator
from inferencesh.models.llm import LLMDelta, LLMInput, LLMOutput, LLMUsage
from inferencesh.llm_types_gen import ResponseFormatType, ToolCallDelta, ToolCallFunctionDelta, ToolChoiceMode
from inferencesh.openai import (
    ChatCompletion,
    ChatCompletionChunk,
    ChatCompletionInput,
    OpenAIChatMixin,
    UnsupportedParameterError,
    to_llm_input,
)


def req(**kw) -> ChatCompletionInput:
    kw.setdefault("messages", [{"role": "user", "content": "hi"}])
    return ChatCompletionInput(**kw)


# ── request → LLMInput ────────────────────────────────────────────────

class TestToLLMInput:
    def test_system_and_current_turn(self):
        i = to_llm_input(req(messages=[
            {"role": "system", "content": "be brief"},
            {"role": "user", "content": "hi"},
        ]))
        assert i.system_prompt == "be brief"
        assert i.text == "hi"
        assert i.context == []

    def test_developer_role_joins_system(self):
        i = to_llm_input(req(messages=[
            {"role": "system", "content": "a"},
            {"role": "developer", "content": "b"},
            {"role": "user", "content": "hi"},
        ]))
        assert i.system_prompt == "a\n\nb"

    def test_history_goes_to_context_last_turn_is_current(self):
        i = to_llm_input(req(messages=[
            {"role": "user", "content": "q1"},
            {"role": "assistant", "content": "a1"},
            {"role": "user", "content": "q2"},
        ]))
        assert [m.text for m in i.context] == ["q1", "a1"]
        assert i.text == "q2"

    def test_multipart_content_with_image(self):
        i = to_llm_input(req(messages=[{"role": "user", "content": [
            {"type": "text", "text": "what is this"},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64,iVBORw0KGgo="}},
        ]}]))
        assert i.text == "what is this"
        assert i.images and i.images[0].uri.startswith("data:image/png")

    def test_tool_result_turn(self):
        i = to_llm_input(req(messages=[
            {"role": "user", "content": "weather?"},
            {"role": "assistant", "content": None, "tool_calls": [
                {"id": "c1", "type": "function", "function": {"name": "get_weather", "arguments": "{\"city\":\"x\"}"}},
            ]},
            {"role": "tool", "tool_call_id": "c1", "content": "sunny"},
        ]))
        assert i.role == "tool"
        assert i.tool_call_id == "c1"
        assert i.text == "sunny"
        assert i.context[1].tool_calls[0]["function"]["name"] == "get_weather"

    def test_sampling_params_mapped(self):
        i = to_llm_input(req(temperature=0.1, top_p=0.5, seed=7, stop="END",
                             max_completion_tokens=99, frequency_penalty=0.3,
                             presence_penalty=-0.2, reasoning_effort="xhigh"))
        assert (i.temperature, i.top_p, i.seed) == (0.1, 0.5, 7)
        assert i.stop == ["END"]
        assert i.max_tokens == 99
        assert (i.frequency_penalty, i.presence_penalty) == (0.3, -0.2)
        assert i.reasoning_effort == "high"

    def test_max_completion_tokens_wins_over_max_tokens(self):
        assert to_llm_input(req(max_tokens=10, max_completion_tokens=20)).max_tokens == 20

    def test_unset_params_keep_app_defaults(self):
        class AppInput(LLMInput):
            context_size: int = Field(default=123456)

        i = to_llm_input(req(), AppInput)
        assert isinstance(i, AppInput)
        assert i.context_size == 123456
        assert i.temperature == LLMInput.model_fields["temperature"].default

    def test_tools_passed_and_tool_choice_none_drops_them(self):
        tools = [{"type": "function", "function": {"name": "f", "parameters": {"type": "object"}}}]
        assert to_llm_input(req(tools=tools)).tools[0]["function"]["name"] == "f"
        assert to_llm_input(req(tools=tools, tool_choice="none")).tools is None

    @pytest.mark.parametrize("kw,param", [
        ({"n": 2}, "n"),
        ({"logprobs": True}, "logprobs"),
        ({"logit_bias": {"1": 1.0}}, "logit_bias"),
        ({"modalities": ["audio"]}, "modalities"),
        ({"moderation": {"model": "omni-moderation-latest"}}, "moderation"),
        ({"functions": [{"name": "f"}], "tools": [{"type": "function", "function": {"name": "g"}}]}, "functions"),
    ])
    def test_unsupported_rejected(self, kw, param):
        with pytest.raises(UnsupportedParameterError) as e:
            to_llm_input(req(**kw))
        assert e.value.param == param

    def test_tool_choice_modes(self):
        tools = [{"type": "function", "function": {"name": "f"}}]
        assert to_llm_input(req(tools=tools)).tool_choice is None
        assert to_llm_input(req(tools=tools, tool_choice="auto")).tool_choice.mode == ToolChoiceMode.AUTO
        assert to_llm_input(req(tools=tools, tool_choice="required")).tool_choice.mode == ToolChoiceMode.REQUIRED
        named = to_llm_input(req(tools=tools, tool_choice={"type": "function", "function": {"name": "f"}})).tool_choice
        assert (named.mode, named.name) == (ToolChoiceMode.FUNCTION, "f")

    def test_deprecated_functions_api_lifted_to_tools(self):
        i = to_llm_input(req(functions=[{"name": "f", "parameters": {"type": "object"}}], function_call={"name": "f"}))
        assert i.tools == [{"type": "function", "function": {"name": "f", "parameters": {"type": "object"}}}]
        assert (i.tool_choice.mode, i.tool_choice.name) == (ToolChoiceMode.FUNCTION, "f")

    def test_response_format_json_object(self):
        rf = to_llm_input(req(response_format={"type": "json_object"})).response_format
        assert rf.type == ResponseFormatType.JSON_OBJECT and rf.json_schema is None

    def test_response_format_json_schema_flattened(self):
        rf = to_llm_input(req(response_format={"type": "json_schema", "json_schema": {
            "name": "answer", "strict": True, "schema": {"type": "object", "properties": {"x": {"type": "integer"}}},
        }})).response_format
        assert rf.type == ResponseFormatType.JSON_SCHEMA
        assert rf.name == "answer" and rf.strict is True
        assert rf.json_schema["properties"]["x"]["type"] == "integer"

    def test_response_format_json_schema_requires_spec(self):
        with pytest.raises(ValueError, match="json_schema is required"):
            to_llm_input(req(response_format={"type": "json_schema"}))

    def test_ignored_params_accepted(self):
        to_llm_input(req(user="u", metadata={"k": "v"}, store=True, parallel_tool_calls=False, n=1,
                         prompt_cache_options={"mode": "implicit", "ttl": "30m"}))

    def test_unknown_extra_field_tolerated(self):
        to_llm_input(ChatCompletionInput(messages=[{"role": "user", "content": "hi"}], some_future_param=1))


# ── app → chunks / completion ─────────────────────────────────────────

class AppInput(LLMInput):
    pass


class AppOutput(LLMOutput, BaseAppOutput):
    pass


DEFAULT_MODEL = "test/delta"


class DeltaApp(OpenAIChatMixin, BaseApp):

    async def run(self, input_data: AppInput) -> AsyncGenerator[Union[LLMDelta, AppOutput], None]:
        yield LLMDelta(response="Hel")
        yield LLMDelta(response="lo", reasoning="think")
        yield LLMDelta(tool_calls=[ToolCallDelta(index=0, id="c1", type="function",
                                                 function=ToolCallFunctionDelta(name="f", arguments='{"a"'))])
        yield LLMDelta(tool_calls=[ToolCallDelta(index=0, function=ToolCallFunctionDelta(arguments=':1}'))])
        yield AppOutput(
            response="Hello", reasoning="think",
            tool_calls=[{"id": "c1", "type": "function", "function": {"name": "f", "arguments": {"a": 1}}}],
            usage=LLMUsage(prompt_tokens=3, completion_tokens=5, total_tokens=8, reasoning_tokens=2),
        )


class ProgressApp(OpenAIChatMixin, BaseApp):
    """Legacy app: yields cumulative outputs, no deltas."""

    async def run(self, input_data: AppInput, metadata) -> AsyncGenerator[AppOutput, None]:
        yield AppOutput(response="Hel")
        yield AppOutput(response="Hello")
        yield AppOutput(response="Hello!")


async def collect(app):
    chunks, finals = [], []
    async for out in app.openai(req(stream=True, stream_options={"include_usage": True})):
        (chunks if isinstance(out, ChatCompletionChunk) else finals).append(out)
    return chunks, finals


class TestDeltaApp:
    @pytest.mark.asyncio
    async def test_chunks_and_completion(self):
        chunks, finals = await collect(DeltaApp())

        assert chunks[0].choices[0].delta.role == "assistant"
        assert chunks[0].choices[0].delta.content == "Hel"
        assert chunks[1].choices[0].delta.content == "lo"
        assert chunks[1].choices[0].delta.reasoning == "think"
        tc = chunks[2].choices[0].delta.tool_calls[0]
        assert (tc.index, tc.id, tc.function.name, tc.function.arguments) == (0, "c1", "f", '{"a"')
        assert chunks[3].choices[0].delta.tool_calls[0].function.arguments == ':1}'
        assert chunks[3].choices[0].delta.tool_calls[0].id is None

        assert chunks[-2].choices[0].finish_reason == "tool_calls"
        assert chunks[-1].choices == [] and chunks[-1].usage.total_tokens == 8
        assert chunks[-1].usage.completion_tokens_details.reasoning_tokens == 2
        assert len({c.id for c in chunks}) == 1
        assert all(c.model == "test/delta" for c in chunks)

        assert len(finals) == 1
        final = finals[0]
        assert isinstance(final, ChatCompletion)
        assert final.id == chunks[0].id
        msg = final.choices[0].message
        assert msg.content == "Hello"
        assert msg.tool_calls[0].function.arguments == json.dumps({"a": 1})
        assert final.choices[0].finish_reason == "tool_calls"
        assert final.usage.prompt_tokens == 3

    @pytest.mark.asyncio
    async def test_chunks_merge_with_generic_accumulator(self):
        chunks, finals = await collect(DeltaApp())
        acc = DeltaAccumulator()
        for c in chunks:
            acc.apply(c)
        merged = acc.to_dict()

        choice = merged["choices"][0]
        assert choice["delta"]["content"] == "Hello"
        assert choice["delta"]["reasoning"] == "think"
        assert choice["delta"]["tool_calls"][0]["function"]["arguments"] == '{"a":1}'
        assert choice["delta"]["tool_calls"][0]["id"] == "c1"
        assert choice["finish_reason"] == "tool_calls"
        assert merged["usage"]["total_tokens"] == 8

    @pytest.mark.asyncio
    async def test_no_usage_chunk_without_include_usage(self):
        chunks = [o async for o in DeltaApp().openai(req()) if isinstance(o, ChatCompletionChunk)]
        assert chunks[-1].choices[0].finish_reason == "tool_calls"
        assert chunks[-1].usage is None


class TestProgressApp:
    @pytest.mark.asyncio
    async def test_diffs_progress_into_chunks(self):
        chunks, finals = await collect(ProgressApp())
        contents = [c.choices[0].delta.content for c in chunks if c.choices and c.choices[0].delta.content]
        assert contents == ["Hel", "lo", "!"]
        assert finals[0].choices[0].message.content == "Hello!"
        assert finals[0].choices[0].finish_reason == "stop"
        assert finals[0].usage is None

    @pytest.mark.asyncio
    async def test_model_falls_back_to_request(self):
        outs = [o async for o in ProgressApp().openai(req(model="req/model"))]
        assert outs[-1].model == "req/model"


class ContractDeltaApp(OpenAIChatMixin, BaseApp):
    """Yields the generated-contract LLMDelta (what stream_generate / OutputDiffer build),
    not the app-layer subclass. Both must become chunks."""

    async def run(self, input_data: AppInput) -> AsyncGenerator[Union[LLMDelta, AppOutput], None]:
        from inferencesh.llm_types_gen import LLMDelta as ContractDelta
        yield ContractDelta(response="Hel")
        yield ContractDelta(response="lo")
        yield AppOutput(response="Hello")


class TestContractDeltaApp:
    @pytest.mark.asyncio
    async def test_contract_deltas_become_chunks(self):
        chunks, finals = await collect(ContractDeltaApp())
        contents = [c.choices[0].delta.content for c in chunks if c.choices and c.choices[0].delta.content]
        assert contents == ["Hel", "lo"]
        assert finals[0].choices[0].message.content == "Hello"
