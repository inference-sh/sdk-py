"""reasoning_state replay in build_openai_messages and merge_reasoning_details (INF-1066)."""

from inferencesh.models.llm import (
    ContextMessage,
    ContextMessageRole,
    LLMInput,
    build_openai_messages,
    merge_reasoning_details,
)

CALL = {"id": "call_1", "type": "function", "function": {"name": "get_weather", "arguments": '{"city":"Paris"}'}}
MINE = [{"type": "reasoning.text", "text": "think", "signature": "sig", "format": "anthropic-claude-v1", "index": 0}]
FOREIGN = {"gemini": {"signatures": ["c2ln"]}}


def _input(*assistants: ContextMessage) -> LLMInput:
    return LLMInput(
        role=ContextMessageRole.TOOL,
        tool_call_id="call_1",
        text='{"temp_c": 17}',
        context=[ContextMessage(role=ContextMessageRole.USER, text="weather?"), *assistants],
        system_prompt="",
    )


def _assistant(messages):
    return next(m for m in messages if m["role"] == "assistant")


def test_own_entry_goes_back_as_reasoning_details():
    msg = ContextMessage(role=ContextMessageRole.ASSISTANT, text="", tool_calls=[CALL],
                         reasoning_state={"openrouter": MINE, **FOREIGN})
    messages = build_openai_messages(_input(msg), reasoning_state_key="openrouter")
    assert _assistant(messages)["reasoning_details"] == MINE


def test_other_keys_are_left_out():
    msg = ContextMessage(role=ContextMessageRole.ASSISTANT, text="", tool_calls=[CALL], reasoning_state=FOREIGN)
    messages = build_openai_messages(_input(msg), reasoning_state_key="openrouter")
    assert "reasoning_details" not in _assistant(messages)


def test_no_key_sends_nothing():
    msg = ContextMessage(role=ContextMessageRole.ASSISTANT, text="", tool_calls=[CALL], reasoning_state={"openrouter": MINE})
    messages = build_openai_messages(_input(msg))
    assert "reasoning_details" not in _assistant(messages)


def test_stored_details_win_over_reasoning_text():
    msg = ContextMessage(role=ContextMessageRole.ASSISTANT, text="", tool_calls=[CALL], reasoning="think",
                         reasoning_state={"openrouter": MINE})
    user = ContextMessage(role=ContextMessageRole.USER, text="next", reasoning="think")
    messages = build_openai_messages(_input(msg, user), include_reasoning=True, reasoning_state_key="openrouter")
    assert _assistant(messages)["reasoning_details"] == MINE


def test_merge_folds_streamed_fragments_in_order():
    streamed = [
        {"type": "reasoning.summary", "summary": "**Calling", "format": "openai-responses-v1", "index": 0},
        {"type": "reasoning.summary", "summary": " the tool**", "format": "openai-responses-v1", "index": 0},
        {"type": "reasoning.encrypted", "data": "abc", "id": "rs_1", "format": "openai-responses-v1", "index": 1},
        {"type": "reasoning.text", "text": "The user", "format": "anthropic-claude-v1", "index": 2},
        {"type": "reasoning.text", "text": " wants", "format": "anthropic-claude-v1", "index": 2},
        {"type": "reasoning.text", "signature": "sig", "format": "anthropic-claude-v1", "index": 2},
    ]
    assert merge_reasoning_details(streamed) == [
        {"type": "reasoning.summary", "summary": "**Calling the tool**", "format": "openai-responses-v1", "index": 0},
        {"type": "reasoning.encrypted", "data": "abc", "id": "rs_1", "format": "openai-responses-v1", "index": 1},
        {"type": "reasoning.text", "text": "The user wants", "signature": "sig", "format": "anthropic-claude-v1", "index": 2},
    ]


def test_merge_keeps_whole_blocks_as_they_are():
    whole = [{"type": "reasoning.encrypted", "data": "x", "id": "call_1", "format": "google-gemini-v1", "index": 0}]
    assert merge_reasoning_details(whole) == whole


