"""Tests for LLM message/tool builders (build_openai_messages, build_tools)."""

import os
import tempfile
from unittest.mock import patch

import pytest

from inferencesh import File
from pydantic import ValidationError

from inferencesh.models.llm import (
    BaseLLMInput,
    ChatInput,
    ContextMessage,
    ContextMessageRole,
    LLMInput,
    ModelSettings,
    build_messages,
    build_openai_messages,
    build_tools,
    file_to_base64_data_uri,
    image_to_base64_data_uri,
)


def _file(uri: str) -> File:
    """Create a File without network I/O."""
    with patch.object(File, "_download_url"):
        return File(uri=uri)


class TestBuildOpenAIMessages:
    def test_text_only_user_message_is_plain_string(self):
        messages = build_openai_messages(LLMInput(text="hello", context=[], system_prompt=""))
        assert messages == [{"role": "user", "content": "hello"}]

    def test_system_prompt_prepended(self):
        messages = build_openai_messages(
            LLMInput(text="hi", context=[], system_prompt="You are helpful."),
        )
        assert messages[0] == {"role": "system", "content": "You are helpful."}
        assert messages[-1]["content"] == "hi"

    def test_empty_system_prompt_omitted(self):
        messages = build_openai_messages(LLMInput(text="hi", context=[], system_prompt=""))
        assert all(m["role"] != "system" for m in messages)

    def test_transform_user_message_applies_to_user_text_only(self):
        messages = build_openai_messages(
            LLMInput(
                text="raw",
                context=[
                    ContextMessage(role=ContextMessageRole.ASSISTANT, text="assistant raw"),
                ],
                system_prompt="",
            ),
            transform_user_message=lambda s: s.upper(),
        )
        user = next(m for m in messages if m["role"] == "user")
        assistant = next(m for m in messages if m["role"] == "assistant")
        assert user["content"] == "RAW"
        assert assistant["content"] == "assistant raw"

    def test_consecutive_same_role_messages_merged(self):
        messages = build_openai_messages(
            LLMInput(
                text="second",
                context=[
                    ContextMessage(role=ContextMessageRole.USER, text="first"),
                ],
                system_prompt="",
            ),
        )
        user_messages = [m for m in messages if m["role"] == "user"]
        assert len(user_messages) == 1
        assert user_messages[0]["content"] == "first\n\nsecond"

    def test_image_url_mode_uses_http_uri_without_download(self):
        image = _file("https://cdn.example.com/photo.png")
        messages = build_openai_messages(
            LLMInput(
                text="describe",
                context=[
                    ContextMessage(
                        role=ContextMessageRole.USER,
                        text="look",
                        images=[image],
                    ),
                ],
                system_prompt="",
            ),
            image_mode="url",
        )
        user = next(m for m in messages if m["role"] == "user")
        assert isinstance(user["content"], list)
        image_parts = [p for p in user["content"] if p["type"] == "image_url"]
        assert len(image_parts) == 1
        assert image_parts[0]["image_url"]["url"] == "https://cdn.example.com/photo.png"

    def test_tool_calls_arguments_serialized_as_json_strings(self):
        messages = build_openai_messages(
            LLMInput(
                text="",
                context=[
                    ContextMessage(
                        role=ContextMessageRole.ASSISTANT,
                        text="",
                        tool_calls=[
                            {
                                "id": "call_1",
                                "type": "function",
                                "function": {
                                    "name": "search",
                                    "arguments": {"q": "weather"},
                                },
                            }
                        ],
                    ),
                ],
                system_prompt="",
            ),
        )
        assistant = next(m for m in messages if m["role"] == "assistant")
        assert assistant["tool_calls"][0]["function"]["arguments"] == '{"q": "weather"}'
        assert assistant["content"] is None

    def test_assistant_tool_calls_with_empty_text_sets_content_null(self):
        """Providers like MiniMax reject assistant tool_call messages with content=\"\"."""
        messages = build_openai_messages(
            LLMInput(
                text="",
                context=[
                    ContextMessage(
                        role=ContextMessageRole.USER,
                        text="What's the weather?",
                    ),
                    ContextMessage(
                        role=ContextMessageRole.ASSISTANT,
                        text="",
                        tool_calls=[
                            {
                                "id": "call_1",
                                "type": "function",
                                "function": {
                                    "name": "search",
                                    "arguments": {"q": "weather"},
                                },
                            }
                        ],
                    ),
                ],
                system_prompt="",
            ),
        )
        assistant = next(m for m in messages if m["role"] == "assistant")
        assert assistant["tool_calls"]
        assert assistant["content"] is None
        assert assistant["content"] != ""

    def test_assistant_tool_calls_with_text_preserves_content(self):
        messages = build_openai_messages(
            LLMInput(
                text="",
                context=[
                    ContextMessage(
                        role=ContextMessageRole.ASSISTANT,
                        text="I'll look that up.",
                        tool_calls=[
                            {
                                "id": "call_1",
                                "type": "function",
                                "function": {
                                    "name": "search",
                                    "arguments": {"q": "weather"},
                                },
                            }
                        ],
                    ),
                ],
                system_prompt="",
            ),
        )
        assistant = next(m for m in messages if m["role"] == "assistant")
        assert assistant["content"] == "I'll look that up."

    def test_tool_role_message_includes_tool_call_id(self):
        messages = build_openai_messages(
            LLMInput(
                text="",
                context=[
                    ContextMessage(
                        role=ContextMessageRole.TOOL,
                        text="result",
                        tool_call_id="call_abc",
                    ),
                ],
                system_prompt="",
            ),
        )
        tool_msg = next(m for m in messages if m["role"] == "tool")
        assert tool_msg["tool_call_id"] == "call_abc"

    def test_tool_role_message_without_tool_call_id_defaults_to_empty_string(self):
        """OpenAI requires tool_call_id on tool messages; missing id must not be omitted."""
        messages = build_openai_messages(
            LLMInput(
                text="",
                context=[
                    ContextMessage(
                        role=ContextMessageRole.TOOL,
                        text="result",
                    ),
                ],
                system_prompt="",
            ),
        )
        tool_msg = next(m for m in messages if m["role"] == "tool")
        assert tool_msg["tool_call_id"] == ""

    def test_consecutive_same_role_messages_merge_images_and_files(self):
        img1 = _file("https://cdn.example.com/a.png")
        img2 = _file("https://cdn.example.com/b.png")
        doc1 = _file("https://cdn.example.com/a.pdf")
        doc2 = _file("https://cdn.example.com/b.pdf")
        messages = build_openai_messages(
            LLMInput(
                text="second",
                images=[img2],
                files=[doc2],
                context=[
                    ContextMessage(
                        role=ContextMessageRole.USER,
                        text="first",
                        images=[img1],
                        files=[doc1],
                    ),
                ],
                system_prompt="",
            ),
            image_mode="url",
            file_mode="url",
        )
        user = next(m for m in messages if m["role"] == "user")
        assert isinstance(user["content"], list)
        text_parts = [p for p in user["content"] if p["type"] == "text"]
        assert len(text_parts) == 1
        assert text_parts[0]["text"] == "first\n\nsecond"
        image_urls = {
            p["image_url"]["url"]
            for p in user["content"]
            if p["type"] == "image_url"
        }
        file_urls = {
            p["file"]["file_data"]
            for p in user["content"]
            if p["type"] == "file"
        }
        assert image_urls == {
            "https://cdn.example.com/a.png",
            "https://cdn.example.com/b.png",
        }
        assert file_urls == {
            "https://cdn.example.com/a.pdf",
            "https://cdn.example.com/b.pdf",
        }

    def test_assistant_text_only_uses_plain_string_content(self):
        """Providers reject multipart arrays for text-only assistant messages."""
        messages = build_openai_messages(
            LLMInput(
                text="",
                context=[
                    ContextMessage(role=ContextMessageRole.ASSISTANT, text="done"),
                ],
                system_prompt="",
            ),
        )
        assistant = next(m for m in messages if m["role"] == "assistant")
        assert assistant["content"] == "done"
        assert not isinstance(assistant["content"], list)

    def test_file_attachment_url_mode(self):
        doc = _file("https://cdn.example.com/report.pdf")
        messages = build_openai_messages(
            LLMInput(
                text="summarize",
                context=[
                    ContextMessage(
                        role=ContextMessageRole.USER,
                        text="see attached",
                        files=[doc],
                    ),
                ],
                system_prompt="",
            ),
            file_mode="url",
        )
        user = next(m for m in messages if m["role"] == "user")
        file_parts = [p for p in user["content"] if p["type"] == "file"]
        assert len(file_parts) == 1
        assert file_parts[0]["file"]["file_data"] == "https://cdn.example.com/report.pdf"
        assert file_parts[0]["file"]["filename"] == "file"

    def test_local_image_encodes_to_data_uri_in_base64_mode(self):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(b"\x89PNG\r\n\x1a\n")
            path = f.name
        try:
            image = File(path=path)
            messages = build_openai_messages(
                LLMInput(
                    text="describe",
                    context=[
                        ContextMessage(
                            role=ContextMessageRole.USER,
                            text="look",
                            images=[image],
                        ),
                    ],
                    system_prompt="",
                ),
                image_mode="base64",
            )
            user = next(m for m in messages if m["role"] == "user")
            image_parts = [p for p in user["content"] if p["type"] == "image_url"]
            assert len(image_parts) == 1
            assert image_parts[0]["image_url"]["url"].startswith("data:image/png;base64,")
        finally:
            os.unlink(path)

    def test_build_messages_is_alias_for_build_openai_messages(self):
        assert build_messages is build_openai_messages


