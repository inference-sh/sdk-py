"""Remotes execute scope, sandbox mount_ns, agent credential tools (api-v1623).

Daemon keys may list remotes scopes without remotes:write implying execute;
admin invoice preview returns nothing_to_invoice when no balance is due;
remote sandboxes report mount-namespace support; agents opt into credential
search/ask via internal_tools.credentials.
"""

from typing import Optional, get_type_hints

from inferencesh.types import (
    ErrorCode,
    InternalToolsConfig,
    RemoteSandbox,
    Scope,
    SystemInfo,
)


def test_remotes_execute_scope_wire_value_and_ordering():
    assert Scope.REMOTES_EXECUTE.value == "remotes:execute"
    assert Scope.REMOTES_EXECUTE == "remotes:execute"
    assert "REMOTES_EXECUTE" in Scope.__members__

    members = list(Scope)
    write_idx = members.index(Scope.REMOTES_WRITE)
    execute_idx = members.index(Scope.REMOTES_EXECUTE)
    sandboxes_read_idx = members.index(Scope.SANDBOXES_READ)
    assert execute_idx == write_idx + 1
    assert sandboxes_read_idx == execute_idx + 1


def test_nothing_to_invoice_error_code_wire_value():
    assert ErrorCode.NOTHING_TO_INVOICE.value == "nothing_to_invoice"
    assert ErrorCode.NOTHING_TO_INVOICE == "nothing_to_invoice"

    members = list(ErrorCode)
    assert ErrorCode.REQUEST_OPEN in members
    request_open_idx = members.index(ErrorCode.REQUEST_OPEN)
    nothing_idx = members.index(ErrorCode.NOTHING_TO_INVOICE)
    assert nothing_idx == request_open_idx + 1


def test_internal_tools_credentials_opt_in_flag():
    hints = get_type_hints(InternalToolsConfig)
    assert hints["credentials"] == Optional[bool]

    enabled: InternalToolsConfig = {
        "remote": True,
        "credentials": True,
    }
    disabled: InternalToolsConfig = {
        "credentials": False,
    }
    assert enabled["credentials"] is True
    assert disabled["credentials"] is False


def test_remote_sandbox_mount_namespace_fields():
    hints = get_type_hints(RemoteSandbox)
    assert hints["mount_ns"] == bool
    assert hints["no_mount_ns"] == str

    with_mount_ns: RemoteSandbox = {
        "mechanism": "landlock",
        "available": True,
        "mount_ns": True,
        "no_mount_ns": "",
    }
    without_mount_ns: RemoteSandbox = {
        "mechanism": "landlock",
        "available": True,
        "mount_ns": False,
        "no_mount_ns": "user namespaces disabled",
    }
    assert with_mount_ns["mount_ns"] is True
    assert without_mount_ns["no_mount_ns"] == "user namespaces disabled"


def test_system_info_sandbox_carries_mount_ns_report():
    info: SystemInfo = {
        "sandbox": {
            "mechanism": "landlock",
            "version": "abi 6",
            "available": True,
            "required": False,
            "mount_ns": True,
            "no_mount_ns": "",
        },
    }
    assert info["sandbox"]["mount_ns"] is True
    assert info["sandbox"]["no_mount_ns"] == ""