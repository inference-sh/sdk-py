"""OpenAI Chat Completions adapter for chat apps.

``OpenAIChatMixin`` adds an ``openai`` function to any chat app whose
``run`` takes an ``LLMInput`` subclass. It is a thin translation layer:

    ChatCompletionInput  ->  <app's AppInput>  ->  self.run()
    LLMDelta             ->  ChatCompletionChunk
    LLMOutput            ->  ChatCompletion

No provider logic lives here. Apps opt in with::

    class App(OpenAIChatMixin, BaseApp):
        ...

and declare ``openai`` under ``functions:`` in ``inf.yml``.
"""

from __future__ import annotations

import inspect
import sys
import time
import uuid
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncGenerator,
    Dict,
    List,
    Optional,
    Type,
    Union,
    get_type_hints,
)

from ..llm_types_gen import (
    ResponseFormat,
    ResponseFormatType,
    StreamDelta,
    ToolChoice,
    ToolChoiceMode,
)
from ..models.file import File
from ..models.output_meta import TextMeta
from ..models.llm import (
    BaseLLMOutput,
    ContextMessage,
    ContextMessageRole,
    LLMDelta,
    LLMInput,
    ReasoningEffortEnum,
)
from .types import (
    ChatCompletion,
    ChatCompletionChunk,
    ChatCompletionInput,
    ChatCompletionMessage,
    ChatMessage,
    Choice,
    ChoiceDelta,
    ChoiceDeltaFunctionCall,
    ChoiceDeltaToolCall,
    ChunkChoice,
    CompletionTokensDetails,
    CompletionUsage,
    FinishReason,
    FunctionCallByName,
    NamedToolChoice,
    ResponseFunctionCall,
    ResponseToolCall,
)


class UnsupportedParameterError(ValueError):
    """A request used a Chat Completions parameter this app cannot honour."""

    def __init__(self, param: str, detail: str = ""):
        self.param = param
        msg = f"unsupported parameter: {param}"
        if detail:
            msg += f" ({detail})"
        super().__init__(msg)


# ── Request → LLMInput ───────────────────────────────────────────────

_REASONING_EFFORT = {
    "none": ReasoningEffortEnum.NONE,
    "minimal": ReasoningEffortEnum.LOW,
    "low": ReasoningEffortEnum.LOW,
    "medium": ReasoningEffortEnum.MEDIUM,
    "high": ReasoningEffortEnum.HIGH,
    "xhigh": ReasoningEffortEnum.HIGH,
}

_ROLE = {
    "user": ContextMessageRole.USER,
    "assistant": ContextMessageRole.ASSISTANT,
    "tool": ContextMessageRole.TOOL,
}


def _reject_unsupported(req: ChatCompletionInput) -> None:
    if req.n not in (None, 1):
        raise UnsupportedParameterError("n", "only n=1 is supported")
    if req.logprobs:
        raise UnsupportedParameterError("logprobs")
    if req.top_logprobs is not None:
        raise UnsupportedParameterError("top_logprobs")
    if req.logit_bias:
        raise UnsupportedParameterError("logit_bias")
    if req.audio is not None:
        raise UnsupportedParameterError("audio")
    if req.modalities not in (None, ["text"]):
        raise UnsupportedParameterError("modalities", "only text is supported")
    if req.prediction is not None:
        raise UnsupportedParameterError("prediction")
    if req.web_search_options is not None:
        raise UnsupportedParameterError("web_search_options")
    if req.moderation is not None:
        raise UnsupportedParameterError("moderation")
    if req.functions is not None and req.tools is not None:
        raise UnsupportedParameterError("functions", "cannot be combined with tools")


def _tool_choice(req: ChatCompletionInput) -> Optional[ToolChoice]:
    """OpenAI tool_choice (string | named object) -> flat ToolChoice.

    The deprecated function_call carries the same meaning for the
    functions API and maps identically.
    """
    choice: Any = req.tool_choice if req.tool_choice is not None else req.function_call
    if choice is None:
        return None
    if isinstance(choice, str):
        return ToolChoice(mode=ToolChoiceMode(choice))
    if isinstance(choice, NamedToolChoice):
        return ToolChoice(mode=ToolChoiceMode.FUNCTION, name=choice.function.name)
    if isinstance(choice, FunctionCallByName):
        return ToolChoice(mode=ToolChoiceMode.FUNCTION, name=choice.name)
    raise UnsupportedParameterError("tool_choice", f"unrecognised value {choice!r}")


