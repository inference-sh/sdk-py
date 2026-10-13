"""fit_image without Pillow (inferencesh[images] optional extra).

The images extra pins Pillow in uv.lock; core installs must still send bytes
unchanged when Pillow is not installed, so provider limits are not applied
client-side.
"""

import builtins

import pytest

from inferencesh.images import ImageLimits, fit_image


def _block_pillow_import(monkeypatch):
    real_import = builtins.__import__

    def guarded(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "PIL" or (fromlist and "Image" in fromlist and name in ("PIL", "")):
            raise ImportError("Pillow not installed")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded)


def test_without_pillow_returns_original_bytes_even_when_limits_would_resize(tmp_path, monkeypatch):
    raw = b"\x89PNG\r\n\x1a\n" + b"payload"
    path = tmp_path / "wide.png"
    path.write_bytes(raw)
    _block_pillow_import(monkeypatch)

    data, mime = fit_image(str(path), ImageLimits(max_long_edge=1))

    assert data == raw
    assert mime == "image/png"


def test_without_pillow_sniffs_jpeg_magic_bytes(tmp_path, monkeypatch):
    raw = b"\xff\xd8\xff" + b"jpeg-bytes"
    path = tmp_path / "photo.jpg"
    path.write_bytes(raw)
    _block_pillow_import(monkeypatch)

    data, mime = fit_image(str(path), ImageLimits(max_bytes=1))

    assert data == raw
    assert mime == "image/jpeg"
