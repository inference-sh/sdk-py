from typing import Optional, List, Any, Callable, Dict, Generator, Union
from enum import Enum
from pydantic import Field, BaseModel
from queue import Queue, Empty
from threading import Thread
import time
from contextlib import contextmanager
import base64
import json

from .base import BaseAppInput, BaseAppOutput
from .file import File
from inferencesh.images import ImageLimits, fit_image

from inferencesh import llm_types_gen as llm_contract
from inferencesh.delta import OutputDiffer

ContextMessageRole = llm_contract.ChatMessageRole


LLMUsage = llm_contract.LLMUsage

class Message(BaseAppInput):
    role: ContextMessageRole
    content: str

class ContextMessage(llm_contract.LLMContextMessage, BaseAppInput):
    # App-layer File types instead of wire URL strings (wire uses List[str])
    images: Optional[List[File]] = None  # type: ignore[assignment]
    files: Optional[List[File]] = None  # type: ignore[assignment]
    # Dict access for backward compat with build_openai_messages (wire uses List[ToolCall])
    tool_calls: Optional[List[Dict[str, Any]]] = None  # type: ignore[assignment]

class ReasoningEffortEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    NONE = "none"


class ModelSettings(BaseModel):
    """Deprecated. Sampling settings live flat on LLMInput (which now
    inherits the generated LLMSettings); nothing sends a nested
    model_settings object. Kept only so existing imports do not break."""

    def __init__(self, **data: Any) -> None:
        import warnings
        warnings.warn(
            "ModelSettings is deprecated: sampling settings are flat fields on LLMInput",
            DeprecationWarning, stacklevel=2,
        )
        super().__init__(**data)

    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    top_k: Optional[int] = Field(default=None, ge=-1)
    min_p: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    frequency_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0)
    presence_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0)
    repetition_penalty: Optional[float] = Field(default=None, ge=0.0)
    seed: Optional[int] = Field(default=None)
    stop: Optional[List[str]] = Field(default=None)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    reasoning_effort: Optional[str] = Field(default=None)
    reasoning_max_tokens: Optional[int] = Field(default=None)


class LLMInput(llm_contract.LLMInput, BaseAppInput):
    """The generated contract with app-layer types (File objects, not wire
    strings/refs) and app defaults. Field order is the contract's: the turn
    first, the settings last. An override keeps its contract position, so
    this body's order is cosmetic; it mirrors the contract for readability."""

    text: str = Field(default="")
    # App-layer File objects replace the wire's List[str] (URL strings) and List[FileRef]
    images: Optional[List[File]] = Field(default=None)  # type: ignore[assignment]
    files: Optional[List[File]] = Field(default=None)  # type: ignore[assignment]
    attachments: Optional[List[File]] = Field(default=None)  # type: ignore[assignment]
    # ContextMessage is a subtype of LLMContextMessage; list is invariant so ignored
    context: List[ContextMessage] = Field(default=[])  # type: ignore[assignment]
    role: ContextMessageRole = Field(default=ContextMessageRole.USER)

    # App defaults and validation (Go has no annotations for these)
    system_prompt: str = Field(
        default="you are a helpful assistant that can answer questions and help with tasks.",
    )
    context_size: int = Field(default=4096)
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    top_p: float = Field(default=0.95, ge=0.0, le=1.0)
    max_tokens: int = Field(default=64000)
    reasoning_effort: ReasoningEffortEnum = Field(default=ReasoningEffortEnum.NONE)
    # Dict for backward compat with build_openai_messages/build_tools (wire uses List[Tool])
    tools: Optional[List[Dict[str, Any]]] = Field(default=None)  # type: ignore[assignment]

BaseLLMInput = LLMInput
ChatInput = LLMInput


# Deprecated no-op input mixins — all fields now on BaseLLMInput.
class _DeprecatedInputMixin(BaseModel):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.__name__ in _DEPRECATED_INPUT_MIXIN_NAMES:
            return
        import warnings
        warnings.warn(
            f"{cls.__name__} inherits from a deprecated input mixin. "
            "All input fields now live on BaseLLMInput. "
            "Remove the mixin from your class bases.",
            DeprecationWarning,
            stacklevel=2,
        )

_DEPRECATED_INPUT_MIXIN_NAMES = frozenset({
    "ImageCapabilityMixin", "FileCapabilityMixin", "ReasoningCapabilityMixin",
    "ToolsCapabilityMixin", "ModelSettingsCapabilityMixin",
})

class ImageCapabilityMixin(_DeprecatedInputMixin): pass
class FileCapabilityMixin(_DeprecatedInputMixin): pass
class ReasoningCapabilityMixin(_DeprecatedInputMixin): pass
class ToolsCapabilityMixin(_DeprecatedInputMixin): pass
class ModelSettingsCapabilityMixin(_DeprecatedInputMixin): pass

