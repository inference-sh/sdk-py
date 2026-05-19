"""Tests for utils.download and StorageDir."""

import hashlib
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.parse import urlparse

import pytest

from inferencesh.utils.download import download
from inferencesh.utils.storage import StorageDir


def test_storage_dir_values():
    assert StorageDir.DATA == "/app/data"
    assert StorageDir.TEMP == "/app/tmp"
    assert StorageDir.CACHE == "/app/cache"


def test_download_writes_file_and_returns_path(tmp_path):
    url = "https://cdn.example.com/assets/photo.png?token=abc"

    mock_file = MagicMock()
    mock_file.path = str(tmp_path / "source.bin")
    (tmp_path / "source.bin").write_bytes(b"image-bytes")

    with patch("inferencesh.utils.download.File", return_value=mock_file) as file_cls:
        result = download(url, tmp_path)

    file_cls.assert_called_once_with(url)
    assert mock_file._tmp_path is None
    assert Path(result).exists()
    assert Path(result).read_bytes() == b"image-bytes"

    parsed = urlparse(url)
    url_hash = hashlib.sha256(
        (parsed.netloc + parsed.path + "?" + parsed.query).encode()
    ).hexdigest()[:12]
    assert result.endswith(f"{url_hash}/photo.png")


def test_download_reuses_cached_file_for_non_temp_directory(tmp_path):
    url = "https://cdn.example.com/data/report.json"
    parsed = urlparse(url)
    url_hash = hashlib.sha256((parsed.netloc + parsed.path).encode()).hexdigest()[:12]
    cached = tmp_path / url_hash / "report.json"
    cached.parent.mkdir(parents=True)
    cached.write_text('{"cached": true}')

    with patch("inferencesh.utils.download.File") as file_cls:
        result = download(url, tmp_path)

    file_cls.assert_not_called()
    assert result == str(cached)


def test_download_raises_when_file_has_no_path(tmp_path):
    mock_file = MagicMock()
    mock_file.path = None

    with patch("inferencesh.utils.download.File", return_value=mock_file):
        with pytest.raises(RuntimeError, match="Failed to download"):
            download("https://cdn.example.com/missing.bin", tmp_path)