def _response_format(req: ChatCompletionInput) -> Optional[ResponseFormat]:
    """OpenAI response_format -> flat ResponseFormat (json_schema un-nested)."""
    rf = req.response_format
    if rf is None:
        return None
    if rf.type == "json_schema":
        if rf.json_schema is None:
            raise ValueError("response_format.json_schema is required for type json_schema")
        return ResponseFormat(
            type=ResponseFormatType.JSON_SCHEMA,
            name=rf.json_schema.name,
            json_schema=rf.json_schema.schema_,
            strict=rf.json_schema.strict,
        )
    return ResponseFormat(type=ResponseFormatType(rf.type))


def _tools(req: ChatCompletionInput) -> Optional[List[Dict[str, Any]]]:
    """tools, or the deprecated functions list lifted into tool shape."""
    if req.tools:
        return [t.model_dump(exclude_none=True) for t in req.tools]
    if req.functions:
        return [{"type": "function", "function": f} for f in req.functions]
    return None


def _render_content(msg: ChatMessage) -> tuple[str, List[File], List[File]]:
    """Return (text, images, files) from a message's content."""
    if msg.content is None:
        return "", [], []
    if isinstance(msg.content, str):
        return msg.content, [], []

    texts: List[str] = []
    images: List[File] = []
    files: List[File] = []
    for part in msg.content:
        if part.type == "text":
            texts.append(part.text)
        elif part.type == "image_url":
            images.append(File(uri=part.image_url.url))
        elif part.type == "file":
            if part.file.file_data:
                files.append(File(uri=part.file.file_data, filename=part.file.filename))
            elif part.file.file_id:
                raise UnsupportedParameterError("file.file_id", "pass file_data (URL or data URI)")
    return "\n".join(texts), images, files


def _tool_calls_to_context(msg: ChatMessage) -> Optional[List[Dict[str, Any]]]:
    if not msg.tool_calls:
        return None
    return [tc.model_dump() for tc in msg.tool_calls]


def _to_context_message(msg: ChatMessage) -> ContextMessage:
    text, images, files = _render_content(msg)
    return ContextMessage(
        role=_ROLE[msg.role],
        text=text,
        reasoning=msg.reasoning,
        images=images or None,
        files=files or None,
        tool_calls=_tool_calls_to_context(msg),
        tool_call_id=msg.tool_call_id,
    )


def to_llm_input(req: ChatCompletionInput, input_cls: Type[LLMInput] = LLMInput) -> LLMInput:
    """Translate a Chat Completions request into the app's input model.

    ``input_cls`` is the app's ``LLMInput`` subclass so app-level defaults
    (context_size, temperature bounds, ...) apply. Only parameters present
    in the request are set; everything else keeps the app default.
    """
    _reject_unsupported(req)
    if not req.messages:
        raise ValueError("messages must not be empty")

    system_parts: List[str] = []
    turns: List[ChatMessage] = []
    for msg in req.messages:
        if msg.role in ("system", "developer"):
            text, _, _ = _render_content(msg)
            if text:
                system_parts.append(text)
        else:
            turns.append(msg)
    if not turns:
        raise ValueError("messages must contain at least one non-system message")

    # LLMInput models the current turn as text/role/... and history as
    # context. build_openai_messages appends the current turn itself, so
    # the last message must not also be in context.
    *history, current = turns
    cur_text, cur_images, cur_files = _render_content(current)

    kwargs: Dict[str, Any] = {
        "context": [_to_context_message(m) for m in history],
        "text": cur_text,
        "role": _ROLE[current.role],
    }
    if system_parts:
        kwargs["system_prompt"] = "\n\n".join(system_parts)
    if cur_images:
        kwargs["images"] = cur_images
    if cur_files:
        kwargs["files"] = cur_files
    if current.reasoning:
        kwargs["reasoning"] = current.reasoning
    if current.tool_call_id:
        kwargs["tool_call_id"] = current.tool_call_id
    if current.tool_calls:
        # A trailing assistant message with tool_calls is a prefill; fold
        # it into context so the provider sees the calls.
        kwargs["context"].append(_to_context_message(current))
        kwargs["text"] = ""

    if req.model is not None:
        kwargs["model"] = req.model
    if req.temperature is not None:
        kwargs["temperature"] = req.temperature
    if req.top_p is not None:
        kwargs["top_p"] = req.top_p
    if req.frequency_penalty is not None:
        kwargs["frequency_penalty"] = req.frequency_penalty
    if req.presence_penalty is not None:
        kwargs["presence_penalty"] = req.presence_penalty
    if req.seed is not None:
        kwargs["seed"] = req.seed
    if req.stop is not None:
        kwargs["stop"] = [req.stop] if isinstance(req.stop, str) else list(req.stop)
    max_tokens = req.max_completion_tokens if req.max_completion_tokens is not None else req.max_tokens
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    if req.reasoning_effort is not None:
        kwargs["reasoning_effort"] = _REASONING_EFFORT[req.reasoning_effort]

    tools = _tools(req)
    tool_choice = _tool_choice(req)
    if tools and not (tool_choice and tool_choice.mode is ToolChoiceMode.NONE):
        kwargs["tools"] = tools
        if tool_choice is not None:
            kwargs["tool_choice"] = tool_choice
    response_format = _response_format(req)
    if response_format is not None:
        kwargs["response_format"] = response_format

    return input_cls(**kwargs)


