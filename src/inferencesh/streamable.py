"""
Streamable HTTP client for NDJSON streaming.

This module provides NDJSON streaming as an alternative to SSE/EventSource,
avoiding browser connection limits when used in environments that support it.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Iterator, Optional, Generator, Union, Callable
from dataclasses import dataclass


@dataclass
class StreamableMessage:
    """A message from a streamable response."""
    data: Any
    event: Optional[str] = None
    fields: Optional[list] = None


def streamable(
    response: Any,
    skip_heartbeats: bool = True,
) -> Generator[Any, None, None]:
    """
    Iterate over NDJSON lines from a streaming HTTP response.

    Works with any response object that supports iter_lines() (httpx, requests, etc.)

    Args:
        response: HTTP response object with iter_lines() method
        skip_heartbeats: Whether to skip heartbeat messages (default: True)

    Yields:
        Parsed JSON objects from each line. If the message is wrapped
        with {data: T, fields: [...]}, yields just the data portion.
    """
    for line in response.iter_lines():
        if not line:
            continue

        # Handle bytes vs str
        if isinstance(line, bytes):
            line = line.decode('utf-8')

        line = line.strip()
        if not line:
            continue

        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue

        # Skip heartbeats
        if skip_heartbeats and isinstance(parsed, dict) and parsed.get('type') == 'heartbeat':
            continue

        # Unwrap data if present
        if isinstance(parsed, dict) and 'data' in parsed:
            yield parsed['data']
        else:
            yield parsed


def streamable_raw(
    response: Any,
    skip_heartbeats: bool = True,
) -> Generator[StreamableMessage, None, None]:
    """
    Like streamable() but yields StreamableMessage objects preserving event/fields.

    Args:
        response: HTTP response object with iter_lines() method
        skip_heartbeats: Whether to skip heartbeat messages (default: True)

    Yields:
        StreamableMessage objects with data, event, and fields attributes.
    """
    for line in response.iter_lines():
        if not line:
            continue

        # Handle bytes vs str
        if isinstance(line, bytes):
            line = line.decode('utf-8')

        line = line.strip()
        if not line:
            continue

        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue

        # Skip heartbeats
        if skip_heartbeats and isinstance(parsed, dict) and parsed.get('type') == 'heartbeat':
            continue

        if isinstance(parsed, dict):
            yield StreamableMessage(
                data=parsed.get('data', parsed),
                event=parsed.get('event'),
                fields=parsed.get('fields'),
            )
        else:
            yield StreamableMessage(data=parsed)


def iter_ndjson(
    response: Any,
    on_heartbeat: Optional[Callable[[], None]] = None,
) -> Generator[Dict[str, Any], None, None]:
    """
    Low-level NDJSON iterator that doesn't skip heartbeats.

    Args:
        response: HTTP response object with iter_lines() method
        on_heartbeat: Optional callback when heartbeat is received

    Yields:
        Raw parsed JSON objects from each line.
    """
    for line in response.iter_lines():
        if not line:
            continue

        # Handle bytes vs str
        if isinstance(line, bytes):
            line = line.decode('utf-8')

        line = line.strip()
        if not line:
            continue

        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue

        if isinstance(parsed, dict) and parsed.get('type') == 'heartbeat':
            if on_heartbeat:
                on_heartbeat()
            continue

        yield parsed


# Convenience function for httpx
def stream_post(
    client: Any,
    url: str,
    json_body: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    skip_heartbeats: bool = True,
    timeout: Optional[float] = None,
) -> Generator[Any, None, None]:
    """
    Make a streaming POST request and iterate NDJSON responses.

    Works with httpx.Client or any client with a stream() context manager.

    Example:
        import httpx

        with httpx.Client() as client:
            for item in stream_post(client, "https://api.example.com/stream", json_body={"query": "test"}):
                print(item)
    """
    request_headers = {
        'Accept': 'application/x-ndjson',
        **(headers or {}),
    }

    with client.stream(
        'POST',
        url,
        json=json_body,
        headers=request_headers,
        timeout=timeout,
    ) as response:
        response.raise_for_status()
        yield from streamable(response, skip_heartbeats=skip_heartbeats)


def stream_get(
    client: Any,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    skip_heartbeats: bool = True,
    timeout: Optional[float] = None,
) -> Generator[Any, None, None]:
    """
    Make a streaming GET request and iterate NDJSON responses.

    Works with httpx.Client or any client with a stream() context manager.
    """
    request_headers = {
        'Accept': 'application/x-ndjson',
        **(headers or {}),
    }

    with client.stream(
        'GET',
        url,
        headers=request_headers,
        timeout=timeout,
    ) as response:
        response.raise_for_status()
        yield from streamable(response, skip_heartbeats=skip_heartbeats)