class BaseLLMOutput(llm_contract.LLMOutput, BaseAppOutput):
    # Dict for backward compat: apps build tool_calls as dicts and
    # build_openai_messages reads them dict-style (wire uses List[ToolCall])
    tool_calls: Optional[List[Dict[str, Any]]] = None  # type: ignore[assignment]

class LLMOutput(BaseLLMOutput): pass


# Streaming delta with append semantics. Yield during streaming, yield
# LLMOutput at the end for the final DB write.
LLMDelta = llm_contract.LLMDelta

_DEPRECATED_MIXIN_NAMES = frozenset({"LLMUsageMixin", "ReasoningMixin", "ToolCallsMixin", "ImagesMixin"})

class _DeprecatedOutputMixin(BaseModel):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.__name__ in _DEPRECATED_MIXIN_NAMES:
            return
        import warnings
        warnings.warn(
            f"{cls.__name__} inherits from a deprecated output mixin. "
            "Output fields now come from BaseLLMOutput. "
            "Remove the mixin from your class bases.",
            DeprecationWarning,
            stacklevel=2,
        )

class LLMUsageMixin(_DeprecatedOutputMixin): pass
class ReasoningMixin(_DeprecatedOutputMixin): pass
class ToolCallsMixin(_DeprecatedOutputMixin): pass
class ImagesMixin(_DeprecatedOutputMixin): pass

@contextmanager
def timing_context():
    """Context manager to track timing information for LLM generation."""
    class TimingInfo:
        def __init__(self):
            self.start_time = time.time()
            self.first_token_time = None
            self.reasoning_start_time = None
            self.total_reasoning_time = 0.0
            self.reasoning_tokens = 0
            self.in_reasoning = False

        def mark_first_token(self):
            if self.first_token_time is None:
                self.first_token_time = time.time()

        def start_reasoning(self):
            if not self.in_reasoning:
                self.reasoning_start_time = time.time()
                self.in_reasoning = True

        def end_reasoning(self, token_count: int = 0):
            if self.in_reasoning and self.reasoning_start_time:
                self.total_reasoning_time += time.time() - self.reasoning_start_time
                self.reasoning_tokens += token_count
                self.reasoning_start_time = None
                self.in_reasoning = False

        @property
        def stats(self):
            current_time = time.time()
            if self.first_token_time is None:
                return {
                    "time_to_first_token": 0.0,
                    "generation_time": 0.0,
                    "reasoning_time": self.total_reasoning_time,
                    "reasoning_tokens": self.reasoning_tokens
                }

            time_to_first = self.first_token_time - self.start_time
            generation_time = current_time - self.first_token_time

            return {
                "time_to_first_token": time_to_first,
                "generation_time": generation_time,
                "reasoning_time": self.total_reasoning_time,
                "reasoning_tokens": self.reasoning_tokens
            }

    timing = TimingInfo()
    try:
        yield timing
    finally:
        pass

def image_to_base64_data_uri(file_path):
    with open(file_path, "rb") as img_file:
        base64_data = base64.b64encode(img_file.read()).decode('utf-8')
        file_extension = file_path.split(".")[-1]
        content_type = "png"
        if file_extension == "png":
            content_type = "png"
        elif file_extension == "jpg":
            content_type = "jpeg"
        elif file_extension == "jpeg":
            content_type = "jpeg"
        elif file_extension == "gif":
            content_type = "gif"

        return f"data:image/{content_type};base64,{base64_data}"

def file_to_base64_data_uri(file_path):
    with open(file_path, "rb") as file:
        base64_data = base64.b64encode(file.read()).decode('utf-8')
        file_extension = file_path.split(".")[-1]
        content_type = "application/octet-stream"
        if file_extension == "pdf":
            content_type = "application/pdf"
        return f"data:{content_type};base64,{base64_data}"