class TestDataUriHelpers:
    def test_image_to_base64_data_uri_png(self):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(b"\x89PNG\r\n\x1a\n")
            path = f.name
        try:
            uri = image_to_base64_data_uri(path)
            assert uri.startswith("data:image/png;base64,")
        finally:
            os.unlink(path)

    def test_file_to_base64_data_uri_pdf(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"%PDF-1.4")
            path = f.name
        try:
            uri = file_to_base64_data_uri(path)
            assert uri.startswith("data:application/pdf;base64,")
        finally:
            os.unlink(path)


class TestBuildTools:
    def test_none_or_empty_returns_none(self):
        assert build_tools(None) is None
        assert build_tools([]) is None

    def test_wraps_bare_function_definition(self):
        tools = build_tools([{"name": "fn", "description": "d", "parameters": None}])
        assert tools == [
            {
                "type": "function",
                "function": {
                    "name": "fn",
                    "description": "d",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        ]

    def test_preserves_already_wrapped_tool(self):
        wrapped = {
            "type": "function",
            "function": {
                "name": "fn",
                "parameters": {"type": "object", "properties": {"x": {"type": "string"}}},
            },
        }
        assert build_tools([wrapped]) == [wrapped]

    def test_strips_null_property_values(self):
        tools = build_tools(
            [
                {
                    "name": "fn",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "keep": {"type": "string"},
                            "drop": None,
                        },
                    },
                }
            ]
        )
        props = tools[0]["function"]["parameters"]["properties"]
        assert props == {"keep": {"type": "string"}}

    def test_fills_missing_properties_dict(self):
        tools = build_tools(
            [{"name": "fn", "parameters": {"type": "object", "properties": None}}]
        )
        assert tools[0]["function"]["parameters"]["properties"] == {}


