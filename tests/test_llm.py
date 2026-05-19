"""Tests for LLM message/tool builders (build_openai_messages, build_tools)."""

from unittest.mock import patch

import pytest

from inferencesh import File
from inferencesh.models.llm import (
    ContextMessage,
    ContextMessageRole,
    LLMInput,
    build_openai_messages,
    build_tools,
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


class TestImagePartDetectionRegression:
    """Guard against JavaScript-style list.any() in render_message."""

    def test_builtin_any_detects_image_url_parts(self):
        parts = [
            {"type": "text", "text": "caption"},
            {"type": "image_url", "image_url": {"url": "https://example.com/x.png"}},
        ]
        assert any(p["type"] == "image_url" for p in parts)

    def test_lists_do_not_expose_any_method(self):
        parts = [{"type": "text", "text": "x"}]
        assert not hasattr(parts, "any")