def build_openai_messages(
    input_data: LLMInput,
    transform_user_message: Optional[Callable[[str], str]] = None,
    include_reasoning: bool = False,
    file_mode: str = "base64",
    image_mode: str = "base64",
    image_limits: Optional[ImageLimits] = None,
    tool_media_as_user_message: bool = False,
    reasoning_state_key: Optional[str] = None,
    reasoning_field: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Build OpenAI-format messages for chat completion.

    If any message includes image/file content, builds multipart format.
    Otherwise, uses plain string-only format.

    file_mode/image_mode: "base64" encodes from local path, "url" passes original URL when available.
    image_limits: what the provider takes; a base64 image is downsized to fit (see inferencesh.images).
    tool_media_as_user_message: a tool result's images and files go in a user
    message after the tool messages instead of in the tool message's content.
    The default sends them in the tool message: OpenRouter and Melious take
    image parts there and the model sees them. Set it for a backend that
    accepts only text in a role "tool" message.
    reasoning_state_key: the key this app writes its reasoning_details under
    in an output's reasoning_state (see merge_reasoning_details). An assistant
    message carrying an entry under it sends that entry back as its
    reasoning_details, as the provider issued them; entries under other keys
    are another provider's and are left out.
    reasoning_field: the field an assistant message sends its own reasoning
    text back in, for a provider that takes it as text: DeepSeek and the
    backends serving it take "reasoning_content". Used when the message has
    no reasoning_state entry under reasoning_state_key.
    include_reasoning: deprecated, the same as reasoning_field="reasoning".
    """
    if include_reasoning and reasoning_field is None:
        reasoning_field = "reasoning"

    def _is_http_url(s: str) -> bool:
        return s.startswith("http://") or s.startswith("https://")

    def render_message(msg: ContextMessage, allow_multipart: bool) -> str | List[dict]:
        parts: List[Dict[str, Any]] = []
        text = transform_user_message(msg.text) if transform_user_message and msg.role == ContextMessageRole.USER and msg.text is not None else msg.text


        if text:
            parts.append({"type": "text", "text": text})
        else:
            parts.append({"type": "text", "text": ""})

        if msg.images:
            for image in msg.images:
                if image_mode == "url" and image.uri and _is_http_url(image.uri):
                    parts.append({"type": "image_url", "image_url": {"url": image.uri}})
                elif image.path:
                    if image_limits is not None:
                        data, mime = fit_image(image.path, image_limits)
                        image_data_uri = f"data:{mime};base64,{base64.b64encode(data).decode()}"
                    else:
                        image_data_uri = image_to_base64_data_uri(image.path)
                    parts.append({"type": "image_url", "image_url": {"url": image_data_uri}})
                elif image.uri:
                    parts.append({"type": "image_url", "image_url": {"url": image.uri}})

        if msg.files:
            for file in msg.files:
                filename = file.filename or "file"
                if file_mode == "url" and file.uri and _is_http_url(file.uri):
                    parts.append({"type": "file", "file": {"filename": filename, "file_data": file.uri}})
                elif file.path:
                    file_data_uri = file_to_base64_data_uri(file.path)
                    parts.append({"type": "file", "file": {"filename": filename, "file_data": file_data_uri}})
                elif file.uri:
                    parts.append({"type": "file", "file": {"filename": filename, "file_data": file.uri}})

        if msg.reasoning:
            parts.append({"type": "reasoning", "reasoning": msg.reasoning})

        # If the message only has a single text part, return as plain string
        # even in multipart mode — avoids sending [{"type":"text","text":""}]
        # for assistant/tool messages which some providers reject
        if len(parts) == 1 and parts[0]["type"] == "text":
            return parts[0]["text"]

        if allow_multipart:
            return parts

        if len(parts) > 1:
            if any(x["type"] == "image_url" for x in parts):
                raise ValueError("Image content requires multipart support")
            return parts

        raise ValueError("Invalid message content")

    messages: List[Dict[str, Any]] = [{"role": "system", "content": input_data.system_prompt}] if input_data.system_prompt is not None and input_data.system_prompt != "" else []

    def merge_messages(messages: List[ContextMessage]) -> ContextMessage:
        text = "\n\n".join(msg.text for msg in messages if msg.text)
        images = []
        files = []
        for msg in messages:
            if msg.images:
                images.extend(msg.images)
            if msg.files:
                files.extend(msg.files)

        images_list = images if len(images) >= 1 else None
        files_list = files if len(files) >= 1 else None
        return ContextMessage(role=messages[0].role, text=text, images=images_list, files=files_list)

    def merge_tool_calls(messages: List[ContextMessage]) -> List[Dict[str, Any]]:
        tool_calls = []
        for msg in messages:
            if msg.tool_calls:
                tool_calls.extend(msg.tool_calls)
        return tool_calls

    user_input_text = ""
    if hasattr(input_data, "text"):
        user_input_text = transform_user_message(input_data.text) if transform_user_message else input_data.text

    user_input_images = None
    if hasattr(input_data, "images"):
        user_input_images = input_data.images

    user_input_files = None
    if hasattr(input_data, "files"):
        user_input_files = input_data.files

    user_input_reasoning = None
    if hasattr(input_data, "reasoning"):
        user_input_reasoning = input_data.reasoning

    # Check if ANY message (including current user input) has images/files/reasoning
    multipart: bool = bool(
        any(m.images or m.files or m.reasoning for m in input_data.context)
        or user_input_images or user_input_files or user_input_reasoning
    )

    input_role = input_data.role if hasattr(input_data, "role") else ContextMessageRole.USER
    input_tool_call_id = input_data.tool_call_id if hasattr(input_data, "tool_call_id") else None
    user_msg = ContextMessage(role=input_role, text=user_input_text, images=user_input_images, files=user_input_files, reasoning=user_input_reasoning, tool_call_id=input_tool_call_id)

    input_data.context.append(user_msg)

    # With tool_media_as_user_message, the images and files a tool returned
    # follow in a user message. These wait until the run of tool messages
    # ends, so every tool result still directly follows the assistant message
    # that called it (parallel tool calls).
    pending_tool_media: List[Dict[str, Any]] = []

    def flush_tool_media() -> None:
        messages.extend(pending_tool_media)
        pending_tool_media.clear()

    def emit_group(group: List[ContextMessage], role: Any) -> None:
        # Convert role enum to string for OpenAI API compatibility
        role_str = role.value if hasattr(role, "value") else role
        merged = merge_messages(group)
        tool_media: Optional[ContextMessage] = None
        if tool_media_as_user_message and role_str == "tool" and (merged.images or merged.files):
            tool_id = group[0].tool_call_id or "unknown"
            # Role TOOL keeps transform_user_message off the label; the
            # message is sent with role "user".
            tool_media = ContextMessage(
                role=ContextMessageRole.TOOL,
                text=f"Images and files returned by tool call {tool_id}:",
                images=merged.images,
                files=merged.files,
            )
            merged = ContextMessage(role=merged.role, text=merged.text)

        if role_str != "tool":
            flush_tool_media()

        msg_dict: Dict[str, Any] = {
            "role": role_str,
            "content": render_message(merged, allow_multipart=multipart),
        }

        # Only add tool_calls if not empty
        tool_calls = merge_tool_calls(group)
        if tool_calls:
            # Ensure arguments are JSON strings (OpenAI API requirement)
            for tc in tool_calls:
                if "function" in tc and "arguments" in tc["function"]:
                    if isinstance(tc["function"]["arguments"], dict):
                        tc["function"]["arguments"] = json.dumps(tc["function"]["arguments"])
            msg_dict["tool_calls"] = tool_calls
            # Assistant messages with tool_calls can have null content per OpenAI spec.
            # Some providers (MiniMax) reject empty string content with tool_calls.
            if msg_dict.get("content") == "":
                msg_dict["content"] = None

        # Add tool_call_id for tool role messages (required by OpenAI API)
        if role_str == "tool":
            if group and group[0].tool_call_id:
                msg_dict["tool_call_id"] = group[0].tool_call_id
            else:
                # If not provided, use empty string to satisfy schema
                msg_dict["tool_call_id"] = ""

        stored_details: List[Dict[str, Any]] = []
        if reasoning_state_key and role_str == "assistant":
            for m in group:
                entry = (m.reasoning_state or {}).get(reasoning_state_key)
                if isinstance(entry, list):
                    stored_details.extend(entry)

        if stored_details:
            msg_dict["reasoning_details"] = stored_details
        elif reasoning_field and role_str == "assistant":
            reasoning = "\n\n".join(m.reasoning for m in group if m.reasoning)
            if reasoning:
                msg_dict[reasoning_field] = reasoning

        messages.append(msg_dict)
        if tool_media is not None:
            pending_tool_media.append({
                "role": "user",
                "content": render_message(tool_media, allow_multipart=True),
            })

    def is_tool(role: Any) -> bool:
        return (role.value if hasattr(role, "value") else role) == "tool"

    current_role = None
    current_messages: List[ContextMessage] = []

    for msg in input_data.context:
        # Consecutive messages of one role merge, except tool messages: each
        # answers its own tool call and keeps its own tool_call_id.
        if current_role is None or (msg.role == current_role and not is_tool(msg.role)):
            current_messages.append(msg)
            current_role = msg.role
        else:
            emit_group(current_messages, current_role)
            current_messages = [msg]
            current_role = msg.role

    if len(current_messages) > 0:
        assert current_role is not None  # set whenever current_messages is non-empty
        emit_group(current_messages, current_role)

    flush_tool_media()

    return messages


# Backwards-compatible alias
build_messages = build_openai_messages


def merge_reasoning_details(details: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Fold streamed reasoning_details fragments into whole blocks.

    OpenAI-compatible APIs that return reasoning_details (OpenRouter, MiniMax
    with reasoning_split) stream each block as fragments sharing its index and
    type: text, summary or data in pieces, the signature or id on one of them.
    Consecutive fragments of one block become one, its strings concatenated
    and its other fields kept; the blocks stay in the order the model made
    them, which the provider checks when they are sent back.
    """
    merged: List[Dict[str, Any]] = []
    for d in details:
        if not isinstance(d, dict):
            continue
        prev = merged[-1] if merged else None
        if prev is not None and d.get("index") == prev.get("index") and d.get("type") == prev.get("type"):
            for k, v in d.items():
                if v is None:
                    continue
                if k in ("text", "summary", "data") and isinstance(v, str):
                    prev[k] = (prev.get(k) or "") + v
                else:
                    prev[k] = v
        else:
            merged.append(dict(d))
    return merged


def openai_tool_choice(choice: Optional[llm_contract.ToolChoice]) -> Any:
    """LLMInput.tool_choice -> OpenAI-spelled tool_choice (also OpenRouter,
    llama.cpp, MiniMax, and other OpenAI-compatible APIs)."""
    if choice is None:
        return "auto"
    if choice.mode == llm_contract.ToolChoiceMode.FUNCTION:
        return {"type": "function", "function": {"name": choice.name}}
    return choice.mode.value  # none | auto | required


def openai_response_format(fmt: Optional[llm_contract.ResponseFormat]) -> Optional[Dict[str, Any]]:
    """LLMInput.response_format -> OpenAI-spelled response_format. None for text."""
    if fmt is None or fmt.type == llm_contract.ResponseFormatType.TEXT:
        return None
    if fmt.type == llm_contract.ResponseFormatType.JSON_OBJECT:
        return {"type": "json_object"}
    spec: Dict[str, Any] = {"name": fmt.name or "response", "schema": fmt.json_schema}
    if fmt.strict is not None:
        spec["strict"] = fmt.strict
    return {"type": "json_schema", "json_schema": spec}


def llamacpp_response_format(fmt: Optional[llm_contract.ResponseFormat]) -> Optional[Dict[str, Any]]:
    """LLMInput.response_format -> llama-cpp-python response_format.

    llama.cpp compiles the schema to a grammar; its spelling is
    {"type": "json_object", "schema": {...}} for both json modes.
    """
    if fmt is None or fmt.type == llm_contract.ResponseFormatType.TEXT:
        return None
    if fmt.type == llm_contract.ResponseFormatType.JSON_OBJECT:
        return {"type": "json_object"}
    return {"type": "json_object", "schema": fmt.json_schema}


def build_tools(tools: Optional[List[Dict[str, Any]]]) -> Optional[List[Dict[str, Any]]]:
    """Build tools in OpenAI API format.

    Ensures tools are properly formatted:
    - Wrapped in {"type": "function", "function": {...}}
    - Parameters is never None (OpenAI API requirement)
    """
    if not tools:
        return None

    result = []
    for tool in tools:
        # Extract function definition
        if "type" in tool and "function" in tool:
            func_def = tool["function"].copy()
        else:
            func_def = tool.copy()

        # Ensure parameters is not None (OpenAI API requirement)
        if func_def.get("parameters") is None:
            func_def["parameters"] = {"type": "object", "properties": {}}
        # Also ensure properties within parameters is not None
        elif func_def["parameters"].get("properties") is None:
            func_def["parameters"]["properties"] = {}
        else:
            # Remove properties with null values (OpenAI API doesn't accept them)
            properties = func_def["parameters"].get("properties", {})
            if properties:
                func_def["parameters"]["properties"] = {
                    k: v for k, v in properties.items() if v is not None
                }

        # Wrap in OpenAI format
        result.append({"type": "function", "function": func_def})

    return result


class StreamResponse:
    """Holds a single chunk of streamed response."""
    def __init__(self):
        self.content = ""
        self.tool_calls = None  # Changed from [] to None
        self.finish_reason = None
        self.timing_stats = {
            "time_to_first_token": None,  # Changed from 0.0 to None
            "generation_time": 0.0,
            "reasoning_time": 0.0,
            "reasoning_tokens": 0,
            "tokens_per_second": 0.0
        }
        self.usage_stats = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "stop_reason": ""
        }

    def update_from_chunk(self, chunk: Dict[str, Any], timing: Any) -> None:
        """Update response state from a chunk."""
        # Update usage stats if present
        if "usage" in chunk:
            usage = chunk["usage"]
            if usage is not None:
                # Update usage stats preserving existing values if not provided
                self.usage_stats.update({
                    "prompt_tokens": usage.get("prompt_tokens", self.usage_stats["prompt_tokens"]),
                    "completion_tokens": usage.get("completion_tokens", self.usage_stats["completion_tokens"]),
                    "total_tokens": usage.get("total_tokens", self.usage_stats["total_tokens"])
                })

        # Get the delta from the chunk
        delta = chunk.get("choices", [{}])[0]

        # Extract content and tool calls from either message or delta
        if "message" in delta:
            message = delta["message"]
            self.content = message.get("content", "")
            if message.get("tool_calls"):
                self._update_tool_calls(message["tool_calls"])
            self.finish_reason = delta.get("finish_reason")
            if self.finish_reason:
                self.usage_stats["stop_reason"] = self.finish_reason
        elif "delta" in delta:
            delta_content = delta["delta"]
            self.content = delta_content.get("content", "")
            if delta_content.get("tool_calls"):
                self._update_tool_calls(delta_content["tool_calls"])
            self.finish_reason = delta.get("finish_reason")
            if self.finish_reason:
                self.usage_stats["stop_reason"] = self.finish_reason

        # Update timing stats
        timing_stats = timing.stats
        if self.timing_stats["time_to_first_token"] is None:
            self.timing_stats["time_to_first_token"] = timing_stats["time_to_first_token"]

        self.timing_stats.update({
            "generation_time": timing_stats["generation_time"],
            "reasoning_time": timing_stats["reasoning_time"],
            "reasoning_tokens": timing_stats["reasoning_tokens"]
        })

        # Calculate tokens per second only if we have valid completion tokens and generation time
        if self.usage_stats["completion_tokens"] > 0 and timing_stats["generation_time"] > 0:
            self.timing_stats["tokens_per_second"] = (
                self.usage_stats["completion_tokens"] / timing_stats["generation_time"]
            )


    def _update_tool_calls(self, new_tool_calls: List[Dict[str, Any]]) -> None:
        """Update tool calls, handling both full and partial updates."""
        if self.tool_calls is None:
            self.tool_calls = []

        for tool_delta in new_tool_calls:
            tool_id = tool_delta.get("id")
            if not tool_id:
                continue

            # Find or create tool call
            current_tool = next((t for t in self.tool_calls if t["id"] == tool_id), None)
            if not current_tool:
                current_tool = {
                    "id": tool_id,
                    "type": tool_delta.get("type", "function"),
                    "function": {"name": "", "arguments": ""}
                }
                self.tool_calls.append(current_tool)

            # Update tool call
            if "function" in tool_delta:
                func_delta = tool_delta["function"]
                if "name" in func_delta:
                    current_tool["function"]["name"] = func_delta["name"]
                if "arguments" in func_delta:
                    current_tool["function"]["arguments"] += func_delta["arguments"]

    def has_updates(self) -> bool:
        """Check if this response has any content, tool call, or usage updates."""
        has_content = bool(self.content)
        has_tool_calls = bool(self.tool_calls)
        has_usage = self.usage_stats["prompt_tokens"] > 0 or self.usage_stats["completion_tokens"] > 0
        has_finish = bool(self.finish_reason)

        return has_content or has_tool_calls or has_usage or has_finish

    def to_output(self, buffer: str, transformer: Any) -> tuple[BaseLLMOutput, str]:
        """Convert current state to LLMOutput."""
        # Create usage object if we have stats
        usage = None
        if any(self.usage_stats.values()):
            usage = LLMUsage(
                stop_reason=self.usage_stats["stop_reason"],
                time_to_first_token=self.timing_stats["time_to_first_token"] or 0.0,
                tokens_per_second=self.timing_stats["tokens_per_second"],
                prompt_tokens=self.usage_stats["prompt_tokens"],
                completion_tokens=self.usage_stats["completion_tokens"],
                total_tokens=self.usage_stats["total_tokens"],
                reasoning_time=self.timing_stats["reasoning_time"],
                reasoning_tokens=self.timing_stats["reasoning_tokens"]
            )

        buffer, output, _ = transformer(self.content, buffer, usage)

        # Add tool calls if present and supported
        if self.tool_calls and hasattr(output, 'tool_calls'):
            output.tool_calls = self.tool_calls

        return output, buffer

