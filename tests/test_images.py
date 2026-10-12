import io

import pytest

PIL = pytest.importorskip("PIL")
from PIL import Image  # noqa: E402

from inferencesh.images import ImageLimits, fit_image  # noqa: E402


def _write(tmp_path, size, fmt="PNG", name="img.png", color=(0, 160, 0)):
    path = tmp_path / name
    Image.new("RGB", size, color).save(path, format=fmt)
    return str(path)


def _size(data):
    return Image.open(io.BytesIO(data)).size


def test_fitting_image_is_returned_byte_for_byte(tmp_path):
    path = _write(tmp_path, (800, 600))
    data, mime = fit_image(path, ImageLimits(max_long_edge=1568))
    assert data == open(path, "rb").read()
    assert mime == "image/png"


def test_never_upscales(tmp_path):
    path = _write(tmp_path, (100, 50))
    data, _ = fit_image(path, ImageLimits(max_long_edge=2576, max_pixels=3_750_000))
    assert _size(data) == (100, 50)


def test_downsizes_to_long_edge_keeping_aspect(tmp_path):
    path = _write(tmp_path, (3840, 2160))
    data, mime = fit_image(path, ImageLimits(max_long_edge=1568))
    assert _size(data) == (1568, 882)
    assert mime == "image/png"


def test_downsizes_to_pixel_budget(tmp_path):
    path = _write(tmp_path, (2000, 2000))
    data, _ = fit_image(path, ImageLimits(max_pixels=1_000_000))
    w, h = _size(data)
    assert w * h <= 1_000_000 and w == h


def test_unsupported_format_is_converted(tmp_path):
    path = _write(tmp_path, (64, 64), fmt="WEBP", name="img.webp")
    data, mime = fit_image(path, ImageLimits(mime_types=("image/png", "image/jpeg")))
    assert mime == "image/png"
    assert data.startswith(b"\x89PNG")


def test_over_byte_limit_goes_lossy(tmp_path):
    path = tmp_path / "noise.png"
    import os
    Image.frombytes("RGB", (512, 512), os.urandom(512 * 512 * 3)).save(path, format="PNG")
    limit = 100_000
    data, mime = fit_image(str(path), ImageLimits(max_bytes=limit))
    assert len(data) <= limit
    assert mime in ("image/jpeg", "image/webp")


def test_non_image_is_returned_unchanged(tmp_path):
    path = tmp_path / "x.png"
    path.write_bytes(b"not an image")
    data, _ = fit_image(str(path), ImageLimits(max_long_edge=10))
    assert data == b"not an image"
