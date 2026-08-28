"""inference.sh Python SDK package."""

from importlib.metadata import version as _pkg_version
__version__ = _pkg_version("inferencesh")

from .models import (
    BaseApp,
    BaseAppInput,
    BaseAppOutput,
    BaseAppSetup,
    File,
    Metadata,
    # LLM types
    ContextMessageRole,
    Message,
    ContextMessage,
    LLMInput,
    LLMOutput,
    build_messages,
    stream_generate,
    timing_context,
    # OutputMeta types
    MetaItem,
    MetaItemType,
    TextMeta,
    ImageMeta,
    VideoMeta,
    VideoResolution,
    AudioMeta,
    RawMeta,
    OutputMeta,
    probe_video,
)

from .delta import DeltaAccumulator
from .utils import StorageDir, download
from .client import (
    Inference, AsyncInference, UploadFileOptions,
    parse_status, is_terminal_status, is_message_ready,
)
from .streamable import streamable, streamable_raw, iter_ndjson, stream_post, stream_get, StreamableMessage
from .api import (
    TasksAPI,
    AsyncTasksAPI,
    FilesAPI,
    AsyncFilesAPI,
    AgentsAPI,
    AsyncAgentsAPI,
    SessionsAPI,
    AsyncSessionsAPI,
    SessionHandle,
    AsyncSessionHandle,
)
from .types import TaskStatus, ChatMessageStatus
from .models.errors import (
    APIError,
    RequirementsNotMetError,
    RequirementError,
    SetupAction,
    SessionError,
    SessionNotFoundError,
    SessionExpiredError,
    SessionEndedError,
    WorkerLostError,
)

# Agent SDK (headless)
from .agent import Agent, AsyncAgent, ToolCallInfo

# Tool Builder (fluent API)
from .tools import (
    tool,
    app_tool,
    agent_tool,
    webhook_tool,
    http_tool,
    call_tool,
    mcp_tool,
    internal_tools,
    lifecycle_hook,
    LifecycleHookBuilder,
    string,
    number,
    integer,
    boolean,
    enum_of,
    array,
    obj,
    optional,
    ClientTool,
    ClientToolHandler,
)

# Generated types for Agent/Chat functionality
from .types import (
    # Enums
    ChatStatus,
    ChatMessageRole,
    ChatMessageContentType,
    ToolType,
    ToolInvocationStatus,
    # Agent types
    AgentTool,
    AgentToolDTO,
    AgentConfigInput as AgentConfig,
    InternalToolsConfig,
    # Chat types
    ChatDTO,
    ChatMessageDTO,
    ChatData,
    ChatMessageContent,
    LLMInput,
    LLMContextMessage,
    # Tool types
    ToolCall,
    ToolCallFunction,
    ToolInvocationDTO,
    ToolResultRequest,
    Tool,
    ToolFunction,
    ToolParameters,
    # Hook types
    LifecycleHookConfig,
    LifecycleHookPayload,
    LifecycleHookResponse,
    ContextInjection,
    HookEvent,
    HookHandlerType,
    HookDecision,
    ToolCallEventData,
    ToolResultEventData,
    ErrorEventData,
)


def inference(*, api_key: str, base_url: str | None = None) -> Inference:
    """Factory function for creating an Inference client (lowercase for branding).

    Example:
        ```python
        client = inference(api_key="your-api-key")
        ```
    """
    return Inference(api_key=api_key, base_url=base_url)


def async_inference(*, api_key: str, base_url: str | None = None) -> AsyncInference:
    """Factory function for creating an AsyncInference client (lowercase for branding).

    Example:
        ```python
        client = async_inference(api_key="your-api-key")
        ```
    """
    return AsyncInference(api_key=api_key, base_url=base_url)


__all__ = [
    # Base types
    "BaseApp",
    "BaseAppInput",
    "BaseAppOutput",
    "BaseAppSetup",
    "File",
    "Metadata",
    # LLM types
    "ContextMessageRole",
    "Message",
    "ContextMessage",
    "LLMInput",
    "LLMOutput",
    "build_messages",
    "stream_generate",
    "timing_context",
    # OutputMeta types
    "MetaItem",
    "MetaItemType",
    "TextMeta",
    "ImageMeta",
    "VideoMeta",
    "VideoResolution",
    "AudioMeta",
    "RawMeta",
    "OutputMeta",
    "probe_video",
    # Utils
    "StorageDir",
    "download",
    # Client
    "inference",
    "async_inference",
    "Inference",
    "AsyncInference",
    "UploadFileOptions",
    "TaskStatus",
    "ChatMessageStatus",
    "parse_status",
    "is_terminal_status",
    "is_message_ready",
    # Errors
    "APIError",
    "RequirementsNotMetError",
    "RequirementError",
    "SetupAction",
    "SessionError",
    "SessionNotFoundError",
    "SessionExpiredError",
    "SessionEndedError",
    "WorkerLostError",
    # Generated types - Enums
    "ChatStatus",
    "ChatMessageRole",
    "ChatMessageContentType",
    "ToolType",
    "ToolInvocationStatus",
    # Generated types - Agent
    "Agent",
    "AgentTool",
    "AgentToolDTO",
    "AgentConfig",
    # Generated types - Chat
    "ChatDTO",
    "ChatMessageDTO",
    "ChatData",
    "ChatMessageContent",
    "LLMInput",
    "LLMContextMessage",
    # Generated types - Tool
    "ToolCall",
    "ToolCallFunction",
    "ToolInvocationDTO",
    "ToolResultRequest",
    "Tool",
    "ToolFunction",
    "ToolParameters",
    # Agent SDK
    "Agent",
    "AsyncAgent",
    "AgentConfig",
    "InternalToolsConfig",
    "ToolCallInfo",
    # Tool Builder
    "tool",
    "app_tool",
    "agent_tool",
    "webhook_tool",
    "http_tool",
    "call_tool",
    "mcp_tool",
    "internal_tools",
    "lifecycle_hook",
    "LifecycleHookBuilder",
    "string",
    "number",
    "integer",
    "boolean",
    "enum_of",
    "array",
    "obj",
    "optional",
    "ClientTool",
    "ClientToolHandler",
    # Hook types
    "LifecycleHookConfig",
    "LifecycleHookPayload",
    "LifecycleHookResponse",
    "ContextInjection",
    "HookEvent",
    "HookHandlerType",
    "HookDecision",
    "ToolCallEventData",
    "ToolResultEventData",
    "ErrorEventData",
    # Namespaced APIs
    "TasksAPI",
    "AsyncTasksAPI",
    "FilesAPI",
    "AsyncFilesAPI",
    "AgentsAPI",
    "AsyncAgentsAPI",
    "SessionsAPI",
    "AsyncSessionsAPI",
    "SessionHandle",
    "AsyncSessionHandle",
    # Delta accumulator
    "DeltaAccumulator",
    # Streamable HTTP
    "streamable",
    "streamable_raw",
    "iter_ndjson",
    "stream_post",
    "stream_get",
    "StreamableMessage",
]
