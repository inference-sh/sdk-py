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
