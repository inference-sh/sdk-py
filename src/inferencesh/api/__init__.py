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

__all__ = [
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