class ResponseState:
    """Holds the state of response transformation."""
    def __init__(self):
        self.buffer = ""
        self.response = ""
        self.reasoning = None
        self.function_calls = None  # For future function calling support
        self.tool_calls = None      # List to accumulate tool calls
        self.current_tool_call = None  # Track current tool call being built
        self.usage = None  # Add usage field
        self.state_changes = {
            "reasoning_started": False,
            "reasoning_ended": False,
            "function_call_started": False,
            "function_call_ended": False,
            "tool_call_started": False,
            "tool_call_ended": False
        }

class ResponseTransformer:
    """Base class for transforming model responses."""
    def __init__(self, output_cls: type[BaseLLMOutput] = LLMOutput):
        self.state = ResponseState()
        self.output_cls = output_cls
        self.timing = None  # Will be set by stream_generate

    def clean_text(self, text: str) -> str:
        """Clean common tokens from the text and apply model-specific cleaning.

        Args:
            text: Raw text to clean

        Returns:
            Cleaned text with common and model-specific tokens removed
        """
        if text is None:
            return ""

        # Common token cleaning across most models
        cleaned = (text.replace("<|im_end|>", "")
                      .replace("<|im_start|>", "")
                      .replace("<start_of_turn>", "")
                      .replace("<end_of_turn>", "")
                      .replace("<eos>", ""))
        return self.additional_cleaning(cleaned)

    def additional_cleaning(self, text: str) -> str:
        """Apply model-specific token cleaning.

        Args:
            text: Text that has had common tokens removed

        Returns:
            Text with model-specific tokens removed
        """
        return text

    def handle_reasoning(self, text: str) -> None:
        """Handle reasoning/thinking detection and extraction.

        Args:
            text: Cleaned text to process for reasoning
        """
        # Default implementation for <think> style reasoning
        # Check for tags in the complete buffer
        if "<think>" in self.state.buffer and not self.state.state_changes["reasoning_started"]:
            self.state.state_changes["reasoning_started"] = True
            if self.timing:
                self.timing.start_reasoning()

        # Extract content and handle end of reasoning
        parts = self.state.buffer.split("<think>", 1)
        if len(parts) > 1:
            reasoning_text = parts[1]
            end_parts = reasoning_text.split("</think>", 1)
            self.state.reasoning = end_parts[0].strip()
            self.state.response = end_parts[1].strip() if len(end_parts) > 1 else ""

            # Check for end tag in complete buffer
            if "</think>" in self.state.buffer and not self.state.state_changes["reasoning_ended"]:
                self.state.state_changes["reasoning_ended"] = True
                if self.timing:
                    # Estimate token count from character count (rough approximation)
                    token_count = len(self.state.reasoning) // 4
                    self.timing.end_reasoning(token_count)
        else:
            self.state.response = self.state.buffer

    def handle_function_calls(self, text: str) -> None:
        """Handle function call detection and extraction.

        Args:
            text: Cleaned text to process for function calls
        """
        # Default no-op implementation
        # Models can override this to implement function call handling
        pass

    def handle_tool_calls(self, text: str) -> None:
        """Handle tool call detection and extraction.

        Args:
            text: Cleaned text to process for tool calls
        """
        # Default no-op implementation
        # Models can override this to implement tool call handling
        pass

    def transform_chunk(self, chunk: str) -> None:
        """Transform a single chunk of model output.

        This method orchestrates the transformation process by:
        1. Cleaning the text
        2. Updating the buffer
        3. Processing various capabilities (reasoning, function calls, etc)

        Args:
            chunk: Raw text chunk from the model
        """
        cleaned = self.clean_text(chunk)
        self.state.buffer += cleaned

        # Process different capabilities
        self.handle_reasoning(cleaned)
        self.handle_function_calls(cleaned)
        self.handle_tool_calls(cleaned)

    def build_output(self) -> tuple[str, BaseLLMOutput, dict]:
        """Build the final output tuple.

        Returns:
            Tuple of (buffer, output_instance, state_changes)
        """
        # Build base output with required fields
        output_data = {
            "response": self.state.response.strip(),
        }

        # Add optional fields if they exist
        if self.state.usage is not None:
            output_data["usage"] = self.state.usage
        if self.state.reasoning:
            output_data["reasoning"] = self.state.reasoning.strip()
        if self.state.function_calls:
            output_data["function_calls"] = self.state.function_calls
        if self.state.tool_calls:
            output_data["tool_calls"] = self.state.tool_calls

        output = self.output_cls(**output_data)

        return (
            self.state.buffer,
            output,
            self.state.state_changes
        )

    def __call__(self, piece: str, buffer: str, usage: Optional[LLMUsage] = None) -> tuple[str, BaseLLMOutput, dict]:
        """Transform a piece of text and return the result.

        Args:
            piece: New piece of text to transform
            buffer: Existing buffer content
            usage: Optional usage statistics

        Returns:
            Tuple of (new_buffer, output, state_changes)
        """
        self.state.buffer = buffer
        if usage is not None:
            self.state.usage = usage
        self.transform_chunk(piece)
        return self.build_output()


