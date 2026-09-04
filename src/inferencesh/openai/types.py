"""OpenAI Chat Completions wire types.

Field names and shapes follow the OpenAI API (openai-python 2.x is the
reference). Only the subset that maps onto ``LLMInput``/``LLMOutput`` is
modelled; see ``adapter.py`` for what is honoured, ignored, or rejected.

``ChatCompletionChunk`` is a ``StreamDelta`` with ``_field_tags`` so the
generic accumulators merge a chunk stream back into a completion without
knowing anything OpenAI-specific.
"""

from __future__ import annotations

from typing import Any, ClassVar, Dict, List, Literal, Optional, Union

import json

from pydantic import BaseModel, Field, field_validator

from ..llm_types_gen import StreamDelta
from ..models.base import BaseAppInput, BaseAppOutput


# ── Request ──────────────────────────────────────────────────────────

class TextContentPart(BaseModel):
    type: Literal["text"]
    text: str


class ImageURL(BaseModel):
    url: str
    detail: Optional[Literal["auto", "low", "high"]] = None


class ImageContentPart(BaseModel):
    type: Literal["image_url"]
    image_url: ImageURL


class FileData(BaseModel):
    file_data: Optional[str] = None
    file_id: Optional[str] = None
    filename: Optional[str] = None


class FileContentPart(BaseModel):
    type: Literal["file"]
    file: FileData


ContentPart = Union[TextContentPart, ImageContentPart, FileContentPart]


class RequestFunctionCall(BaseModel):
    name: str
    arguments: str


class RequestToolCall(BaseModel):
    id: str
    type: Literal["function"] = "function"
    function: RequestFunctionCall


class ChatMessage(BaseModel):
    role: Literal["system", "developer", "user", "assistant", "tool"]
    content: Optional[Union[str, List[ContentPart]]] = None
    name: Optional[str] = None
    tool_calls: Optional[List[RequestToolCall]] = None
    tool_call_id: Optional[str] = None
    # OpenRouter / DeepSeek extension; OpenAI proper does not define it.
    reasoning: Optional[str] = None


class FunctionDefinition(BaseModel):
    name: str
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    strict: Optional[bool] = None


class ToolDefinition(BaseModel):
    type: Literal["function"] = "function"
    function: FunctionDefinition


class NamedToolChoiceFunction(BaseModel):
    name: str


class NamedToolChoice(BaseModel):
    type: Literal["function"] = "function"
    function: NamedToolChoiceFunction


ToolChoice = Union[Literal["none", "auto", "required"], NamedToolChoice]


class StreamOptions(BaseModel):
    include_usage: Optional[bool] = None


class ResponseFormat(BaseModel):
    type: Literal["text", "json_object", "json_schema"]
    json_schema: Optional[Dict[str, Any]] = None


class ChatCompletionInput(BaseAppInput):
    """``POST /v1/chat/completions`` request body."""

    model_config = {"extra": "allow"}

    messages: List[ChatMessage]
    model: Optional[str] = None

    # Sampling / generation — mapped onto LLMInput.
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    seed: Optional[int] = None
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = None
    max_completion_tokens: Optional[int] = None
    reasoning_effort: Optional[Literal["none", "minimal", "low", "medium", "high", "xhigh"]] = None

    tools: Optional[List[ToolDefinition]] = None
    tool_choice: Optional[ToolChoice] = None

    stream: Optional[bool] = None
    stream_options: Optional[StreamOptions] = None

    # Accepted for spec compatibility; no effect on generation.
    user: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None
    store: Optional[bool] = None
    service_tier: Optional[str] = None
    parallel_tool_calls: Optional[bool] = None
    prompt_cache_key: Optional[str] = None
    prompt_cache_retention: Optional[str] = None
    safety_identifier: Optional[str] = None
    verbosity: Optional[str] = None

    # Declared so validation surfaces a clear error instead of silently
    # dropping them. The adapter rejects any non-default value.
    n: Optional[int] = None
    logprobs: Optional[bool] = None
    top_logprobs: Optional[int] = None
    logit_bias: Optional[Dict[str, float]] = None
    response_format: Optional[ResponseFormat] = None
    audio: Optional[Dict[str, Any]] = None
    modalities: Optional[List[str]] = None
    prediction: Optional[Dict[str, Any]] = None
    web_search_options: Optional[Dict[str, Any]] = None
    functions: Optional[List[Dict[str, Any]]] = None
    function_call: Optional[Any] = None


