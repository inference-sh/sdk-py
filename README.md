# inferencesh — python sdk for ai inference api

[![PyPI version](https://badge.fury.io/py/inferencesh.svg)](https://pypi.org/project/inferencesh/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)

official python sdk for [inference.sh](https://inference.sh) — the ai agent runtime for serverless ai inference.

run ai models, build ai agents, and deploy generative ai applications. access 250+ models including flux, stable diffusion, llms (claude, gpt, gemini), video generation (veo, seedance), and more.

## installation

```bash
pip install inferencesh
```

## client api

The `Inference` client exposes namespaced APIs:

| Property | Purpose |
|----------|---------|
| `client.tasks` | Run and manage tasks |
| `client.files` | Upload files |
| `client.agents` | Create agents (`agents.create()` is the same as `agent()` without per-chat context) |
| `client.sessions` | List, inspect, and end sessions; use `client.session()` for a context manager |

`client.run()` and `client.upload_file()` remain supported as legacy aliases for `client.tasks.run()` and `client.files.upload()`.

## client usage

```python
from inferencesh import inference, TaskStatus

# Create client
client = inference(api_key="your-api-key")

# Simple synchronous usage - waits for completion by default
result = client.tasks.run({
    "app": "your-app",
    "input": {"key": "value"},
    "infra": "cloud",
    "variant": "default"
})

print(f"Task ID: {result.get('id')}")
print(f"Output: {result.get('output')}")
```

### with setup parameters

Setup parameters configure the app instance (e.g., model selection). Workers with matching setup are "warm" and skip the setup phase:

```python
result = client.tasks.run({
    "app": "your-app",
    "setup": {"model": "schnell"},  # Setup parameters
    "input": {"prompt": "hello"}
})
```

### run options

```python
# Wait for completion (default behavior)
result = client.tasks.run(params)  # wait=True is default

# Return immediately without waiting
task = client.tasks.run(params, wait=False)
task_id = task["id"]  # Use this to check status later

# Stream updates as they happen
from inferencesh import parse_status, is_terminal_status

for update in client.tasks.run(params, stream=True):
    status = parse_status(update.get("status"))
    print(f"Status: {status.name if status else 'unknown'}")
    if status == TaskStatus.COMPLETED:
        print(f"Output: {update.get('output')}")
```

### task management

```python
# Get current task state
task = client.tasks.get(task_id)
print(f"Status: {TaskStatus(task['status']).name}")

# Cancel a running task
client.tasks.cancel(task_id)

# Wait for a task to complete
result = client.tasks.wait_for_completion(task_id)

# Stream updates for an existing task
with client.tasks.stream(task_id) as stream:
    for update in stream:
        if parse_status(update.get("status")) == TaskStatus.COMPLETED:
            print(f"Result: {update.get('output')}")
            break
        if is_terminal_status(update.get("status")):
            break

# Access final result after streaming
print(f"Final result: {stream.result}")
```

### task status values

Task statuses are integer enums. Streaming responses may return either integers or lowercase strings (for example `"running"`).

```python
from inferencesh import TaskStatus

TaskStatus.RECEIVED    # 1 - Task received by server
TaskStatus.QUEUED      # 2 - Task queued for processing
TaskStatus.DISPATCHED  # 3 - Task dispatched to a worker
TaskStatus.PREPARING   # 4 - Worker preparing environment
TaskStatus.SERVING     # 5 - Model being loaded
TaskStatus.SETTING_UP  # 6 - Task setup in progress
TaskStatus.RUNNING     # 7 - Task actively running
TaskStatus.CANCELLING  # 8 - Cancellation in progress
TaskStatus.UPLOADING   # 9 - Uploading results
TaskStatus.COMPLETED   # 10 - Task completed successfully
TaskStatus.FAILED      # 11 - Task failed
TaskStatus.CANCELLED   # 12 - Task was cancelled
```

### status helpers

Use these helpers when handling streamed task or agent message updates:

```python
from inferencesh import parse_status, is_terminal_status, is_message_ready, TaskStatus

# Tasks: parse int or string status values
status = parse_status(update.get("status"))  # TaskStatus or None
if status == TaskStatus.COMPLETED:
    ...

# Tasks: check for a terminal task state (completed, failed, cancelled)
if is_terminal_status(update.get("status")):
    ...

# Agent chat: check if a message has finished streaming
if is_message_ready(message.get("status")):  # ready, failed, or cancelled
    ...
```

`is_terminal_status()` is for **task** statuses. For **chat message** statuses, use `is_message_ready()` instead.

### sessions (stateful execution)

Sessions allow you to maintain state across multiple task invocations. The worker stays warm between calls, preserving loaded models and in-memory state.

```python
# Start a new session
result = client.tasks.run({
    "app": "my-stateful-app",
    "input": {"prompt": "hello"},
    "session": "new"
})

session_id = result.get("session_id")
print(f"Session ID: {session_id}")

# Continue the session with another call
result2 = client.tasks.run({
    "app": "my-stateful-app",
    "input": {"prompt": "remember what I said?"},
    "session": session_id
})
```

#### session context manager

For multi-step workflows, use `client.session()` to create a session and call app functions by name. The session ends automatically when the context exits.

```python
# Optional kwargs for the initial run: input, function (default "run")
with client.session("my-stateful-app@abc123", input={"prompt": "hello"}) as session:
    # First argument is the app function name; second is input data
    session.call("process", {"step": 1})
    session.call("process", {"step": 2}, wait=False)  # same options as client.run()

    # Stream updates for a session call
    for update in session.call("run", {"prompt": "..."}, stream=True):
        print(update.get("status"))
    print(session.session_id)
```

`session.call()` forwards to `client.run()` with the session ID pinned, so it accepts the same keyword arguments: `wait`, `stream`, `auto_reconnect`, and related streaming options. With the default `wait=True`, it returns the completed task dict; with `wait=False`, task info; with `stream=True`, an iterator of status updates (same as `client.run()`).

On the handle itself you can also call `session.info()`, `session.keepalive()`, and `session.end()` without going through `client.sessions`.

#### session management

```python
info = client.sessions.get(session_id)
sessions = client.sessions.list()
client.sessions.keepalive(session_id)  # extend idle timeout without a task call
client.sessions.end(session_id)
```

#### custom session timeout

By default, sessions expire after 60 seconds of inactivity. You can customize this with `session_timeout` (1-3600 seconds):

```python
# Create a session with 5-minute idle timeout
result = client.tasks.run({
    "app": "my-stateful-app",
    "input": {"prompt": "hello"},
    "session": "new",
    "session_timeout": 300  # 5 minutes
})

# Session stays alive for 5 minutes after each call
```

**Notes:**
- `session_timeout` is only valid when `session: "new"`
- Minimum timeout: 1 second
- Maximum timeout: 3600 seconds (1 hour)
- Each successful call resets the idle timer

For complete session documentation including error handling, best practices, and advanced patterns, see the [Sessions Developer Guide](https://inference.sh/docs/extend/sessions).

### file upload

```python
from inferencesh import UploadFileOptions

# Upload from file path
file_obj = client.files.upload("/path/to/image.png")
print(f"URI: {file_obj['uri']}")

# Upload from bytes
file_obj = client.files.upload(
    b"raw bytes data",
    UploadFileOptions(
        filename="data.bin",
        content_type="application/octet-stream"
    )
)

# Upload with options
file_obj = client.files.upload(
    "/path/to/image.png",
    UploadFileOptions(
        filename="custom_name.png",
        content_type="image/png",
        public=True  # Make publicly accessible
    )
)
```

Note: Files in task input are automatically uploaded. You only need `files.upload()` for manual uploads.

Task and session `input` values are scanned recursively. Local file paths, long base64 strings, and `data:<mime>;base64,...` URIs are uploaded and replaced with cloud URIs before the run is sent (plain short strings are left unchanged).

## agent chat

Chat with AI agents using `client.agents.create()` or `client.agent()`. Both return the same `Agent` instance; use `client.agent()` when you need per-chat **context** variables (see below).

### using a template agent

Use an existing agent from your workspace by its `namespace/name@shortid`:

```python
from inferencesh import inference, is_message_ready

client = inference(api_key="your-api-key")

# Create agent from template
agent = client.agents.create("my-org/assistant@abc123")

# Send a message with streaming
def on_message(msg):
    content = msg.get("content", [])
    for c in content:
        if c.get("type") == "text" and c.get("text"):
            print(c["text"], end="", flush=True)

response = agent.send_message("Hello!", on_message=on_message)
print(f"\nChat ID: {agent.chat_id}")

# Or stream manually and stop when the message is ready
for message in agent.stream_messages():
    on_message(message)
    if is_message_ready(message.get("status")):
        break

# Poll chat state or stop generation
chat = agent.get_chat()  # None if no message sent yet
agent.stop_chat()        # POST /chats/{id}/stop for the active chat
```

`send_message()` can also drive streaming via callbacks (`on_message`, `on_tool_call`), which internally uses `stream_all()`. For manual control, use the iterators below (requires an active chat — call `send_message()` first):

```python
# Message-level updates (chat_messages events)
for message in agent.stream_messages():
    ...

# Chat-level status updates (chats events, e.g. busy → idle)
for chat in agent.stream_chat():
    if chat.get("status") == "idle":
        break

# Unified stream with callbacks; stops when chat becomes idle
agent.stream_all(
    on_message=on_message,
    on_tool_call=on_tool_call,
    on_chat=lambda chat: print(chat.get("status")),
)
```

On the sync `Agent`, `stream_messages()` and `stream_chat()` accept `auto_reconnect`, `max_reconnects`, and `reconnect_delay_ms` (same semantics as task streaming). `AsyncAgent` exposes `stream_messages()` and `stream_chat()` as async iterators (no reconnect kwargs) after `await agent.send_message(...)`.

### creating an ad-hoc agent

Create agents on-the-fly without saving to your workspace:

```python
from inferencesh import inference, tool, string

client = inference(api_key="your-api-key")

# Define a client tool (handler runs in your process)
weather_tool = (
    tool("get_weather")
    .describe("Get current weather")
    .param("city", string("City name"))
    .handler(lambda args: '{"temp": 72, "conditions": "sunny"}')
)

# Create ad-hoc agent (AgentConfig dict; export: from inferencesh import AgentConfig)
agent = client.agents.create({
    "core_app": {"ref": "infsh/claude-sonnet-4@abc123"},
    "system_prompt": "You are a helpful assistant.",
    "tools": [weather_tool],
})

def on_tool_call(call):
    print(f"[Tool: {call.name}]")
    # Tools with handlers are auto-executed

response = agent.send_message(
    "What's the weather in Paris?",
    on_message=on_message,
    on_tool_call=on_tool_call,
)
```

### file attachments

Attach files to a message with the `files` argument (bytes or base64/data URI strings). Each item is uploaded via `agent.upload_file()` before the message is sent:

```python
# Raw bytes
agent.send_message("Summarize this", files=[b"file contents"])

# Data URI (content type parsed from the URI)
agent.send_message("Analyze image", files=["data:image/png;base64,iVBORw0KGgo="])
```

Upload separately when you need the `FileRef` (for example, to reuse the same file across messages):

```python
ref = agent.upload_file(b"notes", filename="notes.txt")
# ref["uri"], ref["filename"], ref["content_type"], ref["size"]
```

`agent.upload_file()` accepts bytes, base64 strings, or `data:<mime>;base64,...` URIs. It is separate from `client.files.upload()`, which also accepts local file paths.

### structured output with `run()`

When the agent uses a finish tool, `agent.run(text)` sends a message, waits for completion, and returns the parsed `chat.output`. Returns `None` if the agent finished without calling the finish tool:

```python
result = agent.run("Extract entities from the text above")
if result is not None:
    print(result)
```

### per-chat context variables

Pass context when creating an agent with `client.agent()` (the `context` argument is not available on `client.agents.create()`). Values are available in HTTP/call tool URL templates as `{{context.KEY}}`:

```python
from inferencesh import call_tool

agent = client.agent(
    "my-org/assistant@abc123",
    context={"tenant_id": "acme", "user_id": "42"},
)

# call_tool URL can reference context, e.g.:
# https://api.example.com/users/{{context.user_id}}/data
lookup = (
    call_tool("fetch_user", "https://api.example.com/users/{{context.user_id}}")
    .auth(bearer="API_TOKEN")
    .describe("Fetch user profile")
    .build()
)
```

### tool builder

Define tools with the fluent API (`tool`, `app_tool`, `agent_tool`, `call_tool`, `mcp_tool`, `webhook_tool`):

```python
from inferencesh import (
    tool, app_tool, agent_tool, call_tool, mcp_tool,
    string, optional, boolean,
)

# Client tool (runs in your code)
search = (
    tool("search")
    .describe("Search files")
    .param("pattern", string("Glob pattern"))
    .build()
)

# App tool (runs another inference app)
generate = (
    app_tool("generate", "infsh/flux-schnell@latest")
    .describe("Generate an image")
    .param("prompt", string("Image description"))
    .function("generate")          # multi-function apps
    .session_enabled()             # agent can pass session IDs
    .require_approval()            # human-in-the-loop
    .build()
)

# HTTP tool with auth (call_tool is an alias for http_tool)
notify = (
    call_tool("notify", "https://api.example.com/notify")
    .method("POST")
    .auth(api_key="MY_API_KEY")
    .header("X-Tenant", "{{context.tenant_id}}")
    .param("message", string("Notification body"))
    .build()
)

# MCP connector tool (integration must be connected in workspace)
web_search = (
    mcp_tool("web_search", "int-abc123", "search")
    .describe("Search via connected MCP server")
    .build()
)
```

See the [Tool Builder reference](https://inference.sh/docs/api/agent-tools) for schema helpers and more examples.

### generated tool types

The fluent tool builder produces JSON Schema objects. For lower-level typing (parsing LLM tool calls or building `Tool` / `ToolParameters` dicts by hand), import enums from `inferencesh.types`:

| Enum | Purpose | Members |
|------|---------|---------|
| `ToolCallType` | Discriminator on tool calls and tool definitions | `TOOL_TYPE_FUNCTION` (`"function"`) |
| `ToolParamType` | JSON Schema parameter types in `ToolParameters` | `OBJECT`, `STRING`, `INTEGER`, `NUMBER`, `BOOLEAN`, `ARRAY`, `NULL` |

```python
from inferencesh.types import ToolCallType, ToolParamType

# Tool / ToolCall wire format
assert ToolCallType.TOOL_TYPE_FUNCTION.value == "function"

# Parameter schema (matches JSON Schema "type" strings)
assert ToolParamType.STRING.value == "string"
```

`ToolParamType` is separate from `ToolCallType`. Parameter types such as `"string"` and `"object"` belong on `ToolParamType`, not on `ToolCallType`.

Package exports (`Tool`, `ToolCall`, `ToolParameters`, and related TypedDicts) are available from `inferencesh`; import `ToolCallType` and `ToolParamType` from `inferencesh.types` when you need the enums.

### integration and instance enums

Workspace API responses use generated enums in `inferencesh.types`:

```python
from inferencesh.types import (
    IntegrationProvider,
    IntegrationAuthType,
    IntegrationStatus,
    InstanceStatus,
)

IntegrationProvider.SLACK       # "slack"
IntegrationAuthType.O_AUTH      # "oauth"
IntegrationStatus.CONNECTED     # "connected"

InstanceStatus.CREATING         # "creating"
InstanceStatus.PENDING_PROVIDER # "pending_provider"
InstanceStatus.ACTIVE           # "active"
InstanceStatus.ERROR            # "error"
```

`IntegrationProvider` includes `google`, `slack`, `notion`, `github`, `discord`, `gcp`, `mcp`, and others. `InstanceStatus` covers the full lifecycle from `creating` through `deleted`.

### requirements errors (HTTP 412)

When an app is missing secrets, integrations, or scopes, `client.tasks.run()` raises `RequirementsNotMetError`:

```python
from inferencesh import RequirementsNotMetError

try:
    result = client.tasks.run({"app": "my-app", "input": {...}})
except RequirementsNotMetError as e:
    for err in e.errors:
        print(f"{err.type}: {err.key} — {err.message}")
    if e.errors[0].action:
        print(e.errors[0].action.type)  # e.g. connect integration
```

Widget and form results for client tools use a dict payload (serialized to JSON on the wire):

```python
agent.submit_tool_result("inv_1", '{"ok": true}')
agent.submit_tool_result("inv_2", {
    "action": {"type": "confirm"},
    "form_data": {"name": "Ada"},
})
```

Session API errors (`SessionNotFoundError`, `SessionExpiredError`, `SessionEndedError`, `WorkerLostError`) are raised when a session is missing, expired, ended, or the worker is lost.

### agent methods

| Method | Description |
|--------|-------------|
| `send_message(text, files=None, on_message=..., on_tool_call=...)` | Send a message; optional `files`; callbacks use `stream_all()` |
| `run(text, ...)` | Send a message and return `chat.output` from the finish tool (or `None`) |
| `upload_file(data, filename=None)` | Upload bytes, base64, or a data URI; returns a `FileRef` |
| `get_chat(chat_id=None)` | Fetch chat by ID (defaults to active chat; `None` if none) |
| `stop_chat()` | Stop generation on the active chat |
| `submit_tool_result(tool_id, result_or_action)` | Submit result for a client tool (string or widget action dict) |
| `stream_messages(...)` | Iterator of `chat_messages` events (active chat required) |
| `stream_chat(...)` | Iterator of `chats` events (active chat required) |
| `stream_all(on_chat=..., on_message=..., on_tool_call=...)` | Callback-driven unified stream until idle |
| `reset()` | Clear active chat and dispatched tool state |

### async agent

```python
from inferencesh import async_inference, is_message_ready

client = async_inference(api_key="your-api-key")
agent = client.agents.create("my-org/assistant@abc123")

response = await agent.send_message("Hello!")

# Same helpers as sync: files on send_message, upload_file, run() for finish-tool output
output = await agent.run("Return structured data")

# Stream after send_message (async iterators; no auto_reconnect kwargs)
async for message in agent.stream_messages():
    if is_message_ready(message.get("status")):
        break
```

## async client

```python
from inferencesh import async_inference, TaskStatus

async def main():
    client = async_inference(api_key="your-api-key")

    # Simple usage - wait for completion
    result = await client.tasks.run({
        "app": "your-app",
        "input": {"key": "value"},
        "infra": "cloud",
        "variant": "default"
    })
    print(f"Output: {result.get('output')}")

    # Return immediately without waiting
    task = await client.tasks.run(params, wait=False)

    # Stream updates
    from inferencesh import parse_status

    async for update in await client.tasks.run(params, stream=True):
        if parse_status(update.get("status")) == TaskStatus.COMPLETED:
            print(f"Output: {update.get('output')}")

    # Task management
    task = await client.tasks.get(task_id)
    await client.tasks.cancel(task_id)
    result = await client.tasks.wait_for_completion(task_id)

    # Stream existing task
    async with client.tasks.stream(task_id) as stream:
        async for update in stream:
            print(f"Update: {update}")

    # Stateful session (async) — session() is async, so await before the context manager
    async with await client.session("my-app@abc123", input={"start": True}) as session:
        await session.call("step", {"x": 1})
        async for update in await session.call("run", {"prompt": "..."}, stream=True):
            print(update.get("status"))
```

## file handling

the `File` class provides a standardized way to handle files in the inference.sh ecosystem:

```python
from inferencesh import File

# Basic file creation
file = File(path="/path/to/file.png")

# File with explicit metadata
file = File(
    path="/path/to/file.png",
    content_type="image/png",
    filename="custom_name.png",
    size=1024  # in bytes
)

# Create from path (automatically populates metadata)
file = File.from_path("/path/to/file.png")

# Check if file exists
exists = file.exists()

# Access file metadata
print(file.content_type)  # automatically detected if not specified
print(file.size)       # file size in bytes
print(file.filename)   # basename of the file

# Refresh metadata (useful if file has changed)
file.refresh_metadata()
```

the `File` class automatically handles:
- mime type detection
- file size calculation
- filename extraction from path
- file existence checking

### downloading remote files

`download()` fetches a URL into a directory and returns the local path. Paths are cached under a short hash of the URL (host, path, and query string); repeated downloads of the same URL reuse the file unless the directory is `StorageDir.TEMP`:

```python
from inferencesh import download, StorageDir

path = download("https://cdn.example.com/model.bin", StorageDir.CACHE)
# e.g. /app/cache/<hash>/model.bin

# Query strings produce distinct cache entries
download("https://cdn.example.com/asset.png?v=1", "/tmp/assets")
download("https://cdn.example.com/asset.png?v=2", "/tmp/assets")  # separate hash dir
```

`StorageDir` provides standard app paths (`DATA`, `TEMP`, `CACHE`) and ensures the directory exists via `.path`.

## creating an app

to create an inference app, inherit from `BaseApp` and define your input/output types:

```python
from inferencesh import BaseApp, BaseAppInput, BaseAppOutput, File

class AppInput(BaseAppInput):
    image: str  # URL or file path to image
    mask: str   # URL or file path to mask

class AppOutput(BaseAppOutput):
    image: File

class MyApp(BaseApp):
    async def setup(self):
        # Initialize your model here
        pass

    async def run(self, app_input: AppInput) -> AppOutput:
        # Process input and return output
        result_path = "/tmp/result.png"
        return AppOutput(image=File(path=result_path))

    async def unload(self):
        # Clean up resources
        pass
```

Input and output models inherit from `BaseAppInput` / `BaseAppOutput` (Pydantic v2). The runtime may pass a `Metadata` object (with `app_id`, `worker_id`, and extra fields) to app methods. JSON schemas preserve field definition order for the app store UI.

app lifecycle has three main methods:
- `setup()`: called when the app starts, use it to initialize models
- `run()`: called for each inference request
- `unload()`: called when shutting down, use it to free resources

## resources

- [documentation](https://inference.sh/docs) — getting started guides and api reference
- [blog](https://inference.sh/blog) — tutorials on ai agents, image generation, and more
- [app store](https://app.inference.sh) — browse 250+ ai models
- [discord](https://discord.gg/inference) — community support
- [github](https://github.com/inference-sh) — open source projects

## license

MIT © [inference.sh](https://inference.sh)
