"""Tests for streamable HTTP module."""

import json
import pytest
from unittest.mock import MagicMock, patch
from inferencesh.streamable import streamable, streamable_raw, iter_ndjson, StreamableMessage


class MockResponse:
    """Mock HTTP response with iter_lines support."""

    def __init__(self, lines: list[str | bytes]):
        self._lines = lines

    def iter_lines(self):
        for line in self._lines:
            yield line


class TestStreamable:
    """Tests for streamable() function."""

    def test_parse_ndjson_lines(self):
        """Should parse NDJSON lines."""
        response = MockResponse([
            '{"id":1,"name":"first"}',
            '{"id":2,"name":"second"}',
        ])

        results = list(streamable(response))

        assert len(results) == 2
        assert results[0] == {"id": 1, "name": "first"}
        assert results[1] == {"id": 2, "name": "second"}

    def test_skip_heartbeats_by_default(self):
        """Should skip heartbeat messages by default."""
        response = MockResponse([
            '{"id":1}',
            '{"type":"heartbeat"}',
            '{"id":2}',
        ])

        results = list(streamable(response))

        assert len(results) == 2
        assert results[0] == {"id": 1}
        assert results[1] == {"id": 2}

    def test_include_heartbeats_when_disabled(self):
        """Should include heartbeats when skip_heartbeats=False."""
        response = MockResponse([
            '{"id":1}',
            '{"type":"heartbeat"}',
            '{"id":2}',
        ])

        results = list(streamable(response, skip_heartbeats=False))

        assert len(results) == 3

    def test_unwrap_data_from_wrapped_messages(self):
        """Should unwrap data from {data: T, fields: [...]} format."""
        response = MockResponse([
            '{"data":{"id":1},"fields":["id"]}',
            '{"event":"update","data":{"id":2}}',
        ])

        results = list(streamable(response))

        assert len(results) == 2
        assert results[0] == {"id": 1}
        assert results[1] == {"id": 2}

    def test_handle_bytes_input(self):
        """Should handle bytes from response."""
        response = MockResponse([
            b'{"id":1}',
            b'{"id":2}',
        ])

        results = list(streamable(response))

        assert len(results) == 2
        assert results[0] == {"id": 1}
        assert results[1] == {"id": 2}

    def test_handle_empty_lines(self):
        """Should skip empty lines."""
        response = MockResponse([
            '{"id":1}',
            '',
            '   ',
            '{"id":2}',
        ])

        results = list(streamable(response))

        assert len(results) == 2

    def test_handle_unicode(self):
        """Should handle unicode in messages."""
        response = MockResponse([
            '{"text":"Hello 世界 🎉"}',
        ])

        results = list(streamable(response))

        assert results[0] == {"text": "Hello 世界 🎉"}


class TestStreamableRaw:
    """Tests for streamable_raw() function."""

    def test_preserve_event_and_fields(self):
        """Should preserve event and fields in raw mode."""
        response = MockResponse([
            '{"event":"update","data":{"id":1},"fields":["id"]}',
        ])

        results = list(streamable_raw(response))

        assert len(results) == 1
        assert results[0].event == "update"
        assert results[0].data == {"id": 1}
        assert results[0].fields == ["id"]

    def test_handle_plain_message(self):
        """Should handle plain messages without wrapper."""
        response = MockResponse([
            '{"id":1}',
        ])

        results = list(streamable_raw(response))

        assert len(results) == 1
        assert results[0].data == {"id": 1}
        assert results[0].event is None
        assert results[0].fields is None


class TestIterNdjson:
    """Tests for iter_ndjson() function."""

    def test_call_heartbeat_callback(self):
        """Should call on_heartbeat callback for heartbeats."""
        response = MockResponse([
            '{"id":1}',
            '{"type":"heartbeat"}',
            '{"id":2}',
        ])

        heartbeats = []
        results = list(iter_ndjson(response, on_heartbeat=lambda: heartbeats.append(1)))

        assert len(results) == 2
        assert len(heartbeats) == 1


class TestChunkingEdgeCases:
    """Tests for various edge cases."""

    def test_multiple_messages_per_line_not_supported(self):
        """iter_lines returns one line at a time, so this is the library's job."""
        # This is handled by the HTTP library (httpx/requests), not our code
        pass

    def test_skip_invalid_json(self):
        """Should skip lines that aren't valid JSON."""
        response = MockResponse([
            '{"id":1}',
            'not valid json',
            '{"id":2}',
        ])

        results = list(streamable(response))

        # Invalid JSON is skipped
        assert len(results) == 2

    def test_handle_non_dict_json(self):
        """Should handle JSON that isn't a dict."""
        response = MockResponse([
            '"just a string"',
            '123',
            '[1,2,3]',
            '{"id":1}',
        ])

        results = list(streamable(response))

        assert len(results) == 4
        assert results[0] == "just a string"
        assert results[1] == 123
        assert results[2] == [1, 2, 3]
        assert results[3] == {"id": 1}
