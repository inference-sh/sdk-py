"""Regression tests for File URL/data-URI download temp file isolation (234a041)."""

from __future__ import annotations

import io
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from inferencesh import File

URL = "https://example.com/worker-shared/asset.bin"


@pytest.fixture
def file_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("FILE_CACHE_DIR", str(tmp_path))
    return tmp_path


def _urlopen(body: bytes = b"payload"):
    return patch("urllib.request.urlopen", side_effect=lambda *a, **k: io.BytesIO(body))


class TestFileUrlDownloadTempIsolation:
    def test_url_download_uses_mkstemp_beside_cache_file(self, file_cache):
        captured: dict = {}

        real_mkstemp = tempfile.mkstemp

        def record_mkstemp(*args, **kwargs):
            captured["kwargs"] = kwargs
            return real_mkstemp(*args, **kwargs)

        with _urlopen(), patch("tempfile.mkstemp", side_effect=record_mkstemp):
            path = File(uri=URL).path

        assert path is not None
        cache_path = Path(path)
        assert captured["kwargs"]["dir"] == cache_path.parent
        assert captured["kwargs"]["suffix"] == ".tmp"
        assert str(captured["kwargs"]["prefix"]).startswith(cache_path.name + ".")

    def test_retry_after_failed_download_allocates_fresh_temp_file(self, file_cache):
        """Each attempt must use its own mkstemp path (never a fixed cache_path.tmp)."""
        tmp_paths: list[str] = []
        real_mkstemp = tempfile.mkstemp

        def tracking_mkstemp(*args, **kwargs):
            fd, tmp = real_mkstemp(*args, **kwargs)
            tmp_paths.append(tmp)
            return fd, tmp

        responses = [
            MagicMock(headers=None, read=MagicMock(side_effect=OSError("transient"))),
            MagicMock(
                headers=None,
                read=MagicMock(side_effect=[b"recovered", b""]),
            ),
        ]
        response_iter = iter(responses)

        def next_response(*args, **kwargs):
            resp = next(response_iter)
            resp.__enter__ = MagicMock(return_value=resp)
            resp.__exit__ = MagicMock(return_value=False)
            return resp

        with patch("tempfile.mkstemp", side_effect=tracking_mkstemp), patch(
            "urllib.request.urlopen", side_effect=next_response
        ), patch("time.sleep"):
            path = File(uri=URL).path

        assert path is not None
        assert len(tmp_paths) == 2
        assert tmp_paths[0] != tmp_paths[1]
        for tmp in tmp_paths:
            assert not os.path.exists(tmp)

    def test_url_download_commits_with_os_replace(self, file_cache):
        replaced: list[tuple[str, str]] = []
        real_replace = os.replace

        def track_replace(src, dst):
            replaced.append((src, dst))
            return real_replace(src, dst)

        with _urlopen(b"done"), patch("os.replace", side_effect=track_replace):
            cache_path = Path(File(uri=URL).path)

        assert len(replaced) == 1
        src, dst = replaced[0]
        assert Path(dst) == cache_path
        assert src != dst
        assert cache_path.read_bytes() == b"done"

    def test_failed_url_download_removes_temp_file_and_clears_tmp_path(self, file_cache):
        seen_tmp: list[str | None] = []

        def explode(*args, **kwargs):
            raise OSError("network down")

        original_download = File._download_url

        def recording_download(self, retries: int = 1):
            try:
                return original_download(self, retries=retries)
            finally:
                seen_tmp.append(getattr(self, "_tmp_path", None))

        with patch("urllib.request.urlopen", side_effect=explode), patch.object(
            File, "_download_url", recording_download
        ):
            with pytest.raises(RuntimeError, match="Error downloading"):
                File(uri=URL)

        assert seen_tmp == [None]
        leftover = list(file_cache.rglob("*.tmp"))
        assert leftover == []


class TestFileDataUriTempIsolation:
    def test_data_uri_decode_uses_mkstemp_outside_cache_dir(self, file_cache):
        uri = "data:text/plain;base64,SGVsbG8="
        captured: dict = {}

        real_mkstemp = tempfile.mkstemp

        def record_mkstemp(*args, **kwargs):
            captured["kwargs"] = kwargs
            return real_mkstemp(*args, **kwargs)

        with patch("tempfile.mkstemp", side_effect=record_mkstemp):
            path = File(uri=uri).path

        cache_path = Path(path)
        assert captured["kwargs"]["dir"] == cache_path.parent.parent
        assert captured["kwargs"]["suffix"] == ".tmp"
        assert cache_path.read_bytes() == b"Hello"