def _assistants(messages):
    return [m for m in messages if m["role"] == "assistant"]


def test_reasoning_field_sends_each_assistant_its_own_reasoning():
    first = ContextMessage(role=ContextMessageRole.ASSISTANT, text="", tool_calls=[CALL], reasoning="first")
    tool = ContextMessage(role=ContextMessageRole.TOOL, text="17", tool_call_id="call_1")
    second = ContextMessage(role=ContextMessageRole.ASSISTANT, text="", tool_calls=[CALL], reasoning="second")
    user = ContextMessage(role=ContextMessageRole.USER, text="and now?", reasoning="not an assistant's")
    messages = build_openai_messages(_input(first, tool, second, user), reasoning_field="reasoning_content")

    assert [m.get("reasoning_content") for m in _assistants(messages)] == ["first", "second"]
    assert all("reasoning_content" not in m for m in messages if m["role"] != "assistant")


def test_reasoning_field_leaves_out_an_assistant_without_reasoning():
    msg = ContextMessage(role=ContextMessageRole.ASSISTANT, text="", tool_calls=[CALL])
    messages = build_openai_messages(_input(msg), reasoning_field="reasoning_content")
    assert "reasoning_content" not in _assistant(messages)


def test_without_reasoning_field_no_reasoning_text_is_sent():
    msg = ContextMessage(role=ContextMessageRole.ASSISTANT, text="", tool_calls=[CALL], reasoning="think")
    messages = build_openai_messages(_input(msg))
    assert set(_assistant(messages)) == {"role", "content", "tool_calls"}


def test_include_reasoning_is_reasoning_field_reasoning():
    msg = ContextMessage(role=ContextMessageRole.ASSISTANT, text="", tool_calls=[CALL], reasoning="think")
    messages = build_openai_messages(_input(msg), include_reasoning=True)
    assert _assistant(messages)["reasoning"] == "think"
    assert "reasoning_details" not in _assistant(messages)


def test_reasoning_state_list_beats_reasoning_field():
    msg = ContextMessage(
        role=ContextMessageRole.ASSISTANT,
        text="",
        tool_calls=[CALL],
        reasoning="plain text",
        reasoning_state={"openrouter": MINE},
    )
    messages = build_openai_messages(
        _input(msg),
        reasoning_state_key="openrouter",
        reasoning_field="reasoning_content",
    )
    assistant = _assistant(messages)
    assert assistant["reasoning_details"] == MINE
    assert "reasoning_content" not in assistant


def test_non_list_reasoning_state_falls_back_to_reasoning_field():
    msg = ContextMessage(
        role=ContextMessageRole.ASSISTANT,
        text="",
        tool_calls=[CALL],
        reasoning="deepseek step",
        reasoning_state={"openrouter": {"type": "reasoning.encrypted", "data": "x"}},
    )
    messages = build_openai_messages(
        _input(msg),
        reasoning_state_key="openrouter",
        reasoning_field="reasoning_content",
    )
    assistant = _assistant(messages)
    assert "reasoning_details" not in assistant
    assert assistant["reasoning_content"] == "deepseek step"


def test_merged_assistants_join_reasoning_for_reasoning_field():
    a1 = ContextMessage(role=ContextMessageRole.ASSISTANT, text="part-a", reasoning="think-a")
    a2 = ContextMessage(role=ContextMessageRole.ASSISTANT, text="part-b", reasoning="think-b")
    inp = LLMInput(
        role=ContextMessageRole.TOOL,
        tool_call_id="call_1",
        text='{"temp_c": 17}',
        context=[ContextMessage(role=ContextMessageRole.USER, text="weather?"), a1, a2],
        system_prompt="",
    )
    messages = build_openai_messages(inp, reasoning_field="reasoning_content")
    assistant = _assistant(messages)
    assert assistant["reasoning_content"] == "think-a\n\nthink-b"
    assert assistant["content"] == "part-a\n\npart-b"