# ── LLMDelta / LLMOutput → chunks / completion ───────────────────────

def _finish_reason(out: BaseLLMOutput) -> FinishReason:
    if out.tool_calls:
        return "tool_calls"
    stop = (out.usage.stop_reason if out.usage else "") or ""
    if stop in ("length", "max_tokens"):
        return "length"
    if stop == "content_filter":
        return "content_filter"
    return "stop"


def _usage(out: BaseLLMOutput) -> Optional[CompletionUsage]:
    if out.usage and (out.usage.prompt_tokens or out.usage.completion_tokens):
        u = out.usage
        details = CompletionTokensDetails(reasoning_tokens=u.reasoning_tokens) if u.reasoning_tokens else None
        return CompletionUsage(
            prompt_tokens=u.prompt_tokens,
            completion_tokens=u.completion_tokens,
            total_tokens=u.total_tokens or (u.prompt_tokens + u.completion_tokens),
            completion_tokens_details=details,
        )
    # Apps that report tokens for pricing via output_meta rather than usage.
    if out.output_meta is not None:
        prompt = sum(m.tokens for m in out.output_meta.inputs if isinstance(m, TextMeta))
        completion = sum(m.tokens for m in out.output_meta.outputs if isinstance(m, TextMeta))
        if prompt or completion:
            return CompletionUsage(
                prompt_tokens=prompt,
                completion_tokens=completion,
                total_tokens=prompt + completion,
            )
    return None


def _tool_calls(out: BaseLLMOutput) -> Optional[List[ResponseToolCall]]:
    if not out.tool_calls:
        return None
    return [ResponseToolCall.model_validate(tc) for tc in out.tool_calls]


class _ChunkStream:
    """Stateful LLMDelta → ChatCompletionChunk translator for one request."""

    def __init__(self, model: str):
        self.id = f"chatcmpl-{uuid.uuid4().hex}"
        self.created = int(time.time())
        self.model = model
        self._first = True

    def _chunk(self, delta: ChoiceDelta, finish_reason: Optional[FinishReason] = None) -> ChatCompletionChunk:
        if self._first:
            delta.role = "assistant"
            self._first = False
        return ChatCompletionChunk(
            id=self.id, created=self.created, model=self.model,
            choices=[ChunkChoice(index=0, delta=delta, finish_reason=finish_reason)],
        )

    def from_delta(self, delta: LLMDelta) -> Optional[ChatCompletionChunk]:
        fields = delta.model_fields_set
        cd = ChoiceDelta()
        if "response" in fields and delta.response:
            cd.content = delta.response
        if "reasoning" in fields and delta.reasoning:
            cd.reasoning = delta.reasoning
        if "tool_calls" in fields and delta.tool_calls:
            cd.tool_calls = [
                ChoiceDeltaToolCall(
                    index=tc.index,
                    id=tc.id,
                    type=tc.type,
                    function=ChoiceDeltaFunctionCall(
                        name=tc.function.name or None,
                        arguments=tc.function.arguments or None,
                    ) if tc.function else None,
                )
                for tc in delta.tool_calls
            ]
        if not cd.model_fields_set and not self._first:
            return None
        return self._chunk(cd)

    def from_text(self, content: str = "", reasoning: str = "") -> Optional[ChatCompletionChunk]:
        """Chunk from diffed progress text, for apps that do not yield deltas."""
        cd = ChoiceDelta()
        if content:
            cd.content = content
        if reasoning:
            cd.reasoning = reasoning
        if not cd.model_fields_set and not self._first:
            return None
        return self._chunk(cd)

    def finish(self, out: BaseLLMOutput, include_usage: bool) -> List[ChatCompletionChunk]:
        chunks = [self._chunk(ChoiceDelta(), finish_reason=_finish_reason(out))]
        if include_usage:
            chunks.append(ChatCompletionChunk(
                id=self.id, created=self.created, model=self.model,
                choices=[], usage=_usage(out),
            ))
        return chunks

    def completion(self, out: BaseLLMOutput) -> ChatCompletion:
        return ChatCompletion(
            id=self.id, created=self.created, model=self.model,
            choices=[Choice(
                index=0,
                message=ChatCompletionMessage(
                    content=out.response or None,
                    reasoning=out.reasoning or None,
                    tool_calls=_tool_calls(out),
                ),
                finish_reason=_finish_reason(out),
            )],
            usage=_usage(out),
            output_meta=out.output_meta,
        )