class TestModelSettingsAndSamplingParams:

    def test_model_settings_all_fields_optional(self):
        ms = ModelSettings()
        assert ms.temperature is None
        assert ms.top_k is None
        assert ms.stop is None

    def test_model_settings_accepts_sampling_params(self):
        ms = ModelSettings(
            temperature=0.5,
            top_p=0.9,
            top_k=40,
            max_tokens=512,
            stop=["END"],
            seed=42,
            reasoning_effort="high",
            reasoning_max_tokens=1024,
        )
        assert ms.temperature == 0.5
        assert ms.top_k == 40
        assert ms.reasoning_effort == "high"
        assert ms.reasoning_max_tokens == 1024

    def test_model_settings_rejects_out_of_range_temperature(self):
        with pytest.raises(ValidationError):
            ModelSettings(temperature=3.0)

    def test_unified_input_has_all_sampling_fields(self):
        props = LLMInput.model_json_schema()["properties"]
        for field in ["temperature", "top_p", "top_k", "min_p",
                      "frequency_penalty", "presence_penalty", "repetition_penalty",
                      "seed", "stop", "max_tokens",
                      "reasoning_effort", "reasoning_max_tokens",
                      "images", "tools"]:
            assert field in props, f"missing {field}"
        assert ChatInput is LLMInput
        assert BaseLLMInput is LLMInput

    def test_input_sampling_params_flat(self):
        inp = LLMInput(text="hi", temperature=0.5, top_k=40, min_p=0.1, seed=42)
        assert inp.temperature == 0.5
        assert inp.top_k == 40
        assert inp.min_p == 0.1
        assert inp.seed == 42

    def test_build_openai_messages_accepts_llm_input(self):
        messages = build_openai_messages(
            LLMInput(text="hi", context=[], system_prompt="Be brief."),
        )
        assert messages[0] == {"role": "system", "content": "Be brief."}
        assert messages[-1] == {"role": "user", "content": "hi"}


