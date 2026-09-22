"""Namespaced API modules."""

from .tasks import TasksAPI, AsyncTasksAPI
from .files import FilesAPI, AsyncFilesAPI
from .agents import AgentsAPI, AsyncAgentsAPI
from .sessions import (
    SessionsAPI,
    AsyncSessionsAPI,
    SessionHandle,
    AsyncSessionHandle,
)
from .sockets import SocketsAPI, AsyncSocketsAPI

__all__ = [
    "SocketsAPI",
    "AsyncSocketsAPI",
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
]