# ── Mixin ────────────────────────────────────────────────────────────

def _run_input_type(app: Any) -> Type[LLMInput]:
    hints = get_type_hints(app.run)
    for name in ("input_data", "input", "app_input"):
        if name in hints:
            return hints[name]
    params = [p for p in inspect.signature(app.run).parameters.values() if p.name not in ("self", "metadata")]
    if params and params[0].name in hints:
        return hints[params[0].name]
    raise TypeError("run() must type-hint its input parameter with an LLMInput subclass")


def _as_llm_output(out: Any) -> BaseLLMOutput:
    if not isinstance(out, BaseLLMOutput):
        raise TypeError(f"OpenAIChatMixin requires run() to yield LLMOutput, got {type(out).__name__}")
    return out


class _ProgressDiffer:
    """Turn cumulative progress outputs into (content, reasoning) increments."""

    def __init__(self) -> None:
        self._response = ""
        self._reasoning = ""

    @staticmethod
    def _increment(prev: str, cur: str) -> str:
        return cur[len(prev):] if cur.startswith(prev) else cur

    def step(self, out: BaseLLMOutput) -> tuple[str, str]:
        response, reasoning = out.response or "", out.reasoning or ""
        inc = (self._increment(self._response, response), self._increment(self._reasoning, reasoning))
        self._response, self._reasoning = response, reasoning
        return inc


def _default_model_name(app: Any) -> str:
    """The ``model`` reported in responses when the request sets none.

    Chat apps declare ``DEFAULT_MODEL`` at module level; reuse it rather
    than adding per-app configuration.
    """
    module = sys.modules.get(type(app).__module__)
    return str(getattr(module, "DEFAULT_MODEL", "") or "")


class OpenAIChatMixin:
    """Adds an OpenAI Chat Completions ``openai`` function to a chat app.

    Chunks are always yielded as ``StreamDelta`` events — they ride the
    delta channel and cost nothing for consumers that only read the final
    output. ``stream_options.include_usage`` adds the trailing usage
    chunk, as in the OpenAI API.

    Responses report ``model`` from the request, else the app module's
    ``DEFAULT_MODEL``.
    """

    if TYPE_CHECKING:
        # Contract with the host app: a chat ``run`` taking an LLMInput.
        # Declared for the type checker only; the real method comes from
        # the app class the mixin is combined with.
        def run(self, input_data: LLMInput, *args: Any, **kwargs: Any) -> Any: ...

    async def openai(self, input_data: ChatCompletionInput) -> AsyncGenerator[Union[ChatCompletionChunk, ChatCompletion], None]:
        """OpenAI Chat Completions compatible entry point."""
        llm_input = to_llm_input(input_data, _run_input_type(self))
        model = input_data.model or _default_model_name(self)
        include_usage = bool(input_data.stream_options and input_data.stream_options.include_usage)
        stream = _ChunkStream(model)

        run_kwargs: Dict[str, Any] = {"input_data": llm_input}
        if "metadata" in inspect.signature(self.run).parameters:
            # Legacy run(input_data, metadata) signature. BaseApp does not
            # declare ``context``; the engine attaches it at setup.
            context = getattr(self, "context", None)
            run_kwargs["metadata"] = context.metadata if context is not None else None
        result = self.run(**run_kwargs)

        final: Optional[BaseLLMOutput] = None
        saw_delta = False
        diff = _ProgressDiffer()

        if inspect.isasyncgen(result) or hasattr(result, "__aiter__"):
            async for out in result:
                if isinstance(out, StreamDelta):
                    saw_delta = True
                    chunk = stream.from_delta(out) if isinstance(out, LLMDelta) else None
                    if chunk is not None:
                        yield chunk
                    continue
                final = _as_llm_output(out)
                if saw_delta:
                    continue
                # No deltas from this app: derive chunks by diffing progress.
                chunk = stream.from_text(*diff.step(final))
                if chunk is not None:
                    yield chunk
        else:
            final = _as_llm_output(await result if inspect.iscoroutine(result) else result)
            chunk = stream.from_text(*diff.step(final))
            if chunk is not None:
                yield chunk

        if final is None:
            raise RuntimeError("run() produced no output")

        for chunk in stream.finish(final, include_usage):
            yield chunk
        yield stream.completion(final)