def stream_generate(
    model: Any,
    messages: List[Dict[str, Any]],
    transformer: ResponseTransformer = ResponseTransformer(),
    tools: Optional[List[Dict[str, Any]]] = None,
    tool_choice: Optional[Union[llm_contract.ToolChoice, Dict[str, Any], str]] = None,
    temperature: float = 0.7,
    top_p: float = 0.95,
    stop: Optional[List[str]] = None,
    verbose: bool = False,
    output_cls: type[BaseLLMOutput] = LLMOutput,
    kwargs: Optional[Dict[str, Any]] = None,
    response_format: Optional[Union[llm_contract.ResponseFormat, Dict[str, Any]]] = None,
    with_deltas: bool = False,
) -> Generator[Any, None, None]:
    """Stream generate from a llama.cpp model with timing and usage tracking.

    tool_choice / response_format accept the LLMInput types (translated to
    llama.cpp's OpenAI-shaped spelling) or already-shaped dicts.

    with_deltas=False (default): yields cumulative output objects.
    with_deltas=True: yields (output, LLMDelta | None) tuples; the delta is
    derived after the transformer runs so <think> extraction is respected.
    """
    if isinstance(tool_choice, llm_contract.ToolChoice):
        tool_choice = openai_tool_choice(tool_choice)
    if isinstance(response_format, llm_contract.ResponseFormat):
        response_format = llamacpp_response_format(response_format)

    # Create queues for communication between threads
    response_queue: Queue[Any] = Queue()
    error_queue: Queue[Any] = Queue()
    keep_alive_queue: Queue[Any] = Queue()

    # Set the output class for the transformer
    transformer.output_cls = output_cls

    def _generate_worker():
        """Worker thread to run the model generation."""
        try:
            # Build completion kwargs
            completion_kwargs = {
                "messages": messages,
                "stream": True,
                "temperature": temperature,
                "top_p": top_p,
                "stop": stop,
            }
            if kwargs:
                completion_kwargs.update(kwargs)
            if tools is not None:
                completion_kwargs["tools"] = tools
            if tool_choice is not None:
                completion_kwargs["tool_choice"] = tool_choice
            if response_format is not None:
                completion_kwargs["response_format"] = response_format

            # Signal that we're starting
            keep_alive_queue.put(("init", time.time()))

            completion = model.create_chat_completion(**completion_kwargs)

            for chunk in completion:
                response_queue.put(("chunk", chunk))
                # Update keep-alive timestamp
                keep_alive_queue.put(("alive", time.time()))

            # Signal completion
            response_queue.put(("done", None))

        except Exception as e:
            # Preserve the full exception with traceback
            import sys
            error_queue.put((e, sys.exc_info()[2]))
            response_queue.put(("error", str(e)))

    with timing_context() as timing:
        transformer.timing = timing

        # Start generation thread
        generation_thread = Thread(target=_generate_worker, daemon=True)
        generation_thread.start()

        # Initialize response state
        response = StreamResponse()
        buffer = ""
        differ = OutputDiffer() if with_deltas else None

        # Keep-alive tracking
        last_activity = time.time()
        init_timeout = 30.0  # 30 seconds for initial response
        chunk_timeout = 10.0  # 10 seconds between chunks
        chunks_begun = False

        try:
            # Wait for initial setup
            try:
                msg_type, timestamp = keep_alive_queue.get(timeout=init_timeout)
                if msg_type != "init":
                    raise RuntimeError("Unexpected initialization message")
                last_activity = timestamp
            except Empty:
                raise RuntimeError(f"Model failed to initialize within {init_timeout} seconds")

            while True:
                # Check for errors - now with proper exception chaining
                if not error_queue.empty():
                    exc, tb = error_queue.get()
                    if isinstance(exc, Exception):
                        raise exc.with_traceback(tb)
                    else:
                        raise RuntimeError(f"Unknown error in worker thread: {exc}")

                # Check keep-alive
                try:
                    while not keep_alive_queue.empty():
                        _, timestamp = keep_alive_queue.get_nowait()
                        last_activity = timestamp
                except Empty:
                    # Ignore empty queue - this is expected
                    pass

                # Check for timeout
                if chunks_begun and time.time() - last_activity > chunk_timeout:
                    raise RuntimeError(f"No response from model for {chunk_timeout} seconds")

                # Get next chunk
                try:
                    msg_type, data = response_queue.get(timeout=0.1)
                except Empty:
                    continue

                if msg_type == "error":
                    # If we get an error message but no exception in error_queue,
                    # create a new error
                    raise RuntimeError(f"Generation error: {data}")
                elif msg_type == "done":
                    break

                chunk = data

                if verbose:
                    print(chunk)

                # Mark first token time
                if not timing.first_token_time:
                    timing.mark_first_token()

                chunks_begun = True

                # Update response state from chunk
                response.update_from_chunk(chunk, timing)

                # Yield output if we have updates
                if response.has_updates():
                    output, buffer = response.to_output(buffer, transformer)
                    yield (output, differ.step(output)) if differ is not None else output

                # Break if we're done
                if response.finish_reason:
                    break

            # Wait for generation thread to finish
            if generation_thread.is_alive():
                generation_thread.join(timeout=5.0)  # Increased timeout to 5 seconds
                if generation_thread.is_alive():
                    # Thread didn't finish - this shouldn't happen normally
                    raise RuntimeError("Generation thread failed to finish")

        except Exception as e:
            # Check if there's a thread error we should chain with
            if not error_queue.empty():
                thread_exc, thread_tb = error_queue.get()
                if isinstance(thread_exc, Exception):
                    raise e from thread_exc
            # If no thread error, raise the original exception
            raise