class TestImagePartDetectionRegression:
    """Guard against JavaScript-style list.any() in render_message (PR #17)."""

    def test_multipart_user_message_with_image_builds_without_error(self):
        """Would raise AttributeError if render_message used list.any()."""
        image = _file("https://cdn.example.com/x.png")
        messages = build_openai_messages(
            LLMInput(
                text="caption",
                context=[
                    ContextMessage(
                        role=ContextMessageRole.USER,
                        text="",
                        images=[image],
                    ),
                ],
                system_prompt="",
            ),
            image_mode="url",
        )
        user = next(m for m in messages if m["role"] == "user")
        assert isinstance(user["content"], list)
        assert any(p["type"] == "image_url" for p in user["content"])


class TestGeneratedTypeConsumption:
    """Verify sdk-py consumes types from the generated llm_contract module."""

    def test_llm_usage_shares_fields_with_generated_type(self):
        from inferencesh import llm_types_gen as llm_contract
        from inferencesh.models.llm import LLMUsage
        gen_keys = set(llm_contract.LLMUsage.__annotations__)
        model_keys = set(LLMUsage.model_fields)
        assert gen_keys.issubset(model_keys)

    def test_llm_usage_has_zero_value_defaults(self):
        from inferencesh.models.llm import LLMUsage
        u = LLMUsage()
        assert u.stop_reason == ""
        assert u.prompt_tokens == 0
        assert u.tokens_per_second == 0.0

    def test_context_message_role_is_generated_enum(self):
        from inferencesh import llm_types_gen as llm_contract
        from inferencesh.models.llm import ContextMessageRole
        assert ContextMessageRole is llm_contract.ChatMessageRole
        assert ContextMessageRole.USER.value == "user"

    def test_llm_output_covers_generated_contract_fields(self):
        from inferencesh import llm_types_gen as llm_contract
        from inferencesh.models.llm import LLMOutput, BaseLLMOutput
        gen_fields = set(llm_contract.LLMOutput.model_fields)
        assert gen_fields.issubset(set(BaseLLMOutput.model_fields))
        assert gen_fields.issubset(set(LLMOutput.model_fields))

    def test_llm_output_has_all_contract_fields(self):
        from inferencesh.models.llm import LLMOutput
        fields = set(LLMOutput.model_fields.keys())
        assert {"response", "reasoning", "tool_calls", "usage"} <= fields

    def test_llm_input_covers_generated_contract_fields(self):
        from inferencesh import llm_types_gen as llm_contract
        from inferencesh.models.llm import LLMInput
        gen_fields = set(llm_contract.LLMInput.model_fields.keys())
        hand_fields = set(LLMInput.model_fields.keys())
        missing = gen_fields - hand_fields
        assert not missing, f"LLMInput is missing fields from generated contract: {missing}"

    def test_context_message_covers_generated_contract_fields(self):
        from inferencesh import llm_types_gen as llm_contract
        from inferencesh.models.llm import ContextMessage
        gen_fields = set(llm_contract.LLMContextMessage.model_fields.keys())
        hand_fields = set(ContextMessage.model_fields.keys())
        missing = gen_fields - hand_fields
        assert not missing, f"ContextMessage is missing fields from generated contract: {missing}"

    def test_llm_output_construction(self):
        from inferencesh.models.llm import LLMOutput, LLMUsage
        o = LLMOutput(
            response="hello",
            reasoning="thought about it",
            tool_calls=[{"id": "1", "type": "function", "function": {"name": "test", "arguments": {}}}],
            usage=LLMUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        )
        assert o.response == "hello"
        assert o.reasoning == "thought about it"
        assert len(o.tool_calls) == 1
        assert o.usage.total_tokens == 15