# ── Response (shared) ────────────────────────────────────────────────

class CompletionTokensDetails(BaseModel):
    reasoning_tokens: Optional[int] = None


class PromptTokensDetails(BaseModel):
    cached_tokens: Optional[int] = None


class CompletionUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    completion_tokens_details: Optional[CompletionTokensDetails] = None
    prompt_tokens_details: Optional[PromptTokensDetails] = None


FinishReason = Literal["stop", "length", "tool_calls", "content_filter"]


# ── Streaming chunk ──────────────────────────────────────────────────

class ChoiceDeltaFunctionCall(BaseModel):
    name: Optional[str] = None
    arguments: Optional[str] = None

    _field_tags: ClassVar[dict] = {
        "name": {"merge": "replace"},
        "arguments": {"merge": "concat"},
    }


class ChoiceDeltaToolCall(BaseModel):
    index: int
    id: Optional[str] = None
    type: Optional[Literal["function"]] = None
    function: Optional[ChoiceDeltaFunctionCall] = None

    _field_tags: ClassVar[dict] = {
        "id": {"merge": "replace"},
        "type": {"merge": "replace"},
        "function": {"merge": "nested"},
    }


class ChoiceDelta(BaseModel):
    role: Optional[Literal["assistant"]] = None
    content: Optional[str] = None
    reasoning: Optional[str] = None
    refusal: Optional[str] = None
    tool_calls: Optional[List[ChoiceDeltaToolCall]] = None

    _field_tags: ClassVar[dict] = {
        "role": {"merge": "replace"},
        "content": {"merge": "concat"},
        "reasoning": {"merge": "concat"},
        "refusal": {"merge": "concat"},
        "tool_calls": {"merge": "indexed"},
    }


class ChunkChoice(BaseModel):
    index: int = 0
    delta: ChoiceDelta
    finish_reason: Optional[FinishReason] = None

    _field_tags: ClassVar[dict] = {
        "delta": {"merge": "nested"},
        "finish_reason": {"merge": "replace"},
    }


class ChatCompletionChunk(StreamDelta):
    """One SSE frame of ``stream: true``."""

    id: str
    object: Literal["chat.completion.chunk"] = "chat.completion.chunk"
    created: int
    model: str
    choices: List[ChunkChoice] = Field(default_factory=list)
    usage: Optional[CompletionUsage] = None
    system_fingerprint: Optional[str] = None

    _field_tags: ClassVar[dict] = {
        "id": {"merge": "replace"},
        "object": {"merge": "replace"},
        "created": {"merge": "replace"},
        "model": {"merge": "replace"},
        "choices": {"merge": "indexed"},
        "usage": {"merge": "replace"},
        "system_fingerprint": {"merge": "replace"},
    }


# ── Final completion ─────────────────────────────────────────────────

class ResponseFunctionCall(BaseModel):
    name: str
    arguments: str

    @field_validator("arguments", mode="before")
    @classmethod
    def _encode_arguments(cls, v: Any) -> str:
        """The wire format is a JSON string; app outputs carry a decoded map."""
        if v is None:
            return ""
        return v if isinstance(v, str) else json.dumps(v)


class ResponseToolCall(BaseModel):
    id: str
    type: Literal["function"] = "function"
    function: ResponseFunctionCall


class ChatCompletionMessage(BaseModel):
    role: Literal["assistant"] = "assistant"
    content: Optional[str] = None
    reasoning: Optional[str] = None
    refusal: Optional[str] = None
    tool_calls: Optional[List[ResponseToolCall]] = None


class Choice(BaseModel):
    index: int = 0
    message: ChatCompletionMessage
    finish_reason: FinishReason = "stop"


class ChatCompletion(BaseAppOutput):
    """``POST /v1/chat/completions`` response body."""

    id: str
    object: Literal["chat.completion"] = "chat.completion"
    created: int
    model: str
    choices: List[Choice]
    usage: Optional[CompletionUsage] = None
    system_fingerprint: Optional[str] = None
