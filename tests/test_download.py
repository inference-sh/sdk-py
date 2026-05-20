"""Tests for utils.download caching and path layout."""

import hashlib
import urllib.parse
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from inferencesh.utils.download import download
from inferencesh.utils.storage import StorageDir


def _url_hash(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    components = parsed.netloc + parsed.path
    if parsed.query:
        components += "?" + parsed.query
    return hashlib.sha256(components.encode()).hexdigest()[:12]


def test_download_writes_file_and_returns_stable_path(tmp_path):
    url = "https://cdn.example.com/assets/photo.png"
    src = tmp_path / "source.bin"
    src.write_bytes(b"image-bytes")

    with patch("inferencesh.utils.download.File") as mock_file_cls:
        mock_file = MagicMock()
        mock_file.path = str(src)
        mock_file_cls.return_value = mock_file

        first = download(url, tmp_path)
        second = download(url, tmp_path)

    assert first == second
    assert mock_file_cls.call_count == 1
    expected = tmp_path / _url_hash(url) / "photo.png"
    assert Path(first) == expected
    assert expected.read_bytes() == b"image-bytes"
    assert mock_file._tmp_path is None


def test_download_query_string_changes_cache_directory(tmp_path):
    base = "https://cdn.example.com/assets/photo.png"
    url_with_query = f"{base}?v=2"

    src = tmp_path / "source.bin"
    src.write_bytes(b"v2")

    with patch("inferencesh.utils.download.File") as mock_file_cls:
        mock_file = MagicMock()
        mock_file.path = str(src)
        mock_file_cls.return_value = mock_file

        path_plain = download(base, tmp_path)
        path_query = download(url_with_query, tmp_path)

    assert path_plain != path_query
    assert mock_file_cls.call_count == 2


def test_download_raises_when_file_has_no_path(tmp_path):
    url = "https://cdn.example.com/missing.bin"

    with patch("inferencesh.utils.download.File") as mock_file_cls:
        mock_file = MagicMock()
        mock_file.path = None
        mock_file_cls.return_value = mock_file

        with pytest.raises(RuntimeError, match="Failed to download"):
            download(url, tmp_path)


def test_download_cache_hit_skips_file_when_not_temp(tmp_path):
    """Non-TEMP directories reuse an existing file without constructing File again."""
    url = "https://cdn.example.com/cached.bin"
    hash_dir = tmp_path / _url_hash(url)
    hash_dir.mkdir(parents=True)
    cached = hash_dir / "cached.bin"
    cached.write_bytes(b"cached")

    with patch("inferencesh.utils.download.File") as mock_file_cls:
        path = download(url, tmp_path)

    assert path == str(cached)
    mock_file_cls.assert_not_called()
    assert StorageDir.TEMP != tmp_path


def test_download_uses_default_filename_when_url_has_no_basename(tmp_path):
    """URLs ending with / get a stable 'download' filename in the hash directory."""
    url = "https://cdn.example.com/assets/"
    src = tmp_path / "source.bin"
    src.write_bytes(b"payload")

    with patch("inferencesh.utils.download.File") as mock_file_cls:
        mock_file = MagicMock()
        mock_file.path = str(src)
        mock_file_cls.return_value = mock_file

        path = download(url, tmp_path)

    expected = tmp_path / _url_hash(url) / "download"
    assert Path(path) == expected
    assert expected.read_bytes() == b"payload"


def test_download_temp_dir_redownloads_even_when_cached(tmp_path, monkeypatch):
    """TEMP storage must not short-circuit on cache hits (always refresh)."""
    import importlib

    url = "https://cdn.example.com/temp.bin"
    temp_root = tmp_path / "tmp"
    temp_root.mkdir()
    hash_dir = temp_root / _url_hash(url)
    hash_dir.mkdir(parents=True, exist_ok=True)
    stale = hash_dir / "temp.bin"
    stale.write_bytes(b"stale")

    src = tmp_path / "fresh.bin"
    src.write_bytes(b"fresh")

    class _StorageDir:
        TEMP = str(temp_root)

    download_mod = importlib.import_module("inferencesh.utils.download")
    monkeypatch.setattr(download_mod, "StorageDir", _StorageDir)

    with patch("inferencesh.utils.download.File") as mock_file_cls:
        mock_file = MagicMock()
        mock_file.path = str(src)
        mock_file_cls.return_value = mock_file

        path = download(url, str(temp_root))

    assert Path(path).read_bytes() == b"fresh"
    mock_file_cls.assert_called_once_with(url)


def test_storage_dir_path_creates_directory(tmp_path, monkeypatch):
    """StorageDir.path ensures the backing directory exists."""
    cache_root = tmp_path / "cache"

    def path_factory(value):
        assert value == StorageDir.CACHE.value
        return cache_root

    monkeypatch.setattr("inferencesh.utils.storage.Path", path_factory)

    result = StorageDir.CACHE.path

    assert result == cache_root
    assert cache_root.is_dir()
