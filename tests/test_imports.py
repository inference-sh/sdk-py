"""Import smoke tests.

Ensures every public module and submodule can be imported without errors.
This catches broken references like the AppSession/AppSessionDTO mismatch
that slipped into 0.7.2 because no test exercised the import path.
"""

import importlib
import pkgutil

import pytest

import inferencesh


# ── Package-wide recursive import ────────────────────────────────────────────

def _iter_submodules(package, prefix=""):
    """Yield dotted names of every submodule/subpackage under *package*."""
    for importer, modname, ispkg in pkgutil.walk_packages(
        package.__path__, prefix=package.__name__ + "."
    ):
        yield modname


def test_all_submodules_importable():
    """Every .py under inferencesh/ must import cleanly."""
    failures = []
    for modname in _iter_submodules(inferencesh):
        try:
            importlib.import_module(modname)
        except Exception as exc:
            failures.append(f"{modname}: {exc}")

    assert not failures, "Failed imports:\n" + "\n".join(failures)


# ── Top-level __all__ exports ────────────────────────────────────────────────

def test_all_exports_resolvable():
    """Every name in __all__ must be accessible on the package."""
    missing = [name for name in inferencesh.__all__ if not hasattr(inferencesh, name)]
    assert not missing, f"Names in __all__ but missing from package: {missing}"


# ── Core public API imports ──────────────────────────────────────────────────

@pytest.mark.parametrize("name", [
    # Base app types
    "BaseApp", "BaseAppInput", "BaseAppOutput", "BaseAppSetup", "File",
    # Client
    "Inference", "AsyncInference",
    # Namespaced APIs
    "TasksAPI", "AsyncTasksAPI",
    "FilesAPI", "AsyncFilesAPI",
    "AgentsAPI", "AsyncAgentsAPI",
    "SessionsAPI", "AsyncSessionsAPI",
    "SessionHandle", "AsyncSessionHandle",
    # Agent SDK
    "Agent", "AsyncAgent",
    # Tools
    "tool", "app_tool", "agent_tool", "http_tool", "call_tool", "mcp_tool",
    # Errors
    "APIError", "SessionError", "SessionNotFoundError",
    # Streamable
    "streamable", "streamable_raw",
    # OutputMeta
    "OutputMeta", "TextMeta", "ImageMeta", "VideoMeta", "AudioMeta",
])
def test_public_name_importable(name):
    """Core public names must be importable from the top-level package."""
    assert hasattr(inferencesh, name), f"inferencesh.{name} not found"


# ── Submodule direct imports ─────────────────────────────────────────────────

@pytest.mark.parametrize("module", [
    "inferencesh.client",
    "inferencesh.types",
    "inferencesh.agent",
    "inferencesh.tools",
    "inferencesh.streamable",
    "inferencesh.api",
    "inferencesh.api.sessions",
    "inferencesh.api.tasks",
    "inferencesh.api.files",
    "inferencesh.api.agents",
    "inferencesh.models",
    "inferencesh.models.base",
    "inferencesh.models.file",
    "inferencesh.models.llm",
    "inferencesh.models.output_meta",
    "inferencesh.models.errors",
    "inferencesh.utils",
    "inferencesh.utils.storage",
    "inferencesh.utils.download",
])
def test_submodule_importable(module):
    """Each submodule must import without errors."""
    importlib.import_module(module)


# ── Generated types (from typegen) ───────────────────────────────────────────

@pytest.mark.parametrize("enum_cls,members", [
    (
        "ToolType",
        {
            "HTTP": "http",
            "MCP": "mcp",
            "CLIENT": "client",
            "APP": "app",
        },
    ),
    (
        "InstanceCloudProvider",
        {"CLOUD_AWS": "aws"},
    ),
    (
        "GPUType",
        {"AMD": "amd"},
    ),
    (
        "EntitlementResource",
        {
            "RESOURCE_API_KEYS": "api_keys",
            "RESOURCE_STORAGE_MB": "storage_mb",
            "RESOURCE_FEATURE_BYOK": "feature:byok",
        },
    ),
    (
        "VideoResolution",
        {
            "VIDEO_RES480P": "480p",
            "VIDEO_RES4K": "4k",
        },
    ),
])
def test_generated_enum_acronym_members(enum_cls, members):
    """Gotypegen must preserve acronyms (HTTP not H_T_T_P, MCP not M_C_P)."""
    from inferencesh import types

    cls = getattr(types, enum_cls)
    for member_name, value in members.items():
        assert hasattr(cls, member_name), f"{enum_cls}.{member_name} missing"
        assert getattr(cls, member_name).value == value


@pytest.mark.parametrize("name", [
    # Enums
    "ChatStatus", "ChatMessageRole", "ChatMessageContentType",
    "ToolType", "ToolInvocationStatus", "TaskStatus",
    # DTOs
    "ChatDTO", "ChatMessageDTO", "AgentToolDTO", "ToolInvocationDTO",
    "AppSessionDTO",
    # Agent config
    "AgentConfigInput", "AgentTool", "InternalToolsConfig",
    # Tool schema
    "Tool", "ToolFunction", "ToolParameters", "ToolCall", "ToolCallFunction",
])
def test_generated_type_exists(name):
    """Typegen'd types must exist in inferencesh.types."""
    from inferencesh import types
    assert hasattr(types, name), f"inferencesh.types.{name} not found"