class TestLLMWireContract:
    """Guard generated llm_types_gen Pydantic wire models (apitypes BaseModel migration)."""

    def test_generated_llm_types_are_pydantic_models(self):
        from pydantic import BaseModel
        from inferencesh import llm_types_gen as llm_contract

        for name in [
            "LLMOutput", "LLMInput", "LLMContextMessage", "ToolCall",
            "ToolCallFunction", "LLMUsage", "FileRef", "Tool", "ToolFunction",
            "ToolParameters", "ToolParameterProperty",
        ]:
            cls = getattr(llm_contract, name)
            assert issubclass(cls, BaseModel), f"{name} must be a Pydantic BaseModel"

    def test_llm_input_model_fields_cover_sampling_contract(self):
        from inferencesh import llm_types_gen as llm_contract

        fields = set(llm_contract.LLMInput.model_fields.keys())
        for field in [
            "model", "context_size", "temperature", "top_p", "top_k", "min_p",
            "frequency_penalty", "presence_penalty", "repetition_penalty",
            "seed", "stop", "max_tokens", "reasoning_effort", "reasoning_max_tokens",
            "system_prompt", "context", "role", "text", "reasoning",
            "attachments", "images", "files", "tools", "tool_call_id",
        ]:
            assert field in fields, f"missing {field} on LLMInput wire contract"

    def test_llm_context_message_model_fields(self):
        from inferencesh import llm_types_gen as llm_contract

        fields = set(llm_contract.LLMContextMessage.model_fields.keys())
        assert {"role", "text", "reasoning", "images", "files", "tools", "tool_calls", "tool_call_id"} <= fields

    def test_tool_call_nested_in_llm_output_after_model_rebuild(self):
        """model_rebuild() must resolve forward refs so tool_calls validate on LLMOutput."""
        from inferencesh import llm_types_gen as llm_contract

        call = llm_contract.ToolCall(
            id="call_1",
            type=llm_contract.ToolCallType.TOOL_TYPE_FUNCTION,
            function=llm_contract.ToolCallFunction(
                name="search",
                arguments={"q": "weather"},
            ),
        )
        output = llm_contract.LLMOutput(response="ok", tool_calls=[call])
        assert output.tool_calls[0].function.name == "search"

    def test_llm_output_json_round_trip(self):
        from inferencesh import llm_types_gen as llm_contract

        original = llm_contract.LLMOutput(
            response="hello",
            usage=llm_contract.LLMUsage(prompt_tokens=5, completion_tokens=3, total_tokens=8),
        )
        restored = llm_contract.LLMOutput.model_validate_json(original.model_dump_json())
        assert restored.response == "hello"
        assert restored.usage.total_tokens == 8

    def test_llm_input_requires_wire_required_fields(self):
        from inferencesh import llm_types_gen as llm_contract
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            llm_contract.LLMInput()


class TestDeprecatedMixins:
    """Deprecated mixins emit warnings but don't break grid apps."""

    def test_output_mixin_warns(self):
        import warnings
        from inferencesh.models.llm import ReasoningMixin, LLMOutput, BaseLLMOutput
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            type("TestOutput", (ReasoningMixin, LLMOutput, BaseLLMOutput), {})
            deprecation_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
            assert len(deprecation_warnings) >= 1
            assert "deprecated output mixin" in str(deprecation_warnings[0].message)

    def test_input_mixin_warns(self):
        import warnings
        from inferencesh.models.llm import ImageCapabilityMixin, LLMInput
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            type("TestInput", (LLMInput, ImageCapabilityMixin), {})
            deprecation_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
            assert len(deprecation_warnings) >= 1
            assert "deprecated input mixin" in str(deprecation_warnings[0].message)

    def test_mixin_subclass_still_has_all_fields(self):
        import warnings
        from inferencesh.models.llm import ReasoningMixin, ToolCallsMixin, LLMOutput, BaseLLMOutput
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            AppOutput = type("AppOutput", (ReasoningMixin, ToolCallsMixin, LLMOutput, BaseLLMOutput), {})
        fields = set(AppOutput.model_fields.keys())
        assert {"response", "reasoning", "tool_calls", "usage"} <= fields
